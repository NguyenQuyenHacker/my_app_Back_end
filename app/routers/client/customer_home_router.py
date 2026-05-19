from fastapi import APIRouter

from app.core.dependencies import CurrentUserDep, SessionDep
from app.services.client.customer_home_service import build_customer_home

router = APIRouter(tags=["customer-home"])


@router.get("/home-page")
def get_customer_home(
    current_user: CurrentUserDep,
    session: SessionDep,
):
    return build_customer_home(current_user)
