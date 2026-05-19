# app/models/user_preferences_model.py
import uuid
from datetime import datetime

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID


class UserPreferences(SQLModel, table=True):
    __tablename__ = "user_preferences"

    user_id: uuid.UUID = Field(
        sa_column=Column(
            UUID(as_uuid=True),
            primary_key=True,
        ),
    )
    theme: str = Field(sa_column=Column(Text, nullable=False, default="system"))
    language: str = Field(sa_column=Column(Text, nullable=False, default="vi"))
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
