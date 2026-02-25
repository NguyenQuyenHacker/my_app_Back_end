from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from datetime import datetime

class NotificationOut(BaseModel):
    notification_id: UUID
    customer_id: UUID
    channel: str
    title: str
    body: str
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime] = None

    class Config:
        from_attributes = True
