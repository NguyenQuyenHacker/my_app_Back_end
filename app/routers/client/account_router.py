from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.dependencies import CurrentUserDep, SessionDep
from app.schemas.client.account_schema import (
    BalanceResponse,
    TransactionFilterQuery,
    TransactionListResponse,
)
from app.services.client.account_service import (
    get_account_overview_data,
    get_balance_data,
    get_transactions_data,
)

router = APIRouter()


@router.get("/account")
def get_account_overview(
    current_user: CurrentUserDep,
    session: SessionDep,
):
    return get_account_overview_data(session, current_user)


@router.get("/api/account/balance", response_model=BalanceResponse, tags=["account"])
def get_account_balance(
    current_user: CurrentUserDep,
    session: SessionDep,
):
    return get_balance_data(session, current_user)


@router.get(
    "/api/account/transactions",
    response_model=TransactionListResponse,
    tags=["account"],
)
def get_account_transactions(
    current_user: CurrentUserDep,
    session: SessionDep,
    filters: Annotated[TransactionFilterQuery, Depends()],
):
    return get_transactions_data(
        session=session,
        current_user=current_user,
        limit=filters.limit,
        direction=filters.direction,
        date_from=filters.date_from,
        date_to=filters.date_to,
        min_amount=filters.min_amount,
        max_amount=filters.max_amount,
    )