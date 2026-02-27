from fastapi import APIRouter

from app.core.dependencies import CurrentUserDep, SessionDep
from app.services.account_service import get_account_overview_data

router = APIRouter()


@router.get("/account")
def get_account_overview(
    current_user: CurrentUserDep,
    session: SessionDep,
):
    return get_account_overview_data(session, current_user)