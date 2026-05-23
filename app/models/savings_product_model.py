import uuid
from datetime import datetime
from decimal import Decimal

from sqlmodel import SQLModel, Field


class SavingsProduct(SQLModel, table=True):
    __tablename__ = "savings_products"

    product_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    code: str = Field(unique=True, index=True, max_length=32)
    name: str
    term_months: int
    interest_rate: Decimal = Field(max_digits=6, decimal_places=4)
    early_withdrawal_rate: Decimal = Field(default=Decimal("0.001"), max_digits=6, decimal_places=4)
    min_amount: Decimal = Field(default=Decimal("100000.00"), max_digits=18, decimal_places=2)
    is_active: bool = Field(default=True, index=True)
    created_at: datetime
    updated_at: datetime
