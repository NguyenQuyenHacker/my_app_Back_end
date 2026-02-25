from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

class CardOut(BaseModel):
    card_id: UUID
    account_id: UUID
    card_type: str
    status: str
    card_last4: str
    issued_at: datetime
    expiry_month: int
    expiry_year: int
    created_at: datetime

    class Config:
        from_attributes = True
