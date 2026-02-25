# app/models/user_model.py
import uuid
from datetime import datetime

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Text, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID, INET

class User(SQLModel, table=True):
    __tablename__ = "users"

    user_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(UUID(as_uuid=True), primary_key=True),
    )
    customer_id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), nullable=False, unique=True),
    )

    password_hash: str = Field(sa_column=Column(Text, nullable=False))
    is_active: bool = Field(default=True, sa_column=Column(Boolean, nullable=False, default=True))
    last_login_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))

    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    updated_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))

class UserSession(SQLModel, table=True):
    __tablename__ = "user_sessions"

    session_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(UUID(as_uuid=True), primary_key=True),
    )
    user_id: uuid.UUID = Field(sa_column=Column(UUID(as_uuid=True), nullable=False))
    refresh_token_hash: str = Field(sa_column=Column(Text, nullable=False))
    user_agent: str | None = Field(default=None, sa_column=Column(Text))
    ip_address: str | None = Field(default=None, sa_column=Column(INET))
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    expires_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    revoked_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))

class LoginAudit(SQLModel, table=True):
    __tablename__ = "login_audit"

    audit_id: int | None = Field(default=None, primary_key=True)
    user_id: uuid.UUID | None = Field(default=None, sa_column=Column(UUID(as_uuid=True)))
    occurred_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    ip_address: str | None = Field(default=None, sa_column=Column(INET))
    user_agent: str | None = Field(default=None, sa_column=Column(Text))
    success: bool = Field(sa_column=Column(Boolean, nullable=False))
    reason: str | None = Field(default=None, sa_column=Column(Text))
