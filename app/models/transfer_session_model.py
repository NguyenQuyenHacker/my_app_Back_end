import uuid
from datetime import datetime

from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB

from app.models.enums import TransferType


class TransferSession(SQLModel, table=True):
    __tablename__ = "transfer_sessions"

    session_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    customer_id: uuid.UUID = Field(index=True)
    source_account_id: uuid.UUID
    transfer_type: TransferType
    payload: dict = Field(sa_column=Column(JSONB, nullable=False))
    used: bool = Field(default=False)
    created_at: datetime
    expires_at: datetime
