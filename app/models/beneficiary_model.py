import uuid
from datetime import datetime

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID

class Beneficiary(SQLModel, table=True):
    __tablename__ = "beneficiaries"

    beneficiary_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(UUID(as_uuid=True), primary_key=True),
    )
    customer_id: uuid.UUID = Field(sa_column=Column(UUID(as_uuid=True), nullable=False))
    nickname: str | None = Field(default=None, sa_column=Column(Text))
    bank_code: str | None = Field(default=None, sa_column=Column(Text))
    beneficiary_name: str = Field(sa_column=Column(Text, nullable=False))
    beneficiary_account_no: str = Field(sa_column=Column(Text, nullable=False))
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
