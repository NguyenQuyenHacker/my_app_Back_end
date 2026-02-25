import uuid
from datetime import datetime

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Enum as SAEnum

from .enums import AccountType, AccountStatus

class Account(SQLModel, table=True):
    __tablename__ = "accounts"

    account_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(UUID(as_uuid=True), primary_key=True),
    )
    customer_id: uuid.UUID = Field(sa_column=Column(UUID(as_uuid=True), nullable=False))

    account_no: str = Field(sa_column=Column(Text, unique=True, nullable=False))
    type: AccountType = Field(
        default=AccountType.CHECKING,
        sa_column=Column(SAEnum(AccountType, name="account_type"), nullable=False),
    )
    status: AccountStatus = Field(
        default=AccountStatus.ACTIVE,
        sa_column=Column(SAEnum(AccountStatus, name="account_status"), nullable=False),
    )
    currency: str = Field(default="VND", max_length=3)

    opened_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    closed_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
