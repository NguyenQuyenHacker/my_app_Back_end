# app/services/admin/knowledge_bases_rag_service.py
from sqlmodel import Session, select, func
from app.models.knowledge_bases_model import KnowledgeBase, KnowledgeBaseDocument, ParsingStatus
from uuid import UUID
from datetime import datetime, timezone
import os
import shutil
import tempfile
from fastapi import HTTPException, UploadFile
from app.db.database import DATABASE_URL_ADMIN

from langchain_community.document_loaders import UnstructuredPDFLoader, UnstructuredWordDocumentLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_postgres import PGEngine, PGVectorStore
from sqlalchemy import inspect
from app.utils.embedding_utils import get_embedding_model

def _extract_documents_from_upload_file(file: UploadFile):
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    # Lưu tạm file upload để loader có thể đọc
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
        shutil.copyfileobj(file.file, temp_file)
        temp_file_path = temp_file.name

    try:
        # Load tùy extension
        if file_extension == ".pdf":
            loader = UnstructuredPDFLoader(temp_file_path)
        elif file_extension in [".doc", ".docx"]:
            loader = UnstructuredWordDocumentLoader(temp_file_path)
        else:
            raise ValueError(f"Unsupported file extension: {file_extension}")
        
        documents = loader.load()
        return documents
    finally:
        # Luôn xóa file tạm
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


def _split_documents(documents, chunk_size: int, chunk_overlap: int):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    return text_splitter.split_documents(documents)



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
    
    # 2. Tạo bản ghi ban đầu với trạng thái processing
    new_doc = KnowledgeBaseDocument(
        kb_id=kb_id,
        file_name=file.filename,
        file_type=file_extension.replace('.', ''),
        vector_size=1536,
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
        
        # 4.5 Cập nhật metadata cho chunk
        for i, chunk in enumerate(split_docs):
            chunk.metadata.update({
                "document_id": str(new_doc.document_id),
                "kb_id": str(kb_id),
                "file_name": new_doc.file_name,
                "file_type": new_doc.file_type,
                "chunk_index": i
            })

        # Khởi tạo embedding và connection    
            
        embedding_model = get_embedding_model()
        engine = PGEngine.from_connection_string(url=DATABASE_URL_ADMIN)
        vector_size = len(embedding_model.embed_query("hello world"))
        table_name = kb.table_name

        # Kiểm tra bảng đã tồn tại chưa bằng chính session hiện có (Clean & SQLModel style)
        if not inspect(session.bind).has_table(table_name):
            # Nếu chưa có thì dùng lệnh khởi tạo qua PGEngine
            pg_engine = PGEngine.from_connection_string(url=DATABASE_URL_ADMIN)
            pg_engine.init_vectorstore_table(
                table_name=table_name,
                vector_size=vector_size,
            )

        # Khởi tạo Vector Store
        pg_engine = PGEngine.from_connection_string(url=DATABASE_URL_ADMIN)
        vector_store = PGVectorStore.create_sync(
            engine=pg_engine,
            table_name=table_name,
            embedding_service=embedding_model,
        )

        vector_store.add_documents(split_docs)

        # 5. Cập nhật thành công
        new_doc.chunk_count = len(split_docs)
        new_doc.parsing_status = ParsingStatus.success
        new_doc.error_message = None
        session.add(new_doc)
        session.commit()
        
        # 6. Update document_count cho KB (chỉ đếm file success)
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
        # 6. Ghi nhận lỗi
        new_doc.parsing_status = ParsingStatus.failed
        new_doc.error_message = str(e)
        session.add(new_doc)
        session.commit()
        raise HTTPException(status_code=500, detail=str(e))
    
    return {
        "document_id": str(new_doc.document_id),
        "kb_id": str(new_doc.kb_id),
        "file_name": new_doc.file_name,
        "parsing_status": new_doc.parsing_status,
        "chunk_count": new_doc.chunk_count,
        "upload_date": new_doc.upload_at,
    }
