import uuid
from datetime import datetime, timezone

from sqlmodel import SQLModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class UserThread(SQLModel, table=True):
    __tablename__ = "user_threads"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(index=True, nullable=False)
    thread_id: uuid.UUID = Field(index=True, nullable=False)
    title: str = Field(default="Cuộc trò chuyện mới", nullable=False)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(default_factory=utc_now, nullable=False)