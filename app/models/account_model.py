import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlmodel import SQLModel, Field

from app.models.enums import AccountStatus


class Account(SQLModel, table=True):
    __tablename__ = "accounts"

    account_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    customer_id: uuid.UUID = Field(foreign_key="customers.customer_id", index=True)
    account_no: str = Field(unique=True, index=True)
    bank_name: str = Field(default="TCB")
    status: AccountStatus
    currency: str = Field(max_length=3)
    balance: Decimal = Field(default=Decimal("0.00"), max_digits=18, decimal_places=2)
    otp_hash: str
    opened_at: datetime
    closed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime