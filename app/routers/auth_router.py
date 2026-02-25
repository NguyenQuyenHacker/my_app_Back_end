from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from passlib.context import CryptContext

from app.db.database import get_session
from app.models.user_model import User
from app.models.customer_model import Customer

# router = APIRouter()

# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# @router.post("/register")
# def register(data: RegisterRequest, session: Session = Depends(get_session)):
    
#     # 1️⃣ Check user tồn tại chưa
#     statement = select(User).where(User.phone == data.phone)
#     existing_user = session.exec(statement).first()

#     if existing_user:
#         raise HTTPException(status_code=400, detail="Phone already registered")

#     # 2️⃣ Hash password
#     hashed_password = pwd_context.hash(data.password)

#     # 3️⃣ Tạo user mới
#     new_user = User(
#         phone=data.phone,
#         hashed_password=hashed_password
#     )

#     session.add(new_user)
#     session.commit()
#     session.refresh(new_user)

#     return {
#         "message": "Register successful",
#         "user_id": new_user.id
#     }

# routers/auth_router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from passlib.context import CryptContext
from app.db.database import get_session
from app.models.customer_model import Customer
from app.schemas.auth_schema import UserLogin
from app.core.security import create_access_token
from app.models.user_model import User

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.post("/login")
def login(data: UserLogin, session: Session = Depends(get_session)):

    customer = session.exec(select(Customer).where(Customer.phone == data.phone)).first()
    user = session.exec(select(User).where(User.customer_id == customer.customer_id)).first()
    if not customer:
        raise HTTPException(status_code=400, detail="Phone not found")

    if not pwd_context.verify(data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Wrong password")

    access_token = create_access_token({"sub": str(customer.customer_id)})

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }