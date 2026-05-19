from fastapi import APIRouter

from app.core.dependencies import CurrentUserDep, SessionDep
from app.services.client.customer_info_service import build_customer_info

router = APIRouter(tags=["customer-info"])


@router.get("/info")
def get_customer_info(
    current_user: CurrentUserDep,
    session: SessionDep,
):
    return build_customer_info(current_user)
