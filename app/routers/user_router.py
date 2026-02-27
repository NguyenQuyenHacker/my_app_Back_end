# /app/routers/user_router.py

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.core.dependencies import get_current_user
from app.models.customer_model import Customer
from app.db.database import get_session

router = APIRouter()
  

@router.get("/customer")
def get_dashboard(
    current_user: Customer = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    # Ví dụ dữ liệu dashboard
    return {
            "phone": current_user.phone,
            "full_name": current_user.full_name,
            "email": current_user.email, 
            "permanent_address": current_user.permanent_address,
            "current_address": current_user.current_address,
            "dob": current_user.date_of_birth,
            "gender": current_user.gender,
            "created_at": current_user.created_at,
            "updated_at": current_user.updated_at,
        }