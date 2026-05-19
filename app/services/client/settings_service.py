import re
import uuid
from datetime import datetime

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.core.security import hash_password, verify_password
from app.crud import user_preferences_crud
from app.models.account_model import Account
from app.models.customer_model import Customer
from app.models.user_model import User
from app.schemas.client.settings_schema import (
    ChangePasswordRequest,
    ChangePinRequest,
    PreferencesUpdate,
    ProfileUpdateRequest,
)


PROFILE_EDITABLE_FIELDS = (
    "full_name",
    "email",
    "phone",
    "current_address",
)


def _get_user_by_customer_id(session: Session, customer_id: uuid.UUID) -> User:
    user = session.exec(
        select(User).where(User.customer_id == customer_id)
    ).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def get_preferences_service(session: Session, customer: Customer):
    user = _get_user_by_customer_id(session, customer.customer_id)
    return user_preferences_crud.get_or_create_preferences(session, user.user_id)


def update_preferences_service(
    session: Session, customer: Customer, payload: PreferencesUpdate
):
    user = _get_user_by_customer_id(session, customer.customer_id)
    return user_preferences_crud.update_preferences(
        session,
        user_id=user.user_id,
        theme=payload.theme,
        language=payload.language,
    )


def update_profile_service(
    session: Session, customer: Customer, payload: ProfileUpdateRequest
):
    user = _get_user_by_customer_id(session, customer.customer_id)

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mật khẩu xác nhận không đúng",
        )

    changed = False
    for field in PROFILE_EDITABLE_FIELDS:
        value = getattr(payload, field)
        if value is not None and value != getattr(customer, field):
            setattr(customer, field, value)
            changed = True

    if not changed:
        return customer

    customer.updated_at = datetime.utcnow()
    session.add(customer)
    session.commit()
    session.refresh(customer)
    return customer


def _validate_new_password(new_password: str) -> None:
    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="Mật khẩu mới tối thiểu 8 ký tự")
    if not re.search(r"[A-Z]", new_password):
        raise HTTPException(status_code=400, detail="Mật khẩu mới cần ít nhất 1 chữ hoa")
    if not re.search(r"\d", new_password):
        raise HTTPException(status_code=400, detail="Mật khẩu mới cần ít nhất 1 chữ số")


def change_password_service(
    session: Session, customer: Customer, payload: ChangePasswordRequest
):
    user = _get_user_by_customer_id(session, customer.customer_id)

    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Mật khẩu hiện tại không đúng")

    if payload.current_password == payload.new_password:
        raise HTTPException(status_code=400, detail="Mật khẩu mới phải khác mật khẩu cũ")

    _validate_new_password(payload.new_password)

    user.password_hash = hash_password(payload.new_password)
    user.updated_at = datetime.utcnow()
    session.add(user)
    session.commit()


def change_pin_service(
    session: Session, customer: Customer, payload: ChangePinRequest
):
    account = session.exec(
        select(Account).where(
            Account.account_id == payload.account_id,
            Account.customer_id == customer.customer_id,
        )
    ).first()

    if not account:
        raise HTTPException(status_code=404, detail="Tài khoản không tồn tại")

    if not verify_password(payload.current_pin, account.otp_hash):
        raise HTTPException(status_code=400, detail="PIN hiện tại không đúng")

    if payload.current_pin == payload.new_pin:
        raise HTTPException(status_code=400, detail="PIN mới phải khác PIN cũ")

    if not payload.new_pin.isdigit():
        raise HTTPException(status_code=400, detail="PIN chỉ gồm chữ số")

    account.otp_hash = hash_password(payload.new_pin)
    account.updated_at = datetime.utcnow()
    session.add(account)
    session.commit()


def get_last_login_service(session: Session, customer: Customer):
    user = _get_user_by_customer_id(session, customer.customer_id)
    return user.last_login_at
