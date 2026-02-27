# src
import uuid
from datetime import datetime

from sqlmodel import SQLModel, Field

from app.models.enums import CardStatus


class Card(SQLModel, table=True):
    __tablename__ = "cards"

    card_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    account_id: uuid.UUID = Field(foreign_key="accounts.account_id", unique=True, index=True)
    card_no: str = Field(unique=True, index=True)
    status: CardStatus
    issued_at: datetime
    expiry_month: int
    expiry_year: int
    created_at: datetime
    updated_at: datetime
