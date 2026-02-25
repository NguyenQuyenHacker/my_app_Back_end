import uuid
from datetime import datetime

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Enum as SAEnum

from .enums import CardType, CardStatus

class Card(SQLModel, table=True):
    __tablename__ = "cards"

    card_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(UUID(as_uuid=True), primary_key=True),
    )
    account_id: uuid.UUID = Field(sa_column=Column(UUID(as_uuid=True), nullable=False))

    card_type: CardType = Field(
        default=CardType.DEBIT,
        sa_column=Column(SAEnum(CardType, name="card_type"), nullable=False),
    )
    status: CardStatus = Field(
        default=CardStatus.ACTIVE,
        sa_column=Column(SAEnum(CardStatus, name="card_status"), nullable=False),
    )

    card_last4: str = Field(sa_column=Column(String(4), nullable=False))  # '0000'..'9999'
    issued_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    expiry_month: int = Field(sa_column=Column(Integer, nullable=False))
    expiry_year: int = Field(sa_column=Column(Integer, nullable=False))
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
