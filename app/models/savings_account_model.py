import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlmodel import SQLModel, Field

from app.models.enums import SavingsAccountStatus


class SavingsAccount(SQLModel, table=True):
    __tablename__ = "savings_accounts"

    savings_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    savings_code: str = Field(unique=True, index=True, max_length=32)
    customer_id: uuid.UUID = Field(foreign_key="customers.customer_id", index=True)
    account_id: uuid.UUID = Field(foreign_key="accounts.account_id", index=True)
    product_id: uuid.UUID = Field(foreign_key="savings_products.product_id", index=True)

    principal_amount: Decimal = Field(max_digits=18, decimal_places=2)
    interest_rate: Decimal = Field(max_digits=6, decimal_places=4)
    early_withdrawal_rate: Decimal = Field(max_digits=6, decimal_places=4)
    term_months: int

    start_date: datetime
    maturity_date: datetime
    status: SavingsAccountStatus = Field(default=SavingsAccountStatus.ACTIVE, index=True)

    interest_earned: Decimal = Field(default=Decimal("0.00"), max_digits=18, decimal_places=2)
    final_amount: Decimal = Field(default=Decimal("0.00"), max_digits=18, decimal_places=2)
    closed_at: Optional[datetime] = None

    created_at: datetime
    updated_at: datetime
