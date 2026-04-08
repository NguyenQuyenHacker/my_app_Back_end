# app/services/admin/admin_info_service.py
from sqlmodel import Session, select

from app.models.admin_model import Admin
from app.schemas.admin.admin_schema import AdminRead


def get_admin_info_service(session: Session) -> AdminRead | None:
    admin = session.exec(   
        select(Admin).order_by(Admin.created_at.desc())
    ).first()

    if not admin:
        return None

    return AdminRead(
        admin_name=admin.admin_name,
        admin_code=admin.admin_code,
    )