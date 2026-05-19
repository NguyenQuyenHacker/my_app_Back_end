from typing import Optional

from fastapi import APIRouter, Depends, Header
from sqlmodel import Session

from app.core.dependencies import get_current_user
from app.db.database import get_session
from app.models.customer_model import Customer
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
