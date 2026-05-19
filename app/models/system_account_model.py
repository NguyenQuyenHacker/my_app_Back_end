import uuid
from datetime import datetime
from decimal import Decimal

from sqlmodel import SQLModel, Field


class SystemAccount(SQLModel, table=True):
    __tablename__ = "system_accounts"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    account_code: str = Field(unique=True, index=True, max_length=32)
    name: str
    balance: Decimal = Field(default=Decimal("0.00"), max_digits=18, decimal_places=2)

    created_at: datetime
    updated_at: datetime
