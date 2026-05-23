import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator
from sqlmodel import SQLModel

from app.models.enums import AccountStatus, TransactionStatus, TransferType


class AccountCreate(SQLModel):
    customer_id: uuid.UUID
    account_no: str
    bank_name: str = "TCB"
    status: AccountStatus = AccountStatus.ACTIVE
    currency: str
    balance: Decimal = Decimal("0.00")
    otp: str
    opened_at: datetime


class AccountRead(SQLModel):
    account_id: uuid.UUID
    customer_id: uuid.UUID
    account_no: str
    bank_name: str
    status: AccountStatus
    currency: str
    balance: Decimal
    opened_at: datetime
    closed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


# ============================================================
# Schemas cho Agent tool: balance & transaction history
# ============================================================
class BalanceResponse(BaseModel):
    account_no: Optional[str] = None
    bank_name: Optional[str] = None
    currency: Optional[str] = None
    balance: Optional[Decimal] = None
    hold_amount: Optional[Decimal] = None
    available_balance: Optional[Decimal] = None
    status: Optional[AccountStatus] = None
    has_account: bool = True


class TransactionItem(BaseModel):
    transaction_code: str
    direction: Literal["IN", "OUT"]
    transfer_type: TransferType
    status: TransactionStatus
    counterparty_name: str
    counterparty_account: str
    counterparty_bank: Optional[str] = None
    amount: Decimal
    currency: str
    description: Optional[str] = None
    created_at: datetime


class TransactionFilterQuery(BaseModel):
    limit: int = Field(default=5, ge=1, le=20)
    direction: Literal["IN", "OUT", "ALL"] = "ALL"
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    min_amount: Optional[Decimal] = Field(default=None, ge=0)
    max_amount: Optional[Decimal] = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _check_ranges(self):
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("date_from must be <= date_to")
        if (
            self.min_amount is not None
            and self.max_amount is not None
            and self.min_amount > self.max_amount
        ):
            raise ValueError("min_amount must be <= max_amount")
        return self


class TransactionListResponse(BaseModel):
    filters: dict
    count: int
    transactions: list[TransactionItem]