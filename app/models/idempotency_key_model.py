import uuid
from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class IdempotencyKey(SQLModel, table=True):
    __tablename__ = "idempotency_keys"

    key: str = Field(primary_key=True, max_length=128)
    user_id: uuid.UUID = Field(index=True)
    response: Optional[str] = None
    status_code: int
    created_at: datetime
    expires_at: datetime
