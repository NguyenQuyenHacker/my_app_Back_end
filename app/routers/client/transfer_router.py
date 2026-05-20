from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlmodel import Session, select

from app.core.dependencies import get_current_user
from app.db.database import get_session
from app.models.account_model import Account
from app.models.customer_model import Customer
from app.models.enums import AccountStatus, ExternalBankAccountStatus
from app.models.external_bank_account_model import ExternalBankAccount
from app.schemas.client.transfer_schema import (
    ExternalTransferInitRequest,
    InternalTransferInitRequest,
    TransferConfirmRequest,
    TransferConfirmResponse,
    TransferInitResponse,
)
from app.services.client import (
    transfer_external_service,
    transfer_internal_service,
)

router = APIRouter(prefix="/api/transfer", tags=["transfer"])


@router.get("/lookup/internal")
def lookup_internal_recipient(
    account_no: str = Query(..., min_length=4, max_length=32),
    current_user: Customer = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    acc = session.exec(select(Account).where(Account.account_no == account_no)).first()
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")
    if acc.status != AccountStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Account is not ACTIVE")
    if acc.customer_id == current_user.customer_id:
        raise HTTPException(status_code=400, detail="Cannot transfer to your own account")
    cust = session.exec(select(Customer).where(Customer.customer_id == acc.customer_id)).first()
    if not cust:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {
        "account_no": acc.account_no,
        "bank_code": acc.bank_name,
        "full_name": cust.full_name,
    }


@router.get("/lookup/external")
def lookup_external_recipient(
    bank_code: str = Query(..., min_length=2, max_length=16),
    account_number: str = Query(..., min_length=4, max_length=32),
    current_user: Customer = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    acc = session.exec(
        select(ExternalBankAccount).where(
            ExternalBankAccount.bank_code == bank_code,
            ExternalBankAccount.account_number == account_number,
        )
    ).first()
    if not acc:
        raise HTTPException(status_code=404, detail="External account not found")
    if acc.status != ExternalBankAccountStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="External account is not ACTIVE")
    return {
        "account_no": acc.account_number,
        "bank_code": acc.bank_code,
        "full_name": acc.account_holder_name,
    }


@router.post("/internal/init", response_model=TransferInitResponse)
def internal_init(
    payload: InternalTransferInitRequest,
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
    current_user: Customer = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return transfer_internal_service.init_internal_transfer(
        session,
        current_user=current_user,
        payload=payload,
        idempotency_key=idempotency_key,
    )


@router.post("/internal/confirm", response_model=TransferConfirmResponse)
def internal_confirm(
    payload: TransferConfirmRequest,
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
    current_user: Customer = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return transfer_internal_service.confirm_internal_transfer(
        session,
        current_user=current_user,
        payload=payload,
        idempotency_key=idempotency_key,
    )


@router.post("/external/init", response_model=TransferInitResponse)
def external_init(
    payload: ExternalTransferInitRequest,
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
    current_user: Customer = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return transfer_external_service.init_external_transfer(
        session,
        current_user=current_user,
        payload=payload,
        idempotency_key=idempotency_key,
    )


@router.post("/external/confirm", response_model=TransferConfirmResponse)
def external_confirm(
    payload: TransferConfirmRequest,
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
    current_user: Customer = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return transfer_external_service.confirm_external_transfer(
        session,
        current_user=current_user,
        payload=payload,
        idempotency_key=idempotency_key,
    )
