from fastapi import APIRouter, status

from app.core.dependencies import CurrentUserDep, SessionDep
from app.schemas.client.settings_schema import (
    ChangePasswordRequest,
    ChangePinRequest,
    LastLoginResponse,
    MessageResponse,
    PreferencesRead,
    PreferencesUpdate,
    ProfileUpdateRequest,
)
from app.services.client import settings_service
from app.services.client.customer_info_service import build_customer_info

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/preferences", response_model=PreferencesRead)
def get_preferences(current_user: CurrentUserDep, session: SessionDep):
    return settings_service.get_preferences_service(session, current_user)


@router.patch("/preferences", response_model=PreferencesRead)
def update_preferences(
    payload: PreferencesUpdate,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    return settings_service.update_preferences_service(session, current_user, payload)


@router.post("/profile/update")
def update_profile(
    payload: ProfileUpdateRequest,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    customer = settings_service.update_profile_service(session, current_user, payload)
    return build_customer_info(customer)


@router.post(
    "/security/change-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
)
def change_password(
    payload: ChangePasswordRequest,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    settings_service.change_password_service(session, current_user, payload)
    return MessageResponse(message="Đổi mật khẩu thành công")


@router.post(
    "/security/change-pin",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
)
def change_pin(
    payload: ChangePinRequest,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    settings_service.change_pin_service(session, current_user, payload)
    return MessageResponse(message="Đổi PIN thành công")


@router.get("/security/last-login", response_model=LastLoginResponse)
def get_last_login(current_user: CurrentUserDep, session: SessionDep):
    last_login_at = settings_service.get_last_login_service(session, current_user)
    return LastLoginResponse(last_login_at=last_login_at)
