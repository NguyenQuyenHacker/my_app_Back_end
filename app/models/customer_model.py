# app/models/customer_model.py
import uuid
from datetime import date, datetime

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Text, Date, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Enum as SAEnum

from app.models.enums import GenderType

class Customer(SQLModel, table=True):
    __tablename__ = "customers"

    customer_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(UUID(as_uuid=True), primary_key=True),
    )

    full_name: str = Field(sa_column=Column(Text, nullable=False))
    cccd_number: str = Field(sa_column=Column(Text, nullable=False, unique=True))

    date_of_birth: date = Field(sa_column=Column(Date, nullable=False))
    gender: GenderType = Field(sa_column=Column(SAEnum(GenderType, name="gender_type"), nullable=False))

    permanent_address: str = Field(sa_column=Column(Text, nullable=False))
    current_address: str = Field(sa_column=Column(Text, nullable=False))
    occupation: str = Field(sa_column=Column(Text, nullable=False))

    email: str | None = Field(default=None, sa_column=Column(Text, unique=True))
    phone: str = Field(sa_column=Column(Text, nullable=False, unique=True))

    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    updated_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
