# app/schemas/admin/admin_user_bar_schema.py
from sqlmodel import SQLModel


class AdminUserBarRead(SQLModel):
    full_name: str
    account_no: str
    is_active: bool