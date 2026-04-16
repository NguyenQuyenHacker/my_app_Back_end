from sqlmodel import Session, select
from app.models.knowledge_bases_model import KnowledgeBase, KnowledgeBaseConfig
from app.models.admin_model import Admin

def get_all_knowledge_bases(session: Session):
    statement = (
        select(
            KnowledgeBase.kb_id,
            KnowledgeBase.name,
            KnowledgeBase.description,
            KnowledgeBase.table_name,
            KnowledgeBase.document_count,
            KnowledgeBase.is_active,
            Admin.admin_name,
            KnowledgeBase.updated_at,
            KnowledgeBaseConfig.chunk_size,
            KnowledgeBaseConfig.chunk_overlap,
        )
        .join(Admin, KnowledgeBase.created_by == Admin.admin_id)
        .outerjoin(KnowledgeBaseConfig, KnowledgeBase.kb_id == KnowledgeBaseConfig.kb_id)
    )

    rows = session.exec(statement).all()

    return [
        {
            "kb_id": row.kb_id,
            "name": row.name,
            "description": row.description,
            "table_name": row.table_name,
            "document_count": row.document_count,
            "admin_name": row.admin_name,
            "chunk_size": row.chunk_size if row.chunk_size is not None else 1000,
            "chunk_overlap": row.chunk_overlap if row.chunk_overlap is not None else 150,
            "updated_at": row.updated_at,
            "is_active": row.is_active,
        }
        for row in rows
    ]
