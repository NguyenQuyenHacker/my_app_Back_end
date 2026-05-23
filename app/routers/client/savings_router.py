import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Header, Query
from sqlmodel import Session

from app.core.dependencies import get_current_user
from app.db.database import get_session
from app.models.customer_model import Customer
from app.models.enums import SavingsAccountStatus
from app.schemas.client.savings_schema import (
    EarlyWithdrawConfirmResponse,
    EarlyWithdrawInitResponse,
    SavingsAccountOut,
    SavingsConfirmRequest,
    SavingsConfirmResponse,
    SavingsDetailOut,
    SavingsInitRequest,
    SavingsInitResponse,
    SavingsPreviewRequest,
    SavingsPreviewResponse,
    SavingsProductOut,
)
from app.services.client import savings_service

router = APIRouter(prefix="/api/savings", tags=["savings"])


@router.get("/products", response_model=list[SavingsProductOut])
def get_products(session: Session = Depends(get_session)):
    return savings_service.list_products(session)


@router.post("/preview", response_model=SavingsPreviewResponse)
def preview(
    payload: SavingsPreviewRequest,
    current_user: Customer = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return savings_service.preview(session, payload)


@router.post("/init", response_model=SavingsInitResponse)
def init(
    payload: SavingsInitRequest,
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
    current_user: Customer = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return savings_service.init_deposit(
        session,
        current_user=current_user,
        payload=payload,
        idempotency_key=idempotency_key,
    )


@router.post("/confirm", response_model=SavingsConfirmResponse)
def confirm(
    payload: SavingsConfirmRequest,
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
    current_user: Customer = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return savings_service.confirm_deposit(
        session,
        current_user=current_user,
        session_id=payload.session_id,
        otp=payload.otp,
        idempotency_key=idempotency_key,
    )


@router.get("/my-accounts", response_model=list[SavingsAccountOut])
def my_accounts(
    status: Optional[SavingsAccountStatus] = Query(default=None),
    current_user: Customer = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return savings_service.list_my_accounts(session, current_user=current_user, status=status)


@router.get("/{savings_id}", response_model=SavingsDetailOut)
def detail(
    savings_id: uuid.UUID,
    current_user: Customer = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return savings_service.get_detail(session, current_user=current_user, savings_id=savings_id)


@router.post("/{savings_id}/early-withdraw-init", response_model=EarlyWithdrawInitResponse)
def early_withdraw_init(
    savings_id: uuid.UUID,
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
    current_user: Customer = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return savings_service.init_early_withdraw(
        session,
        current_user=current_user,
        savings_id=savings_id,
        idempotency_key=idempotency_key,
    )


@router.post("/{savings_id}/early-withdraw-confirm", response_model=EarlyWithdrawConfirmResponse)
def early_withdraw_confirm(
    savings_id: uuid.UUID,
    payload: SavingsConfirmRequest,
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
    current_user: Customer = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return savings_service.confirm_early_withdraw(
        session,
        current_user=current_user,
        session_id=payload.session_id,
        otp=payload.otp,
        idempotency_key=idempotency_key,
    )
