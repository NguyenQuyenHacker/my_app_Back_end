import uuid
from datetime import datetime

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB

class AuditEvent(SQLModel, table=True):
    __tablename__ = "audit_events"

    event_id: int | None = Field(default=None, primary_key=True)
    actor_user_id: uuid.UUID | None = Field(default=None, sa_column=Column(UUID(as_uuid=True)))
    event_type: str = Field(sa_column=Column(Text, nullable=False))
    entity_type: str = Field(sa_column=Column(Text, nullable=False))
    entity_id: uuid.UUID | None = Field(default=None, sa_column=Column(UUID(as_uuid=True)))
    payload: dict | None = Field(default=None, sa_column=Column(JSONB))
    occurred_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    ip_address: str | None = Field(default=None, sa_column=Column(INET))
