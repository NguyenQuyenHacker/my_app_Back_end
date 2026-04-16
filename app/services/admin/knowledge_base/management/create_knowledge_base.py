from sqlmodel import Session, select
from fastapi import HTTPException, status
from datetime import datetime, timezone
from uuid import UUID
from app.models.knowledge_bases_model import KnowledgeBase, KnowledgeBaseConfig
from app.schemas.admin.knowledge_bases_schema import KnowledgeBaseCreate

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
