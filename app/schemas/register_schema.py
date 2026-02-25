from pydantic import BaseModel, EmailStr
from datetime import date
from typing import Optional

class RegisterRequest(BaseModel):
    full_name: str
    cccd_number: str
    date_of_birth: date
    gender: str  # MALE/FEMALE/OTHER

    permanent_address: str
    current_address: str
    occupation: str

    email: Optional[EmailStr] = None
    phone: str
    password: str
