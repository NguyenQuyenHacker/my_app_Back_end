
from typing import Annotated
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlmodel import Session, select

from app.core.security import SECRET_KEY, ALGORITHM
from app.db.database import get_session
from app.models.customer_model import Customer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


SessionDep = Annotated[Session, Depends(get_session)]


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
        if not sub:
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


CurrentUserDep = Annotated[Customer, Depends(get_current_user)]