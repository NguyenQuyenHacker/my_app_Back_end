from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import SavingsAccountStatus


class SavingsProductOut(BaseModel):
    product_id: UUID
    code: str
    name: str
    term_months: int
    interest_rate: Decimal
    early_withdrawal_rate: Decimal
    min_amount: Decimal
    is_active: bool


class SavingsPreviewRequest(BaseModel):
    product_id: UUID
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)


class SavingsPreviewResponse(BaseModel):
    product_id: UUID
    product_name: str
    term_months: int
    interest_rate: Decimal
    principal: Decimal
    interest_earned: Decimal
    final_amount: Decimal
    start_date: datetime
    maturity_date: datetime


class SavingsInitRequest(BaseModel):
    product_id: UUID
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)


class SavingsInitResponse(BaseModel):
    session_id: UUID
    product_id: UUID
    product_name: str
    term_months: int
    interest_rate: Decimal
    principal: Decimal
    expected_interest: Decimal
    expected_final_amount: Decimal
    expected_maturity_date: datetime
    expires_at: datetime


class SavingsConfirmRequest(BaseModel):
    session_id: UUID
    otp: str = Field(min_length=4, max_length=12)


class SavingsAccountOut(BaseModel):
    savings_id: UUID
    savings_code: str
    product_id: UUID
    product_name: Optional[str] = None
    product_code: Optional[str] = None
    principal_amount: Decimal
    interest_rate: Decimal
    term_months: int
    start_date: datetime
    maturity_date: datetime
    status: SavingsAccountStatus
    interest_earned: Decimal
    final_amount: Decimal
    closed_at: Optional[datetime] = None


class SavingsConfirmResponse(BaseModel):
    transaction_id: UUID
    transaction_code: str
    savings: SavingsAccountOut
    new_balance: Decimal
    created_at: datetime


class SavingsDetailOut(SavingsAccountOut):
    projected_interest_at_maturity: Decimal
    projected_final_amount_at_maturity: Decimal
    days_held: int


class EarlyWithdrawInitResponse(BaseModel):
    session_id: UUID
    savings_id: UUID
    principal: Decimal
    days_held: int
    estimated_interest: Decimal
    estimated_final_amount: Decimal
    expires_at: datetime


class EarlyWithdrawConfirmResponse(BaseModel):
    transaction_id: UUID
    transaction_code: str
    savings: SavingsAccountOut
    new_balance: Decimal
    created_at: datetime
