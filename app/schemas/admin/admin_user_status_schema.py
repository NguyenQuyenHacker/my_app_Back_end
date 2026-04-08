# app/schemas/admin/admin_user_status_schema.py
from sqlmodel import SQLModel


class AdminUserStatusUpdate(SQLModel):
    is_active: bool