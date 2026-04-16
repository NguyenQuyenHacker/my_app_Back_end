from fastapi import HTTPException
from sqlmodel import Session
from uuid import UUID
from datetime import datetime, timezone

from app.models.knowledge_bases_model import KnowledgeBase

def toggle_kb_status_service(session: Session, kb_id: UUID, is_active: bool):
    kb = session.get(KnowledgeBase, kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge Base not found")
        
    kb.is_active = is_active
    kb.updated_at = datetime.now(timezone.utc)
    
    session.add(kb)
    session.commit()
    session.refresh(kb)
    
    return kb
