from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class OverviewOut(BaseModel):
    period: str
    total_income: Decimal
    total_expense: Decimal
    net: Decimal
    transaction_count: int
    income_change_percent: Optional[Decimal] = None
    expense_change_percent: Optional[Decimal] = None


class ExpenseByTypeItem(BaseModel):
    transfer_type: str
    label: str
    total: Decimal
    count: int


class ExpenseByTypeOut(BaseModel):
    period: str
    total_expense: Decimal
    items: list[ExpenseByTypeItem]


class DailyPoint(BaseModel):
    day: str
    income: Decimal
    expense: Decimal


class DailyOut(BaseModel):
    period: str
    points: list[DailyPoint]


class TopRecipientItem(BaseModel):
    name: str
    account_no: Optional[str] = None
    bank_code: Optional[str] = None
    customer_id: Optional[UUID] = None
    is_internal: bool
    total: Decimal
    count: int


class TopRecipientsOut(BaseModel):
    period: str
    items: list[TopRecipientItem]


class TrendPoint(BaseModel):
    period: str
    total_income: Decimal
    total_expense: Decimal


class TrendOut(BaseModel):
    months: int
    points: list[TrendPoint]
