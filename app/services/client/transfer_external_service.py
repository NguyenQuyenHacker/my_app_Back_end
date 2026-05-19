from decimal import Decimal
from typing import Optional

from fastapi import HTTPException
from sqlmodel import Session, select

from app.models.account_model import Account
from app.models.customer_model import Customer
from app.models.enums import (
    ExternalBankAccountStatus,
    SystemAccountCode,
    TransactionStatus,
    TransferType,
)
from app.models.external_bank_account_model import ExternalBankAccount
from app.models.system_account_model import SystemAccount
from app.models.transaction_model import Transaction
from app.schemas.client.transfer_schema import (
    ExternalTransferInitRequest,
    TransferConfirmRequest,
    TransferConfirmResponse,
    TransferInitResponse,
)
from app.services.client import (
    idempotency_service,
    ledger_service,
    napas_mock,
    otp_service,
    transfer_session_service,
)
from app.services.client.transfer_common import (
    check_limits,
    ensure_account_active,
    ensure_sufficient_balance,
    generate_transaction_code,
    get_source_account_for_customer,
    lock_account_by_id,
    utcnow,
)


def _find_external_account(session: Session, bank_code: str, account_number: str) -> ExternalBankAccount:
    acc = session.exec(
        select(ExternalBankAccount).where(
            ExternalBankAccount.bank_code == bank_code,
            ExternalBankAccount.account_number == account_number,
        )
    ).first()
    if not acc:
        raise HTTPException(status_code=404, detail="External account not found")
    if acc.status != ExternalBankAccountStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="External account is not ACTIVE")
    return acc


def _lock_external_account(session: Session, bank_code: str, account_number: str) -> Optional[ExternalBankAccount]:
    return session.exec(
        select(ExternalBankAccount).where(
            ExternalBankAccount.bank_code == bank_code,
            ExternalBankAccount.account_number == account_number,
        ).with_for_update()
    ).first()


def _get_system_account(session: Session, code: SystemAccountCode) -> SystemAccount:
    acc = session.exec(
        select(SystemAccount).where(SystemAccount.account_code == code.value).with_for_update()
    ).first()
    if not acc:
        raise HTTPException(status_code=500, detail=f"System account {code.value} missing")
    return acc


