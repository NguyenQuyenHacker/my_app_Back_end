from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID

class AccountOut(BaseModel):
    account_id: UUID
    customer_id: UUID
    account_no: str
    type: str
    status: str
    currency: str
    opened_at: datetime
    closed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
