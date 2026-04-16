from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import select
from sqlmodel import Session
from app.models.knowledge_bases_model import KnowledgeBase, KnowledgeBaseDocument
from app.services.admin.knowledge_base.management.kb_utils import get_chunk_table

def get_document_chunks_service(session: Session, kb_id: UUID, document_id: UUID):
    document = session.get(KnowledgeBaseDocument, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.kb_id != kb_id:
        raise HTTPException(
            status_code=400, 
            detail="Tài liệu không thuộc bản Knowledge Base này."
        )

    kb = session.get(KnowledgeBase, kb_id)
    if kb is None:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    chunk_table = get_chunk_table(session, kb.table_name)

    stmt = (
        select(chunk_table.c.content)
        .where(chunk_table.c.langchain_metadata["file_name"].astext == document.file_name)
    )

    return session.execute(stmt).scalars().all()
