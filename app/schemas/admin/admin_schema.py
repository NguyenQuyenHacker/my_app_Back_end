# app/schemas/admin/admin_schema.py
from sqlmodel import SQLModel


class AdminRead(SQLModel):
    admin_name: str
    admin_code: str