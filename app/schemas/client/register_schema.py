from datetime import date
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.enums import GenderType


class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    cccd_number: str = Field(..., min_length=9, max_length=20)
    date_of_birth: date
    gender: GenderType

    permanent_address: str = Field(..., min_length=2)
    current_address: str = Field(..., min_length=2)
    occupation: str = Field(..., min_length=1)

    email: Optional[EmailStr] = None
    phone: str = Field(..., min_length=10, max_length=15)
    password: str = Field(..., min_length=8, max_length=72)
    pin: str = Field(..., min_length=6, max_length=6)

    identity_issue_date: Optional[date] = None
    identity_expiry_date: Optional[date] = None
    identity_issue_place: Optional[str] = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        v = v.strip()
        if not v.isdigit():
            raise ValueError("Số điện thoại chỉ chứa chữ số")
        if not v.startswith("0") or len(v) != 10:
            raise ValueError("Số điện thoại phải gồm 10 chữ số và bắt đầu bằng 0")
        return v

    @field_validator("cccd_number")
    @classmethod
    def validate_cccd(cls, v: str) -> str:
        v = v.strip()
        if not v.isdigit():
            raise ValueError("Số CCCD chỉ chứa chữ số")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Mật khẩu cần ít nhất 8 ký tự")
        has_upper = any(c.isupper() for c in v)
        has_digit = any(c.isdigit() for c in v)
        if not has_upper or not has_digit:
            raise ValueError("Mật khẩu cần chứa ít nhất 1 chữ in hoa và 1 chữ số")
        return v

    @field_validator("pin")
    @classmethod
    def validate_pin(cls, v: str) -> str:
        v = v.strip()
        if not (v.isdigit() and len(v) == 6):
            raise ValueError("PIN giao dịch phải gồm đúng 6 chữ số")
        return v


class RegisteredAccount(BaseModel):
    account_id: str
    account_no: str
    bank_name: str
    currency: str
    balance: str
    status: str


class RegisteredCard(BaseModel):
    card_id: str
    card_no_masked: str
    status: str
    expiry_month: int
    expiry_year: int


class RegisterResponse(BaseModel):
    customer_id: str
    full_name: str
    phone: str
    email: Optional[EmailStr] = None
    access_token: str
    token_type: str = "bearer"
    account: RegisteredAccount
    card: RegisteredCard
