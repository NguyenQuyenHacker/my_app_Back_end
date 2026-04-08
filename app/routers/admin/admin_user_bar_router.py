# app/routers/admin/admin_user_bar_router.py
from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db.database import get_session_admin, get_session
from app.schemas.admin.admin_user_bar_schema import AdminUserBarRead
from app.services.admin.admin_user_bar_service import (
    get_admin_customer_bars_service,
    update_customer_active_status_service,
)
from app.schemas.admin.admin_user_status_schema import AdminUserStatusUpdate

router = APIRouter(prefix="/admin", tags=["Admin Users"])


@router.get("/customers", response_model=list[AdminUserBarRead])
def get_admin_customers(session: Session = Depends(get_session)):
    return get_admin_customer_bars_service(session)

@router.patch("/customers/{account_no}/status")
def update_customer_status(
    account_no: str,
    data: AdminUserStatusUpdate,
    session: Session = Depends(get_session),
):
    return update_customer_active_status_service(
        account_no=account_no,
        is_active=data.is_active,
        session=session,
    )