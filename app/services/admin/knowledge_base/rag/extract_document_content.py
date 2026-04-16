import os
import shutil
import tempfile
from fastapi import UploadFile
from langchain_community.document_loaders import UnstructuredPDFLoader, UnstructuredWordDocumentLoader

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
