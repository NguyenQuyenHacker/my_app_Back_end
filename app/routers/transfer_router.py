from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.dependencies import get_current_user
from app.db.database import get_session
from app.models.customer_model import Customer
from app.schemas.transfer_schema import TransferCreateRequest, TransferCreateResponse
from app.services.transfer_service import create_transfer_service

router = APIRouter(prefix="/transfer", tags=["transfer"])


@router.post("", response_model=TransferCreateResponse)
def create_transfer(
    payload: TransferCreateRequest,
    current_user: Customer = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return create_transfer_service(session, current_user, payload)