import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlmodel import SQLModel, Field

from app.models.enums import TransactionStatus, TransferType


class Transaction(SQLModel, table=True):
    __tablename__ = "transactions"

    transaction_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    transaction_code: str = Field(unique=True, index=True, max_length=32)
    idempotency_key: Optional[str] = Field(default=None, index=True, max_length=128)

    transfer_type: TransferType
    status: TransactionStatus = Field(default=TransactionStatus.PENDING, index=True)

    from_account_id: Optional[uuid.UUID] = Field(default=None, foreign_key="accounts.account_id", index=True)
    from_customer_id: Optional[uuid.UUID] = Field(default=None, index=True)

    to_account_id: Optional[uuid.UUID] = Field(default=None, foreign_key="accounts.account_id", index=True)
    to_customer_id: Optional[uuid.UUID] = Field(default=None, index=True)

    to_bank_code: Optional[str] = Field(default=None, max_length=16)
    to_bank_account: str = Field(max_length=32)
    to_account_holder: str

    amount: Decimal = Field(max_digits=18, decimal_places=2)
    currency: str = Field(default="VND", max_length=3)
    description: Optional[str] = None

    failure_reason: Optional[str] = None
    external_ref_id: Optional[str] = Field(default=None, index=True)

    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
