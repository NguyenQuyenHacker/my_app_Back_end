import uuid
from datetime import date, datetime
from typing import Optional

from sqlmodel import SQLModel

from models.enums import GenderType


class CustomerCreate(SQLModel):
    full_name: str
    cccd_number: str
    date_of_birth: date
    gender: GenderType
    permanent_address: str
    current_address: str
    occupation: str
    email: Optional[str] = None
    phone: str


class CustomerRead(SQLModel):
    customer_id: uuid.UUID
    full_name: str
    cccd_number: str
    date_of_birth: date
    gender: GenderType
    permanent_address: str
    current_address: str
    occupation: str
    email: Optional[str] = None
    phone: str
    created_at: datetime
    updated_at: datetime