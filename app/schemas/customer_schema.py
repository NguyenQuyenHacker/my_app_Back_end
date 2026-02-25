from pydantic import BaseModel, EmailStr
from datetime import date, datetime
from typing import Optional
from uuid import UUID

class CustomerOut(BaseModel):
    customer_id: UUID
    full_name: str
    cccd_number: str
    date_of_birth: date
    gender: str
    permanent_address: str
    current_address: str
    occupation: str
    email: Optional[EmailStr] = None
    phone: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
