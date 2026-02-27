from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException
from passlib.context import CryptContext
from sqlmodel import Session, select

from app.models.account_model import Account
from app.models.customer_model import Customer
from app.models.ledger_model import Entry
from app.models.transfer_model import Transfer
from app.schemas.transfer_schema import TransferCreateRequest

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_otp(raw_otp: str, otp_hash: str) -> bool:
    try:
        return pwd_context.verify(raw_otp, otp_hash)
    except Exception:
        return False


def create_transfer_service(
    session: Session,
    current_user: Customer,
    payload: TransferCreateRequest,
) -> dict:
    account = session.exec(
        select(Account).where(Account.customer_id == current_user.customer_id)
    ).first()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    if account.status != "ACTIVE":
        raise HTTPException(status_code=400, detail="Account is not active")

    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid amount")

    if account.balance < payload.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    if not verify_otp(payload.otp, account.otp_hash):
        raise HTTPException(status_code=400, detail="Invalid OTP")

    now = datetime.utcnow()

    transfer = Transfer(
        sender_account_id=account.account_id,
        receiver_account_id=None,
        sender_bank_name=account.bank_name,
        sender_name=current_user.full_name,
        sender_account_no=account.account_no,
        receiver_bank_name=payload.receiver_bank_name,
        receiver_name=payload.receiver_name,
        receiver_account_no=payload.receiver_account_no,
        amount=payload.amount,
        description=payload.description,
        reference_no=None,
        created_at=now,
        executed_at=now,
    )
    session.add(transfer)
    session.flush()

    balance_before = account.balance
    balance_after = balance_before - payload.amount

    entry = Entry(
        transfer_id=transfer.transfer_id,
        account_id=account.account_id,
        amount=Decimal("0") - payload.amount,
        balance_before=balance_before,
        balance_after=balance_after,
        note=payload.description or "Chuyển tiền",
        created_at=now,
    )
    session.add(entry)

    account.balance = balance_after
    session.add(account)

    session.commit()
    session.refresh(transfer)
    session.refresh(account)

    return {
        "transfer_id": transfer.transfer_id,
        "message": "Transfer created successfully",
        "new_balance": account.balance,
        "created_at": transfer.created_at,
    }