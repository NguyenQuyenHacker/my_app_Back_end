import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlmodel import Session

from app.models.enums import LedgerSide
from app.models.ledger_entry_model import LedgerEntry


def _now() -> datetime:
    return datetime.now(timezone.utc)


def post_entry(
    session: Session,
    *,
    transaction_id: uuid.UUID,
    entry_type: LedgerSide,
    amount: Decimal,
    account_id: Optional[uuid.UUID] = None,
    system_account_id: Optional[uuid.UUID] = None,
    balance_after: Optional[Decimal] = None,
    currency: str = "VND",
    description: Optional[str] = None,
) -> LedgerEntry:
    targets = sum(x is not None for x in (account_id, system_account_id))
    if targets != 1:
        raise ValueError("ledger entry must reference exactly one account target")
    if amount <= 0:
        raise ValueError("ledger amount must be positive")

    entry = LedgerEntry(
        transaction_id=transaction_id,
        account_id=account_id,
        system_account_id=system_account_id,
        entry_type=entry_type,
        amount=amount,
        balance_after=balance_after,
        currency=currency,
        description=description,
        created_at=_now(),
    )
    session.add(entry)
    return entry


def post_double_entry(
    session: Session,
    *,
    transaction_id: uuid.UUID,
    amount: Decimal,
    debit: dict,
    credit: dict,
    description: Optional[str] = None,
    currency: str = "VND",
) -> tuple[LedgerEntry, LedgerEntry]:
    deb = post_entry(
        session,
        transaction_id=transaction_id,
        entry_type=LedgerSide.DEBIT,
        amount=amount,
        description=description,
        currency=currency,
        **debit,
    )
    cred = post_entry(
        session,
        transaction_id=transaction_id,
        entry_type=LedgerSide.CREDIT,
        amount=amount,
        description=description,
        currency=currency,
        **credit,
    )
    return deb, cred
