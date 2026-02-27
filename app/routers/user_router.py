# /app/routers/user_router.py

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.core.dependencies import get_current_user
from app.models.customer_model import Customer
from app.db.database import get_session
from app.services.customer_service import build_customer_overview
from app.core.dependencies import CurrentUserDep, SessionDep

router = APIRouter()
  

@router.get("/overview")
def get_dashboard(
    current_user: CurrentUserDep,
    session: SessionDep,
):
    return build_customer_overview(current_user)