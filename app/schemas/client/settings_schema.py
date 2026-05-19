import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field


ThemeLiteral = Literal["light", "dark", "system"]
LanguageLiteral = Literal["vi", "en"]


class PreferencesRead(BaseModel):
    user_id: uuid.UUID
    theme: ThemeLiteral
    language: LanguageLiteral
    updated_at: datetime


class PreferencesUpdate(BaseModel):
    theme: Optional[ThemeLiteral] = None
    language: Optional[LanguageLiteral] = None


class ProfileUpdateRequest(BaseModel):
    password: str = Field(..., min_length=1)
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    current_address: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)


class ChangePinRequest(BaseModel):
    account_id: uuid.UUID
    current_pin: str = Field(..., min_length=4, max_length=12)
    new_pin: str = Field(..., min_length=4, max_length=12)


class LastLoginResponse(BaseModel):
    last_login_at: Optional[datetime] = None


class MessageResponse(BaseModel):
    message: str
