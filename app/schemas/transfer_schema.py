from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from datetime import datetime

class TransferCreate(BaseModel):
    from_account_id: UUID
    to_account_no: str
    to_bank_code: Optional[str] = None
    to_name: Optional[str] = None
    type: str  # INTERNAL/INTERBANK
    amount: float
    currency: str = "VND"
    note: Optional[str] = None
    idempotency_key: Optional[str] = None

class TransferOut(BaseModel):
    transfer_id: UUID
    customer_id: UUID
    from_account_id: UUID
    to_account_no: str
    to_bank_code: Optional[str] = None
    to_name: Optional[str] = None
    type: str
    status: str
    amount: float
    currency: str
    fee_amount: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
