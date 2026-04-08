from __future__ import annotations

import re
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4
from sqlalchemy import Column, Text, DateTime, CheckConstraint
from sqlalchemy.dialects.postgresql import JSON, UUID as PG_UUID
from sqlmodel import SQLModel, Field


_DYNAMIC_DOCUMENT_CHUNK_MODELS: dict[str, type[SQLModel]] = {}


def validate_table_name(table_name: str) -> str:
    if not re.fullmatch(r"[a-zA-Z_][a-zA-Z0-9_]*", table_name):
        raise ValueError("Invalid table name")
    return table_name


def build_document_chunk_model(table_name: str):
    table_name = validate_table_name(table_name)

    if table_name in _DYNAMIC_DOCUMENT_CHUNK_MODELS:
        return _DYNAMIC_DOCUMENT_CHUNK_MODELS[table_name]

    DynamicDocumentChunk = type(
        f"DocumentChunk_{table_name}",
        (SQLModel,),
        {
            "__tablename__": table_name,
            "__table_args__": {"extend_existing": True},
            "__annotations__": {
                "langchain_id": UUID,
                "content": str,
                "embedding": Any,
                "langchain_metadata": Optional[dict],
            },
            "langchain_id": Field(
                sa_column=Column(PG_UUID(as_uuid=True), primary_key=True, nullable=False)
            ),
            "content": Field(sa_column=Column(Text, nullable=False)),
            "embedding": Field(default=None, sa_column=Column(nullable=False)),
            "langchain_metadata": Field(
                default=None,
                sa_column=Column(JSON, nullable=True),
            ),
        },
    )

    _DYNAMIC_DOCUMENT_CHUNK_MODELS[table_name] = DynamicDocumentChunk
    return DynamicDocumentChunk


class ParsingStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    success = "success"
    failed = "failed"


class KnowledgeBase(SQLModel, table=True):
    __tablename__ = "knowledge_bases"

    kb_id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(nullable=False, max_length=255)
    description: Optional[str] = Field(default=None)

    table_name: str = Field(nullable=False, max_length=255, unique=True, index=True)

    created_by: UUID = Field(nullable=False, index=True)

    document_count: int = Field(default=0, nullable=False)
    is_active: bool = Field(default=True, nullable=False)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class KnowledgeBaseDocument(SQLModel, table=True):
    __tablename__ = "knowledge_base_documents"

    document_id: UUID = Field(default_factory=uuid4, primary_key=True)

    kb_id: UUID = Field(
        foreign_key="knowledge_bases.kb_id",
        nullable=False,
        index=True,
    )

    file_name: str = Field(nullable=False, max_length=500)
    file_type: str = Field(nullable=False, max_length=20)

    vector_size: int = Field(nullable=False)
    chunk_size: int = Field(nullable=False)
    chunk_overlap: int = Field(nullable=False)
    retrieval_top_k: int = Field(nullable=False)

    is_enabled: bool = Field(default=True, nullable=False)

    parsing_status: ParsingStatus = Field(
        default=ParsingStatus.pending,
        nullable=False,
    )

    chunk_count: int = Field(default=0, nullable=False)

    uploaded_by: UUID = Field(nullable=False, index=True)

    upload_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    error_message: Optional[str] = Field(default=None)

class KnowledgeBaseConfig(SQLModel, table=True):
    __tablename__ = "knowledge_base_configs"

    __table_args__ = (
        CheckConstraint(
            "chunk_size >= 300 AND chunk_size <= 2000",
            name="chk_chunk_size_range",
        ),
        CheckConstraint(
            "chunk_overlap >= 0 AND chunk_overlap <= 400",
            name="chk_chunk_overlap_range",
        ),
        CheckConstraint(
            "chunk_overlap < chunk_size",
            name="chk_chunk_overlap_lt_size",
        ),
    )

    config_id: UUID = Field(default_factory=uuid4, primary_key=True)
    kb_id: UUID = Field(
        foreign_key="knowledge_bases.kb_id",
        nullable=False,
        unique=True,
        index=True,
    )

    chunk_size: int = Field(default=1000, nullable=False)
    chunk_overlap: int = Field(default=150, nullable=False)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


