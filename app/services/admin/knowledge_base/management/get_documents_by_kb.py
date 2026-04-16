from sqlmodel import Session, select
from uuid import UUID
from app.models.knowledge_bases_model import KnowledgeBase, KnowledgeBaseDocument

def get_documents_by_kb_id_service(session: Session, kb_id: UUID):
    kb = session.get(KnowledgeBase, kb_id)
    if not kb:
        return None

    statement = (
        select(KnowledgeBaseDocument)
        .where(KnowledgeBaseDocument.kb_id == kb_id)
        .order_by(KnowledgeBaseDocument.upload_at.desc())
    )

    documents = session.exec(statement).all()

    return [
        {
            "document_id": doc.document_id,
            "kb_id": doc.kb_id,
            "file_name": doc.file_name,
            "parsing_status": doc.parsing_status.value if hasattr(doc.parsing_status, "value") else str(doc.parsing_status),
            "chunk_count": doc.chunk_count,
            "upload_date": doc.upload_at,
        }
        for doc in documents
    ]
