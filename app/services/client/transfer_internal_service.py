import uuid
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException
from sqlmodel import Session, select

from app.models.account_model import Account
from app.models.customer_model import Customer
from app.models.enums import AccountStatus, TransactionStatus, TransferType
from app.models.transaction_model import Transaction
from app.schemas.client.transfer_schema import (
    InternalTransferInitRequest,
    TransferConfirmRequest,
    TransferConfirmResponse,
    TransferInitResponse,
)
from app.services.client import (
    idempotency_service,
    ledger_service,
    otp_service,
    transfer_session_service,
)
from app.services.client.transfer_common import (
    check_limits,
    ensure_account_active,
    ensure_sufficient_balance,
    generate_transaction_code,
    get_source_account_for_customer,
    lock_accounts_ordered,
    utcnow,
)


def _find_dest_account(session: Session, account_no: str) -> Account:
    acc = session.exec(
        select(Account).where(Account.account_no == account_no)
    ).first()
    if not acc:
        raise HTTPException(status_code=404, detail="Destination account not found")
    if acc.status != AccountStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Destination account is not ACTIVE")
    return acc


def _dest_customer_name(session: Session, customer_id: uuid.UUID) -> str:
    cust = session.exec(
        select(Customer).where(Customer.customer_id == customer_id)
    ).first()
    if not cust:
        raise HTTPException(status_code=404, detail="Destination customer not found")
    return cust.full_name


def init_internal_transfer(
    session: Session,
    *,
    current_user: Customer,
    payload: InternalTransferInitRequest,
    idempotency_key: Optional[str],
) -> TransferInitResponse:
    if idempotency_key:
        cached = idempotency_service.get_existing(session, idempotency_key, current_user.customer_id)
        if cached:
            return TransferInitResponse(**cached)

    source = get_source_account_for_customer(session, current_user.customer_id)
    ensure_account_active(source, "Source")

    dest = _find_dest_account(session, payload.to_account_no)
    if dest.account_id == source.account_id:
        raise HTTPException(status_code=400, detail="Cannot transfer to the same account")

    ensure_sufficient_balance(source, payload.amount)
    check_limits(session, source, payload.amount)

    dest_name = _dest_customer_name(session, dest.customer_id)

    session_row = transfer_session_service.create_session(
        session,
        customer_id=current_user.customer_id,
        source_account_id=source.account_id,
        transfer_type=TransferType.INTERNAL,
        payload={
            "to_account_no": payload.to_account_no,
            "to_account_id": str(dest.account_id),
            "to_customer_id": str(dest.customer_id),
            "to_name": dest_name,
            "amount": str(payload.amount),
            "description": payload.description,
        },
    )

    response = TransferInitResponse(
        session_id=session_row.session_id,
        transfer_type=TransferType.INTERNAL,
        to_account_no=payload.to_account_no,
        to_bank_code=None,
        to_name=dest_name,
        amount=payload.amount,
        fee=Decimal("0.00"),
        description=payload.description,
        expires_at=session_row.expires_at,
    )

    if idempotency_key:
        idempotency_service.save(
            session,
            key=idempotency_key,
            user_id=current_user.customer_id,
            status_code=200,
            response_body=response.model_dump(mode="json"),
        )
    session.commit()
    return response


def confirm_internal_transfer(
    session: Session,
    *,
    current_user: Customer,
    payload: TransferConfirmRequest,
    idempotency_key: Optional[str],
) -> TransferConfirmResponse:
    if idempotency_key:
        cached = idempotency_service.get_existing(session, idempotency_key, current_user.customer_id)
        if cached:
            return TransferConfirmResponse(**cached)

    sess = transfer_session_service.load_active_session(
        session,
        session_id=payload.session_id,
        customer_id=current_user.customer_id,
        transfer_type=TransferType.INTERNAL,
    )
    if not sess:
        raise HTTPException(status_code=400, detail="Invalid or expired transfer session")

    body = sess.payload
    amount = Decimal(body["amount"])
    dest_account_id = uuid.UUID(body["to_account_id"])
    dest_customer_id = uuid.UUID(body["to_customer_id"]) if body.get("to_customer_id") else None

    accs = lock_accounts_ordered(session, [sess.source_account_id, dest_account_id])
    source = next(a for a in accs if a.account_id == sess.source_account_id)
    dest = next(a for a in accs if a.account_id == dest_account_id)

    ensure_account_active(source, "Source")
    ensure_account_active(dest, "Destination")

    if not otp_service.verify_otp(payload.otp, source.otp_hash):
        raise HTTPException(status_code=401, detail="Invalid OTP")

    ensure_sufficient_balance(source, amount)
    check_limits(session, source, amount)

    now = utcnow()
    txn = Transaction(
        transaction_code=generate_transaction_code(session),
        idempotency_key=idempotency_key,
        transfer_type=TransferType.INTERNAL,
        status=TransactionStatus.SUCCESS,
        from_account_id=source.account_id,
        from_customer_id=current_user.customer_id,
        to_account_id=dest.account_id,
        to_customer_id=dest_customer_id,
        to_bank_code=dest.bank_name,
        to_bank_account=dest.account_no,
        to_account_holder=body["to_name"],
        amount=amount,
        currency=source.currency or "VND",
        description=body.get("description"),
        created_at=now,
        updated_at=now,
        completed_at=now,
    )
    session.add(txn)
    session.flush()

    source.balance -= amount
    dest.balance += amount
    source.updated_at = now
    dest.updated_at = now

    ledger_service.post_double_entry(
        session,
        transaction_id=txn.transaction_id,
        amount=amount,
        debit={"account_id": source.account_id, "balance_after": source.balance},
        credit={"account_id": dest.account_id, "balance_after": dest.balance},
        description=body.get("description"),
        currency=source.currency or "VND",
    )

    transfer_session_service.consume(sess)

    response = TransferConfirmResponse(
        transaction_id=txn.transaction_id,
        transaction_code=txn.transaction_code,
        transfer_type=TransferType.INTERNAL,
        status=TransactionStatus.SUCCESS,
        amount=amount,
        new_balance=source.balance,
        external_ref_id=None,
        failure_reason=None,
        created_at=txn.created_at,
    )

    if idempotency_key:
        idempotency_service.save(
            session,
            key=idempotency_key,
            user_id=current_user.customer_id,
            status_code=200,
            response_body=response.model_dump(mode="json"),
        )

    session.commit()
    return response
