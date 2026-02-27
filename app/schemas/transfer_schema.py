import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlmodel import SQLModel


class TransferCreate(SQLModel):
    sender_account_id: Optional[uuid.UUID] = None
    receiver_account_id: Optional[uuid.UUID] = None

    sender_bank_name: Optional[str] = None
    sender_name: Optional[str] = None
    sender_account_no: Optional[str] = None

    receiver_bank_name: str
    receiver_name: str
    receiver_account_no: str

    amount: Decimal
    description: Optional[str] = None
    reference_no: Optional[str] = None
    otp: Optional[str] = None


class TransferRead(SQLModel):
    transfer_id: uuid.UUID
    sender_account_id: Optional[uuid.UUID] = None
    receiver_account_id: Optional[uuid.UUID] = None
    sender_bank_name: Optional[str] = None
    sender_name: Optional[str] = None
    sender_account_no: Optional[str] = None
    receiver_bank_name: str
    receiver_name: str
    receiver_account_no: str
    amount: Decimal
    description: Optional[str] = None
    reference_no: Optional[str] = None
    created_at: datetime
    executed_at: datetime


class EntryRead(SQLModel):
    entry_id: uuid.UUID
    transfer_id: uuid.UUID
    account_id: uuid.UUID
    amount: Decimal
    balance_before: Decimal
    balance_after: Decimal
    note: Optional[str] = None
    created_at: datetime