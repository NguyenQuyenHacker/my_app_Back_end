import uuid
from datetime import datetime

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Text, DateTime, Numeric
from sqlalchemy.dialects.postgresql import UUID

class LedgerEntry(SQLModel, table=True):
    __tablename__ = "ledger_entries"

    entry_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(UUID(as_uuid=True), primary_key=True),
    )
    reference_code: str = Field(sa_column=Column(Text, unique=True, nullable=False))
    description: str | None = Field(default=None, sa_column=Column(Text))
    occurred_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))

class LedgerPosting(SQLModel, table=True):
    __tablename__ = "ledger_postings"

    posting_id: int | None = Field(default=None, primary_key=True)
    entry_id: uuid.UUID = Field(sa_column=Column(UUID(as_uuid=True), nullable=False))
    account_id: uuid.UUID = Field(sa_column=Column(UUID(as_uuid=True), nullable=False))
    direction: str = Field(max_length=1)  # 'D'/'C'
    amount: float = Field(sa_column=Column(Numeric(18, 2), nullable=False))
    currency: str = Field(default="VND", max_length=3)
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
