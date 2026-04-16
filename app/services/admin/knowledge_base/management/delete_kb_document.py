from sqlmodel import Session, select, func
from fastapi import HTTPException, status
from uuid import UUID
from sqlalchemy import text
from sqlalchemy import text, delete
from app.models.knowledge_bases_model import KnowledgeBase, KnowledgeBaseDocument, ParsingStatus
from app.services.admin.knowledge_base.management.kb_utils import get_chunk_table

def delete_kb_document_service(session: Session, kb_id: UUID, document_id: UUID):
    # 1. Tìm thông tin Knowledge Base và Document
    kb = session.get(KnowledgeBase, kb_id)
    if not kb:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge Base không tồn tại."
        )

    document = session.get(KnowledgeBaseDocument, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document không tồn tại."
        )
    
    # Kiểm tra document có thuộc về KB này không
    if document.kb_id != kb_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tài liệu không thuộc bản Knowledge Base này."
        )

    try:
        # 2. Xóa các chunks trong Vector DB (Postgres table)
        # Sử dụng hàm get_chunk_table để lấy Table object từ DB 
        chunk_table = get_chunk_table(session, kb.table_name)
        
        # Cú pháp SQLAlchemy an toàn, tương đương: langchain_metadata->>'document_id'
        delete_stmt = delete(chunk_table).where(
            chunk_table.c.langchain_metadata["document_id"].astext == str(document_id)
        )
        session.execute(delete_stmt)

        # 3. Xóa bản ghi trong knowledge_base_documents
        session.delete(document)
        session.flush() # Flush để database cập nhật trạng thái xóa trước khi đếm lại
        
        # 4. Cập nhật lại document_count và updated_at cho Knowledge Base
        from datetime import datetime, timezone
        success_count = session.scalar(
            select(func.count(KnowledgeBaseDocument.document_id))
            .where(KnowledgeBaseDocument.kb_id == kb_id)
            .where(KnowledgeBaseDocument.parsing_status == ParsingStatus.success)
        )
        
        kb.document_count = success_count if success_count is not None else 0
        kb.updated_at = datetime.now(timezone.utc)
        
        session.add(kb)
        session.commit()

        return {
            "message": "Xóa document và dữ liệu vector thành công.",
        }

    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi xóa document: {str(e)}"
        )
