# app/models/admin_model.py
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, String


class Admin(SQLModel, table=True):
    __tablename__ = "admins"

    admin_id: UUID = Field(default_factory=uuid4, primary_key=True)
    is_active: bool = Field(default=True, nullable=False)
    last_login_at: Optional[datetime] = Field(default=None, nullable=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)

    admin_name: str = Field(nullable=False, max_length=255)
    email: str = Field(nullable=False, index=True, max_length=255)
    password_hash: str = Field(nullable=False)
    role: str = Field(default="admin", nullable=False, max_length=50)

    admin_code: str = Field(sa_column=Column(String(9), unique=True, nullable=False, index=True))