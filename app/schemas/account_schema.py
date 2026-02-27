import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlmodel import SQLModel

from models.enums import AccountStatus


class AccountCreate(SQLModel):
    customer_id: uuid.UUID
    account_no: str
    bank_name: str = "TCB"
    status: AccountStatus = AccountStatus.ACTIVE
    currency: str
    balance: Decimal = Decimal("0.00")
    otp: str
    opened_at: datetime


class AccountRead(SQLModel):
    account_id: uuid.UUID
    customer_id: uuid.UUID
    account_no: str
    bank_name: str
    status: AccountStatus
    currency: str
    balance: Decimal
    opened_at: datetime
    closed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime