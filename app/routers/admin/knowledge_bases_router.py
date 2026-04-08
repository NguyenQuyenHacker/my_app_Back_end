from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from uuid import UUID
from app.db.database import get_session_admin
from app.schemas.admin.knowledge_bases_schema import (
    KnowledgeBaseRead, 
    KnowledgeBaseConfigUpdate, 
    KnowledgeBaseDocumentRead,
    KnowledgeBaseCreate
)
from app.services.admin.knowledge_bases_service import (
    get_all_knowledge_bases, 
    get_documents_by_kb_id_service, 
    update_kb_config_service,
    create_knowledge_base_service
)
from app.services.admin.knowledge_bases_rag_service import upload_document_to_kb_service
from fastapi import UploadFile, File, Form
from app.core.dependencies import get_current_admin
from app.models.admin_model import Admin
router = APIRouter(
    prefix="/admin/knowledge-bases",
    tags=["Admin Knowledge Bases"],
)


@router.get("", response_model=list[KnowledgeBaseRead])
def read_knowledge_bases(
    session: Session = Depends(get_session_admin),
):
    try:
        return get_all_knowledge_bases(session=session)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("", response_model=dict)
def create_new_knowledge_base(
    payload: KnowledgeBaseCreate,
    session: Session = Depends(get_session_admin),
    current_admin: Admin = Depends(get_current_admin),
):
    try:
        new_kb = create_knowledge_base_service(
            session=session,
            data=payload,
            admin_id=current_admin.admin_id
        )
        
        return {
            "message": "Tạo Knowledge Base thành công",
            "data": {
                "kb_id": str(new_kb.kb_id),
                "name": new_kb.name,
                "table_name": new_kb.table_name
            }
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")


@router.get("/{kb_id}/documents", response_model=list[KnowledgeBaseDocumentRead])
def get_documents_by_kb_id(
    kb_id: UUID,
    session: Session = Depends(get_session_admin),
):
    documents = get_documents_by_kb_id_service(session, kb_id)

    if documents is None:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    return documents

@router.patch("/{kb_id}/config", response_model=dict)
def update_kb_config(
    kb_id: UUID,
    config_update: KnowledgeBaseConfigUpdate,
    session: Session = Depends(get_session_admin),
    current_admin: Admin = Depends(get_current_admin),
):
    # Kiểm tra ràng buộc logic: overlap < size
    if config_update.chunk_overlap >= config_update.chunk_size:
        raise HTTPException(
            status_code=400,
            detail="chunk_overlap must be less than chunk_size"
        )
        
    config = update_kb_config_service(
        session,
        kb_id,
        config_update.model_dump()
    )
        
    return {
        "message": "Cập nhật cấu hình thành công",
        "data": {
            "config_id": config.config_id,
            "kb_id": config.kb_id,
            "chunk_size": config.chunk_size,
            "chunk_overlap": config.chunk_overlap,
            "updated_at": config.updated_at
        }
    }


def validate_upload_document_input(file: UploadFile, chunk_size: int, chunk_overlap: int) -> None:
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File name is required.",
        )

    allowed_extensions = {".pdf", ".doc", ".docx"}
    file_name_lower = file.filename.lower()

    if not any(file_name_lower.endswith(ext) for ext in allowed_extensions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only {', '.join(allowed_extensions)} files are supported.",
        )

    if not 300 <= chunk_size <= 2000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="chunk_size must be between 300 and 2000.",
        )

    if not 0 <= chunk_overlap <= 400:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="chunk_overlap must be between 0 and 400.",
        )

    if chunk_overlap >= chunk_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="chunk_overlap must be smaller than chunk_size.",
        )

@router.post("/{kb_id}/documents/upload")
def upload_document_to_kb(
    kb_id: UUID,
    session: Session = Depends(get_session_admin),
    current_admin: Admin = Depends(get_current_admin),
    file: UploadFile = File(...),
    chunk_size: int = Form(...),
    chunk_overlap: int = Form(...),
):
    # Validate input
    validate_upload_document_input(file, chunk_size, chunk_overlap)
    
    # Gọi service xử lý
    new_doc_data = upload_document_to_kb_service(
        session=session,
        kb_id=kb_id,
        file=file,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        admin_id=current_admin.admin_id
    )
    
    return {
        "message": "Upload document successfully.",
        "data": new_doc_data
    }



    