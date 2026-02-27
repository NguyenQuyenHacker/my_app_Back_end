# src/app/models/ledger_model.py
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlmodel import SQLModel, Field


class Entry(SQLModel, table=True):
    __tablename__ = "entries"

    entry_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    transfer_id: uuid.UUID = Field(foreign_key="transfers.transfer_id", index=True)
    account_id: uuid.UUID = Field(foreign_key="accounts.account_id", index=True)

    amount: Decimal = Field(max_digits=18, decimal_places=2)
    balance_before: Decimal = Field(max_digits=18, decimal_places=2)
    balance_after: Decimal = Field(max_digits=18, decimal_places=2)

    note: Optional[str] = None
    created_at: datetime