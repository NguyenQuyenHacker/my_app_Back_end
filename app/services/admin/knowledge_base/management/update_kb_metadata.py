from fastapi import HTTPException
from sqlmodel import Session
from uuid import UUID
from datetime import datetime, timezone
from typing import Optional

from app.models.knowledge_bases_model import KnowledgeBase
from app.schemas.admin.knowledge_bases_schema import KnowledgeBaseUpdate

def update_kb_metadata_service(session: Session, kb_id: UUID, payload: KnowledgeBaseUpdate):
    kb = session.get(KnowledgeBase, kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge Base not found")
        
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(kb, key, value)
        
    kb.updated_at = datetime.now(timezone.utc)
    
    session.add(kb)
    session.commit()
    session.refresh(kb)
    
    return kb
