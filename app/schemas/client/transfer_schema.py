from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import TransactionStatus, TransferType


class InternalTransferInitRequest(BaseModel):
    to_account_no: str = Field(min_length=4, max_length=32)
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    description: Optional[str] = Field(default=None, max_length=255)


class ExternalTransferInitRequest(BaseModel):
    to_bank_code: str = Field(min_length=2, max_length=16)
    to_account_number: str = Field(min_length=4, max_length=32)
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    description: Optional[str] = Field(default=None, max_length=255)


class TransferInitResponse(BaseModel):
    session_id: UUID
    transfer_type: TransferType
    to_account_no: str
    to_bank_code: Optional[str] = None
    to_name: str
    amount: Decimal
    fee: Decimal
    description: Optional[str] = None
    expires_at: datetime


class TransferConfirmRequest(BaseModel):
    session_id: UUID
    otp: str = Field(min_length=4, max_length=12)


class TransferConfirmResponse(BaseModel):
    transaction_id: UUID
    transaction_code: str
    transfer_type: TransferType
    status: TransactionStatus
    amount: Decimal
    new_balance: Decimal
    external_ref_id: Optional[str] = None
    failure_reason: Optional[str] = None
    created_at: datetime
