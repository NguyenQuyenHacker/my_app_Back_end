from sqlmodel import Session, select
from datetime import datetime, timezone
from uuid import UUID
from app.models.knowledge_bases_model import KnowledgeBaseConfig

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
