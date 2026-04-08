# routers/admin/auth_admin_router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db.database import get_session_admin
from app.core.dependencies import CurrentAdminDep
from app.models.admin_model import Admin
from app.schemas.auth_schema import AdminLoginRequest
from app.schemas.admin.admin_schema import AdminRead
from app.core.security import verify_password, create_access_token

router = APIRouter(prefix="/admin", tags=["Admin Auth"])


@router.post("/login")
def login_admin(data: AdminLoginRequest, session: Session = Depends(get_session_admin)):
    admin = session.exec(
        select(Admin).where(Admin.email == data.email)
    ).first()

    if not admin or not verify_password(data.password, admin.password_hash):
        raise HTTPException(
            status_code=401, 
            detail="Invalid email or password"
        )

    if not admin.is_active:
        raise HTTPException(
            status_code=401, 
            detail="ADMIN_LOCKED"
        )

    access_token = create_access_token({
        "sub": str(admin.admin_id),
        "role": "admin"
    })

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "admin_name": admin.admin_name,
        "admin_code": admin.admin_code
    }


@router.get("/me", response_model=AdminRead)
def get_admin_me(current_admin: CurrentAdminDep):
    """
    Get current logged-in admin information.
    """
    return current_admin