def init_external_transfer(
    session: Session,
    *,
    current_user: Customer,
    payload: ExternalTransferInitRequest,
    idempotency_key: Optional[str],
) -> TransferInitResponse:
    if idempotency_key:
        cached = idempotency_service.get_existing(session, idempotency_key, current_user.customer_id)
        if cached:
            return TransferInitResponse(**cached)

    source = get_source_account_for_customer(session, current_user.customer_id)
    ensure_account_active(source, "Source")

    ext = _find_external_account(session, payload.to_bank_code, payload.to_account_number)

    ensure_sufficient_balance(source, payload.amount)
    check_limits(session, source, payload.amount)

    sess = transfer_session_service.create_session(
        session,
        customer_id=current_user.customer_id,
        source_account_id=source.account_id,
        transfer_type=TransferType.EXTERNAL,
        payload={
            "to_bank_code": payload.to_bank_code,
            "to_account_number": payload.to_account_number,
            "to_external_id": str(ext.id),
            "to_name": ext.account_holder_name,
            "amount": str(payload.amount),
            "description": payload.description,
        },
    )

    response = TransferInitResponse(
        session_id=sess.session_id,
        transfer_type=TransferType.EXTERNAL,
        to_account_no=payload.to_account_number,
        to_bank_code=payload.to_bank_code,
        to_name=ext.account_holder_name,
        amount=payload.amount,
        fee=Decimal("0.00"),
        description=payload.description,
        expires_at=sess.expires_at,
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


def _hold_funds_and_create_txn(
    session: Session,
    *,
    current_user: Customer,
    sess,
    idempotency_key: Optional[str],
    otp: str,
) -> Transaction:
    body = sess.payload
    amount = Decimal(body["amount"])

    source = lock_account_by_id(session, sess.source_account_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source account not found")
    ensure_account_active(source, "Source")

    if not otp_service.verify_otp(otp, source.otp_hash):
        raise HTTPException(status_code=401, detail="Invalid OTP")

    ensure_sufficient_balance(source, amount)
    check_limits(session, source, amount)

    suspense = _get_system_account(session, SystemAccountCode.SUSPENSE)

    now = utcnow()
    txn = Transaction(
        transaction_code=generate_transaction_code(session),
        idempotency_key=idempotency_key,
        transfer_type=TransferType.EXTERNAL,
        status=TransactionStatus.PENDING,
        from_account_id=source.account_id,
        from_customer_id=current_user.customer_id,
        to_account_id=None,
        to_customer_id=None,
        to_bank_code=body["to_bank_code"],
        to_bank_account=body["to_account_number"],
        to_account_holder=body["to_name"],
        amount=amount,
        currency=source.currency or "VND",
        description=body.get("description"),
        created_at=now,
        updated_at=now,
    )
    session.add(txn)
    session.flush()

    source.balance -= amount
    source.hold_amount += amount
    source.updated_at = now

    suspense.balance += amount

    ledger_service.post_double_entry(
        session,
        transaction_id=txn.transaction_id,
        amount=amount,
        debit={"account_id": source.account_id, "balance_after": source.balance},
        credit={"system_account_id": suspense.id, "balance_after": suspense.balance},
        description=f"HOLD external transfer to {body['to_account_number']}",
        currency=source.currency or "VND",
    )

    transfer_session_service.consume(sess)
    session.commit()
    session.refresh(txn)
    return txn


def _settle_success(session: Session, txn: Transaction, ext_ref_id: str) -> Transaction:
    source = lock_account_by_id(session, txn.from_account_id)
    suspense = _get_system_account(session, SystemAccountCode.SUSPENSE)
    clearing = _get_system_account(session, SystemAccountCode.CLEARING)

    ext_acc = _lock_external_account(session, txn.to_bank_code, txn.to_bank_account) if txn.to_bank_code else None

    now = utcnow()
    source.hold_amount -= txn.amount
    source.updated_at = now

    suspense.balance -= txn.amount
    clearing.balance += txn.amount

    if ext_acc:
        ext_acc.balance += txn.amount
        ext_acc.updated_at = now

    ledger_service.post_double_entry(
        session,
        transaction_id=txn.transaction_id,
        amount=txn.amount,
        debit={"system_account_id": suspense.id, "balance_after": suspense.balance},
        credit={"system_account_id": clearing.id, "balance_after": clearing.balance},
        description=f"SETTLE success ref={ext_ref_id}",
        currency=txn.currency or "VND",
    )

    txn.status = TransactionStatus.SUCCESS
    txn.external_ref_id = ext_ref_id
    txn.updated_at = now
    txn.completed_at = now
    session.add(txn)
    return txn


def _settle_failure(session: Session, txn: Transaction, ext_ref_id: str, reason: str) -> Transaction:
    source = lock_account_by_id(session, txn.from_account_id)
    suspense = _get_system_account(session, SystemAccountCode.SUSPENSE)

    now = utcnow()
    source.hold_amount -= txn.amount
    source.balance += txn.amount
    source.updated_at = now

    suspense.balance -= txn.amount

    ledger_service.post_double_entry(
        session,
        transaction_id=txn.transaction_id,
        amount=txn.amount,
        debit={"system_account_id": suspense.id, "balance_after": suspense.balance},
        credit={"account_id": source.account_id, "balance_after": source.balance},
        description=f"REVERSAL failed ref={ext_ref_id} reason={reason}",
        currency=txn.currency or "VND",
    )

    txn.status = TransactionStatus.FAILED
    txn.external_ref_id = ext_ref_id
    txn.failure_reason = reason
    txn.updated_at = now
    txn.completed_at = now
    session.add(txn)
    return txn


def confirm_external_transfer(
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
        transfer_type=TransferType.EXTERNAL,
    )
    if not sess:
        raise HTTPException(status_code=400, detail="Invalid or expired transfer session")

    txn = _hold_funds_and_create_txn(
        session,
        current_user=current_user,
        sess=sess,
        idempotency_key=idempotency_key,
        otp=payload.otp,
    )

    txn.status = TransactionStatus.PROCESSING
    txn.updated_at = utcnow()
    session.add(txn)
    session.commit()
    session.refresh(txn)

    napas_result = napas_mock.send_to_napas(
        bank_code=txn.to_bank_code,
        account_number=txn.to_bank_account,
        amount=txn.amount,
        description=txn.description,
    )

    final_status = napas_result["status"]
    ref_id = napas_result["ref_id"]
    reason = napas_result.get("reason")

    if final_status == "SUCCESS":
        txn = _settle_success(session, txn, ref_id)
    elif final_status == "FAILED":
        txn = _settle_failure(session, txn, ref_id, reason or "UNKNOWN")
    else:
        txn.external_ref_id = ref_id
        txn.updated_at = utcnow()
        session.add(txn)

    src = session.exec(select(Account).where(Account.account_id == txn.from_account_id)).first()
    new_balance = src.balance if src else Decimal("0")

    response = TransferConfirmResponse(
        transaction_id=txn.transaction_id,
        transaction_code=txn.transaction_code,
        transfer_type=TransferType.EXTERNAL,
        status=txn.status,
        amount=txn.amount,
        new_balance=new_balance,
        external_ref_id=txn.external_ref_id,
        failure_reason=txn.failure_reason,
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
