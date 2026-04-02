# routers/admin/auth_admin_router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db.database import get_session
from app.models.admin_model import Admin
from app.schemas.auth_schema import AdminLoginRequest
from app.core.security import verify_password, create_access_token

router = APIRouter(prefix="/admin", tags=["Admin Auth"])


@router.post("/login")
def login_admin(data: AdminLoginRequest, session: Session = Depends(get_session)):
    admin = session.exec(
        select(Admin).where(Admin.email == data.email)
    ).first()

    if not admin:
        raise HTTPException(status_code=400, detail="Email not found")

    if not verify_password(data.password, admin.password_hash):
        raise HTTPException(status_code=400, detail="Wrong password")

    access_token = create_access_token({
        "sub": str(admin.admin_id),
        "role": "admin"
    })

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }