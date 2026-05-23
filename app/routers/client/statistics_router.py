from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.core.dependencies import get_current_user
from app.db.database import get_session
from app.models.customer_model import Customer
from app.schemas.client.statistics_schema import (
    DailyOut,
    ExpenseByTypeOut,
    OverviewOut,
    TopRecipientsOut,
    TrendOut,
)
from app.services.client import statistics_service

router = APIRouter(prefix="/api/statistics", tags=["statistics"])


@router.get("/overview", response_model=OverviewOut)
def overview(
    month: Optional[str] = Query(default=None, description="Format: YYYY-MM"),
    current_user: Customer = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return statistics_service.overview(session, current_user=current_user, month=month)


@router.get("/expense-by-type", response_model=ExpenseByTypeOut)
def expense_by_type(
    month: Optional[str] = Query(default=None),
    current_user: Customer = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return statistics_service.expense_by_type(session, current_user=current_user, month=month)


@router.get("/daily", response_model=DailyOut)
def daily(
    month: Optional[str] = Query(default=None),
    current_user: Customer = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return statistics_service.daily(session, current_user=current_user, month=month)


@router.get("/top-recipients", response_model=TopRecipientsOut)
def top_recipients(
    month: Optional[str] = Query(default=None),
    limit: int = Query(default=5, ge=1, le=50),
    current_user: Customer = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return statistics_service.top_recipients(session, current_user=current_user, month=month, limit=limit)


@router.get("/trend", response_model=TrendOut)
def trend(
    months: int = Query(default=6, ge=1, le=24),
    current_user: Customer = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return statistics_service.trend(session, current_user=current_user, months=months)
