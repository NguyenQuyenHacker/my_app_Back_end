from sqlmodel import Session, select
from app.models.knowledge_bases_model import KnowledgeBase, KnowledgeBaseDocument, KnowledgeBaseConfig, ParsingStatus
from app.schemas.admin.knowledge_bases_schema import KnowledgeBaseCreate
from app.models.admin_model import Admin
from uuid import UUID
from datetime import datetime, timezone
from pathlib import Path
from fastapi import HTTPException, status


def get_all_knowledge_bases(session):
    statement = (
        select(
            KnowledgeBase.kb_id,
            KnowledgeBase.name,
            KnowledgeBase.description,
            KnowledgeBase.table_name,
            KnowledgeBase.document_count,
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
        }
        for row in rows
    ]


# Trigger reload uvicorn


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

def update_kb_config_service(session: Session, kb_id: UUID, data: dict):
    # Tìm config theo kb_id
    statement = select(KnowledgeBaseConfig).where(KnowledgeBaseConfig.kb_id == kb_id)
    config = session.exec(statement).first()
    
    chunk_size = data.get("chunk_size")
    chunk_overlap = data.get("chunk_overlap")

    if not config:
        # Nếu chưa có thì khởi tạo mới (Upsert)
        config = KnowledgeBaseConfig(
            kb_id=kb_id,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            updated_at=datetime.now(timezone.utc)
        )
    else:
        # Nếu đã có thì cập nhật thông tin
        config.chunk_size = chunk_size
        config.chunk_overlap = chunk_overlap
        config.updated_at = datetime.now(timezone.utc)
    
    session.add(config)
    session.commit()
    session.refresh(config)
    
    return config


def create_knowledge_base_service(session: Session, data: KnowledgeBaseCreate, admin_id: UUID):
    # 1. Kiểm tra table_name đã tồn tại chưa
    statement = select(KnowledgeBase).where(KnowledgeBase.table_name == data.table_name)
    existing_kb = session.exec(statement).first()
    if existing_kb:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Table name '{data.table_name}' đã tồn tại. Vui lòng chọn tên khác."
        )

    # 2. Tạo Knowledge Base mới
    new_kb = KnowledgeBase(
        name=data.name,
        description=data.description,
        table_name=data.table_name,
        created_by=admin_id,
        document_count=0,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    session.add(new_kb)
    session.flush() # Để lấy được kb_id cho bước sau

    # 3. Tạo cấu hình mặc định (chunking settings)
    new_config = KnowledgeBaseConfig(
        kb_id=new_kb.kb_id,
        chunk_size=1000,
        chunk_overlap=150,
        updated_at=datetime.now(timezone.utc)
    )
    session.add(new_config)
    
    # 4. Lưu tất cả vào DB
    session.commit()
    session.refresh(new_kb)
    
    return new_kb



