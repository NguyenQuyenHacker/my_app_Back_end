import uuid
from datetime import datetime

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Text, Boolean, DateTime, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Enum as SAEnum

from .enums import TransferType, TransferStatus

class Transfer(SQLModel, table=True):
    __tablename__ = "transfers"

    transfer_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(UUID(as_uuid=True), primary_key=True),
    )
    customer_id: uuid.UUID = Field(sa_column=Column(UUID(as_uuid=True), nullable=False))
    from_account_id: uuid.UUID = Field(sa_column=Column(UUID(as_uuid=True), nullable=False))

    to_account_no: str = Field(sa_column=Column(Text, nullable=False))
    to_bank_code: str | None = Field(default=None, sa_column=Column(Text))
    to_name: str | None = Field(default=None, sa_column=Column(Text))

    type: TransferType = Field(sa_column=Column(SAEnum(TransferType, name="transfer_type"), nullable=False))
    status: TransferStatus = Field(
        default=TransferStatus.DRAFT,
        sa_column=Column(SAEnum(TransferStatus, name="transfer_status"), nullable=False),
    )

    amount: float = Field(sa_column=Column(Numeric(18, 2), nullable=False))
    currency: str = Field(default="VND", max_length=3)
    fee_amount: float = Field(default=0, sa_column=Column(Numeric(18, 2), nullable=False, default=0))

    note: str | None = Field(default=None, sa_column=Column(Text))
    idempotency_key: str | None = Field(default=None, sa_column=Column(Text, unique=True))
    otp_required: bool = Field(default=True, sa_column=Column(Boolean, nullable=False, default=True))

    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    updated_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    submitted_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    completed_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    failure_reason: str | None = Field(default=None, sa_column=Column(Text))

    ledger_entry_id: uuid.UUID | None = Field(default=None, sa_column=Column(UUID(as_uuid=True), unique=True))

class Otp(SQLModel, table=True):
    __tablename__ = "otps"

    otp_id: int | None = Field(default=None, primary_key=True)
    user_id: uuid.UUID = Field(sa_column=Column(UUID(as_uuid=True), nullable=False))
    purpose: str = Field(sa_column=Column(Text, nullable=False))
    code_hash: str = Field(sa_column=Column(Text, nullable=False))
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    expires_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    verified_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    attempts: int = Field(default=0)
