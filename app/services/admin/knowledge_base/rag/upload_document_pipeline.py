from sqlmodel import Session, select, func
from fastapi import HTTPException, UploadFile
from uuid import UUID
from datetime import datetime, timezone
import os
import traceback
import logging

from app.models.knowledge_bases_model import KnowledgeBase, KnowledgeBaseDocument, ParsingStatus
from app.services.admin.knowledge_base.rag.extract_document_content import _extract_documents_from_upload_file
from app.services.admin.knowledge_base.rag.split_document_chunks import _split_documents
from app.services.admin.knowledge_base.rag.store_vectors_pg import init_and_store_vectors
from app.utils.embedding_utils import get_embedding_model

logger = logging.getLogger(__name__)

def upload_document_to_kb_service(
    session: Session, 
    kb_id: UUID, 
    file: UploadFile, 
    chunk_size: int, 
    chunk_overlap: int, 
    admin_id: UUID
):
    # 1. Kiểm tra tồn tại
    kb = session.get(KnowledgeBase, kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    # 1.5 Kiểm tra file trùng tên trong KB
    existing_doc = session.exec(
        select(KnowledgeBaseDocument).where(
            KnowledgeBaseDocument.kb_id == kb_id,
            KnowledgeBaseDocument.file_name == file.filename
        )
    ).first()
    if existing_doc:
        raise HTTPException(status_code=400, detail=f"Văn bản '{file.filename}' đã tồn tại trong Knowledge Base này.")

    file_extension = os.path.splitext(file.filename)[1]

    embedding_model = get_embedding_model()
    vector_size = len(embedding_model.embed_query("hello world"))

    # 2. Tạo bản ghi ban đầu với trạng thái processing
    new_doc = KnowledgeBaseDocument(
        kb_id=kb_id,
        file_name=file.filename,
        file_type=file_extension.replace('.', ''),
        vector_size=vector_size,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        retrieval_top_k=5,
        parsing_status=ParsingStatus.processing,
        error_message=None,
        chunk_count=0,
        uploaded_by=admin_id,
        upload_at=datetime.now(timezone.utc)
    )
    
    session.add(new_doc)
    session.commit()
    session.refresh(new_doc)

    try:
        # 3. Extract & Split
        documents = _extract_documents_from_upload_file(file)
        split_docs = _split_documents(documents, chunk_size, chunk_overlap)
        
        # 4. Cập nhật metadata cho chunk
        for i, chunk in enumerate(split_docs):
            chunk.metadata.update({
                "document_id": str(new_doc.document_id),
                "kb_id": str(kb_id),
                "file_name": new_doc.file_name,
                "file_type": new_doc.file_type,
                "chunk_index": i
            })

        # 5. Khởi tạo DB nếu cần và lưu Vectors
        init_and_store_vectors(session, kb.table_name, split_docs)

        # 6. Cập nhật trạng thái thành công
        new_doc.chunk_count = len(split_docs)
        new_doc.parsing_status = ParsingStatus.success
        new_doc.error_message = None
        session.add(new_doc)
        session.commit()
        
        # 7. Update document_count cho KB (chỉ đếm file success)
        success_count = session.exec(
            select(func.count(KnowledgeBaseDocument.document_id))
            .where(KnowledgeBaseDocument.kb_id == kb_id)
            .where(KnowledgeBaseDocument.parsing_status == ParsingStatus.success)
        ).one()
        
        kb.document_count = success_count
        kb.updated_at = datetime.now(timezone.utc)
        session.add(kb)
        
        session.commit()
        session.refresh(new_doc)
        
    except Exception as e:
        tb = traceback.format_exc()
        logger.error("Upload document failed for kb_id=%s file=%s\n%s", kb_id, file.filename, tb)
        new_doc.parsing_status = ParsingStatus.failed
        new_doc.error_message = f"{type(e).__name__}: {e}"
        session.add(new_doc)
        session.commit()
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")
    
    return {
        "document_id": str(new_doc.document_id),
        "kb_id": str(new_doc.kb_id),
        "file_name": new_doc.file_name,
        "parsing_status": new_doc.parsing_status,
        "chunk_count": new_doc.chunk_count,
        "upload_date": new_doc.upload_at,
    }
