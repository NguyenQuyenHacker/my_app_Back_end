from app.db.database import get_session_admin
from typing import Annotated
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlmodel import Session, select

from app.core.security import SECRET_KEY, ALGORITHM
from app.db.database import get_session
from app.models.customer_model import Customer
from app.models.admin_model import Admin

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
admin_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="admin/login")

SessionDep = Annotated[Session, Depends(get_session)]
SessionAdminDep = Annotated[Session, Depends(get_session_admin)]


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: SessionDep,
) -> Customer:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        role = payload.get("role")

        if not sub:
            raise unauthorized

        if role != "client":
            raise unauthorized

        customer_id = uuid.UUID(sub)
    except (JWTError, ValueError):
        raise unauthorized

    customer = session.exec(
        select(Customer).where(Customer.customer_id == customer_id)
    ).first()

    if not customer:
        raise unauthorized

    return customer


def get_current_admin(
    token: Annotated[str, Depends(admin_oauth2_scheme)],
    session: SessionAdminDep,
) -> Admin:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid admin authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        role = payload.get("role")

        if not sub:
            raise unauthorized

        if role != "admin":
            raise unauthorized

        admin_id = uuid.UUID(sub)
    except (JWTError, ValueError):
        raise unauthorized

    admin = session.exec(
        select(Admin).where(Admin.admin_id == admin_id)
    ).first()

    if not admin:
        raise unauthorized

    if not admin.is_active:
        raise unauthorized

    return admin


CurrentUserDep = Annotated[Customer, Depends(get_current_user)]
CurrentAdminDep = Annotated[Admin, Depends(get_current_admin)]