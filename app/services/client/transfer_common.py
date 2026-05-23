import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import func
from sqlmodel import Session, select

from app.models.account_model import Account
from app.models.enums import AccountStatus, TransactionStatus, TransferType
from app.models.transaction_model import Transaction


_TRANSFER_LIMIT_TYPES = [TransferType.INTERNAL, TransferType.EXTERNAL]


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def lock_account_by_id(session: Session, account_id: uuid.UUID) -> Optional[Account]:
    return session.exec(
        select(Account).where(Account.account_id == account_id).with_for_update()
    ).first()


def lock_accounts_ordered(session: Session, account_ids: list[uuid.UUID]) -> list[Account]:
    ordered = sorted(set(account_ids), key=lambda x: str(x))
    rows = []
    for aid in ordered:
        acc = lock_account_by_id(session, aid)
        if acc is None:
            raise HTTPException(status_code=404, detail=f"Account {aid} not found")
        rows.append(acc)
    return rows


def ensure_account_active(account: Account, label: str) -> None:
    if account.status != AccountStatus.ACTIVE:
        raise HTTPException(status_code=400, detail=f"{label} account is not ACTIVE")


def ensure_sufficient_balance(account: Account, amount: Decimal) -> None:
    if account.balance < amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")


def _sum_today(session: Session, account_id: uuid.UUID) -> Decimal:
    stmt = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
        Transaction.from_account_id == account_id,
        Transaction.transfer_type.in_(_TRANSFER_LIMIT_TYPES),
        Transaction.status.in_([TransactionStatus.PENDING, TransactionStatus.PROCESSING, TransactionStatus.SUCCESS]),
        func.date(Transaction.created_at) == func.current_date(),
    )
    val = session.exec(stmt).one()
    return Decimal(val) if val is not None else Decimal("0")


def _sum_this_month(session: Session, account_id: uuid.UUID) -> Decimal:
    stmt = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
        Transaction.from_account_id == account_id,
        Transaction.transfer_type.in_(_TRANSFER_LIMIT_TYPES),
        Transaction.status.in_([TransactionStatus.PENDING, TransactionStatus.PROCESSING, TransactionStatus.SUCCESS]),
        func.date_trunc("month", Transaction.created_at) == func.date_trunc("month", func.current_timestamp()),
    )
    val = session.exec(stmt).one()
    return Decimal(val) if val is not None else Decimal("0")


def check_limits(session: Session, account: Account, amount: Decimal) -> None:
    used_today = _sum_today(session, account.account_id)
    if used_today + amount > account.daily_limit:
        raise HTTPException(status_code=400, detail="Daily transfer limit exceeded")
    used_month = _sum_this_month(session, account.account_id)
    if used_month + amount > account.monthly_limit:
        raise HTTPException(status_code=400, detail="Monthly transfer limit exceeded")


def generate_transaction_code(session: Session) -> str:
    today_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    prefix = f"TXN{today_str}"
    count_stmt = select(func.count()).select_from(Transaction).where(
        Transaction.transaction_code.like(f"{prefix}%")
    )
    count = session.exec(count_stmt).one()
    seq = (count or 0) + 1
    return f"{prefix}{seq:06d}"


def get_source_account_for_customer(session: Session, customer_id: uuid.UUID) -> Account:
    acc = session.exec(
        select(Account).where(Account.customer_id == customer_id)
    ).first()
    if not acc:
        raise HTTPException(status_code=404, detail="Source account not found")
    return acc
