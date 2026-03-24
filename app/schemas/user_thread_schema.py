import uuid
from datetime import datetime
from pydantic import BaseModel


class UserThreadRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    thread_id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime


class UserThreadCreate(BaseModel):
    thread_id: uuid.UUID
    title: str | None = None


class UserThreadUpdateTitle(BaseModel):
    title: str