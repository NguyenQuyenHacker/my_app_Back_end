import uuid
from datetime import datetime
from decimal import Decimal

from sqlmodel import SQLModel, Field, UniqueConstraint

from app.models.enums import ExternalBankAccountStatus


class ExternalBankAccount(SQLModel, table=True):
    __tablename__ = "external_bank_accounts"
    __table_args__ = (UniqueConstraint("bank_code", "account_number", name="uq_ext_bank_account"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    bank_code: str = Field(index=True, max_length=16)
    account_number: str = Field(index=True, max_length=32)
    account_holder_name: str
    balance: Decimal = Field(default=Decimal("0.00"), max_digits=18, decimal_places=2)
    status: ExternalBankAccountStatus = Field(default=ExternalBankAccountStatus.ACTIVE)

    created_at: datetime
    updated_at: datetime
