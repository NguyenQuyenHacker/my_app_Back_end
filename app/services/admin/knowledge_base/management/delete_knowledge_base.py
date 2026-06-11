from sqlmodel import Session, delete
from sqlalchemy import inspect, text
from fastapi import HTTPException, status
from uuid import UUID

from app.models.knowledge_bases_model import (
    KnowledgeBase,
    KnowledgeBaseDocument,
    KnowledgeBaseConfig,
)


def delete_knowledge_base_service(session: Session, kb_id: UUID):
    kb = session.get(KnowledgeBase, kb_id)
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge Base không tồn tại.",
        )

    table_name = kb.table_name

    try:
        # 1. Drop physical vector table nếu tồn tại
        bind = session.get_bind()
        if inspect(bind).has_table(table_name):
            session.execute(text(f'DROP TABLE IF EXISTS "{table_name}" CASCADE'))

        # 2. Xoá documents thuộc KB
        session.execute(
            delete(KnowledgeBaseDocument).where(KnowledgeBaseDocument.kb_id == kb_id)
        )

        # 3. Xoá config
        session.execute(
            delete(KnowledgeBaseConfig).where(KnowledgeBaseConfig.kb_id == kb_id)
        )

        # 4. Xoá KB record
        session.delete(kb)
        session.commit()

        return {
            "message": "Xoá Knowledge Base thành công.",
            "kb_id": str(kb_id),
            "table_name": table_name,
        }

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi xoá Knowledge Base: {e}",
        )
