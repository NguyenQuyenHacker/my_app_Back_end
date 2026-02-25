import uuid
from datetime import datetime

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Text, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Enum as SAEnum

from .enums import NotificationChannel

class Notification(SQLModel, table=True):
    __tablename__ = "notifications"

    notification_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(UUID(as_uuid=True), primary_key=True),
    )
    customer_id: uuid.UUID = Field(sa_column=Column(UUID(as_uuid=True), nullable=False))
    channel: NotificationChannel = Field(
        default=NotificationChannel.IN_APP,
        sa_column=Column(SAEnum(NotificationChannel, name="notification_channel"), nullable=False),
    )
    title: str = Field(sa_column=Column(Text, nullable=False))
    body: str = Field(sa_column=Column(Text, nullable=False))
    is_read: bool = Field(default=False, sa_column=Column(Boolean, nullable=False, default=False))
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    read_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
