from typing import Optional
from uuid import UUID

from datetime import datetime
from pydantic import BaseModel, Field


class KnowledgeBaseCreate(BaseModel):
    name: str = Field(..., max_length=255)
    table_name: str = Field(..., max_length=255, pattern=r"^[a-zA-Z_][a-zA-Z0-9_]*$")
    description: Optional[str] = None


class KnowledgeBaseRead(BaseModel):
    kb_id: UUID
    name: str
    description: str | None = None
    table_name: str
    document_count: int
    admin_name: str
    chunk_size: int
    chunk_overlap: int
    updated_at: datetime

class KnowledgeBaseDocumentRead(BaseModel):
    document_id: UUID
    kb_id: UUID
    file_name: str
    parsing_status: str
    chunk_count: int
    upload_date: datetime

class KnowledgeBaseConfigUpdate(BaseModel):
    chunk_size: int = Field(..., ge=300, le=2000)
    chunk_overlap: int = Field(..., ge=0, le=400)

class KnowledgeBaseConfigRead(KnowledgeBaseConfigUpdate):
    config_id: UUID
    kb_id: UUID
    updated_at: datetime
