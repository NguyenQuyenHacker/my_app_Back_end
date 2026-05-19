import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlmodel import SQLModel, Field

from app.models.enums import LedgerSide


class LedgerEntry(SQLModel, table=True):
    __tablename__ = "ledger_entries"

    entry_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    transaction_id: uuid.UUID = Field(foreign_key="transactions.transaction_id", index=True)

    account_id: Optional[uuid.UUID] = Field(default=None, foreign_key="accounts.account_id", index=True)
    system_account_id: Optional[uuid.UUID] = Field(default=None, foreign_key="system_accounts.id", index=True)

    entry_type: LedgerSide
    amount: Decimal = Field(max_digits=18, decimal_places=2)
    balance_after: Optional[Decimal] = Field(default=None, max_digits=18, decimal_places=2)
    currency: str = Field(default="VND", max_length=3)
    description: Optional[str] = None
    created_at: datetime
