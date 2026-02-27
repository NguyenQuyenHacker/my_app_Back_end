import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlmodel import SQLModel, Field


class Transfer(SQLModel, table=True):
    __tablename__ = "transfers"

    transfer_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    sender_account_id: Optional[uuid.UUID] = Field(default=None, foreign_key="accounts.account_id", index=True)
    receiver_account_id: Optional[uuid.UUID] = Field(default=None, foreign_key="accounts.account_id", index=True)

    sender_bank_name: Optional[str] = None
    sender_name: Optional[str] = None
    sender_account_no: Optional[str] = Field(default=None, index=True)

    receiver_bank_name: str
    receiver_name: str
    receiver_account_no: str = Field(index=True)

    amount: Decimal = Field(max_digits=18, decimal_places=2)
    description: Optional[str] = None
    reference_no: Optional[str] = Field(default=None, index=True)

    created_at: datetime
    executed_at: datetime