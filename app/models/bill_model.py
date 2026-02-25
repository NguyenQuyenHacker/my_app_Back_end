import uuid
from datetime import datetime, date

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Text, Date, DateTime, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Enum as SAEnum

from .enums import BillStatus, TransferStatus

class Biller(SQLModel, table=True):
    __tablename__ = "billers"

    biller_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(UUID(as_uuid=True), primary_key=True),
    )
    biller_code: str = Field(sa_column=Column(Text, unique=True, nullable=False))
    biller_name: str = Field(sa_column=Column(Text, nullable=False))

class Bill(SQLModel, table=True):
    __tablename__ = "bills"

    bill_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(UUID(as_uuid=True), primary_key=True),
    )
    customer_id: uuid.UUID = Field(sa_column=Column(UUID(as_uuid=True), nullable=False))
    biller_id: uuid.UUID = Field(sa_column=Column(UUID(as_uuid=True), nullable=False))
    bill_reference: str = Field(sa_column=Column(Text, nullable=False))
    amount: float = Field(sa_column=Column(Numeric(18, 2), nullable=False))
    currency: str = Field(default="VND", max_length=3)
    due_date: date | None = Field(default=None, sa_column=Column(Date))
    status: BillStatus = Field(
        default=BillStatus.DUE,
        sa_column=Column(SAEnum(BillStatus, name="bill_status"), nullable=False),
    )
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))

class BillPayment(SQLModel, table=True):
    __tablename__ = "bill_payments"

    bill_payment_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(UUID(as_uuid=True), primary_key=True),
    )
    bill_id: uuid.UUID = Field(sa_column=Column(UUID(as_uuid=True), nullable=False))
    from_account_id: uuid.UUID = Field(sa_column=Column(UUID(as_uuid=True), nullable=False))
    amount: float = Field(sa_column=Column(Numeric(18, 2), nullable=False))
    fee_amount: float = Field(default=0, sa_column=Column(Numeric(18, 2), nullable=False, default=0))
    status: TransferStatus = Field(
        default=TransferStatus.SUBMITTED,
        sa_column=Column(SAEnum(TransferStatus, name="transfer_status"), nullable=False),
    )
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    completed_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    ledger_entry_id: uuid.UUID | None = Field(default=None, sa_column=Column(UUID(as_uuid=True), unique=True))
