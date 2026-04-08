# app/services/admin/admin_user_bar_service.py
from sqlmodel import Session, select
from fastapi import HTTPException

from app.models.customer_model import Customer
from app.models.account_model import Account
from app.models.user_model import User
from app.schemas.admin.admin_user_bar_schema import AdminUserBarRead


def get_admin_customer_bars_service(session: Session) -> list[AdminUserBarRead]:
    statement = (
        select(
            Customer.full_name,
            Account.account_no,
            User.is_active,
        )
        .join(User, User.customer_id == Customer.customer_id)
        .join(Account, Account.customer_id == Customer.customer_id)
        .order_by(Customer.created_at.desc())
    )

    results = session.exec(statement).all()

    return [
        AdminUserBarRead(
            full_name=row.full_name,
            account_no=row.account_no,
            is_active=row.is_active,
        )
        for row in results
    ]

def update_customer_active_status_service(
    account_no: str,
    is_active: bool,
    session: Session,
):
    account = session.exec(
        select(Account).where(Account.account_no == account_no)
    ).first()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    user = session.exec(
        select(User).where(User.customer_id == account.customer_id)
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = is_active
    session.add(user)
    session.commit()
    session.refresh(user)

    return {
        "message": "Updated successfully",
        "account_no": account_no,
        "is_active": user.is_active,
    }