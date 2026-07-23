from datetime import datetime
from pathlib import Path
from typing import List, Optional
import uuid
import os

from fastapi import APIRouter, HTTPException, status, UploadFile, Form, Request
from pydantic import BaseModel

from backend.src.core.entities.document import DocumentType, DocumentCategory

router = APIRouter()

BASE_DIR = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
UPLOAD_DIR = BASE_DIR / "uploads" / "documents"


class DocumentCreateRequest(BaseModel):
    document_type: Optional[str] = "other"
    category: Optional[str] = "asset"
    entity_id: Optional[int] = None
    entity_type: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    is_primary: Optional[bool] = False
    sort_order: Optional[int] = 0


class DocumentResponse(BaseModel):
    id: int
    filename: str
    file_path: str
    file_size: int
    mime_type: str
    uploaded_by: int
    document_type: str
    category: str
    entity_id: Optional[int]
    entity_type: Optional[str]
    title: Optional[str]
    description: Optional[str]
    uploaded_at: datetime
    is_primary: bool
    sort_order: int
    file_hash: Optional[str]


documents_db: dict = {}
document_id_counter = 1


@router.get("/", response_model=List[DocumentResponse], status_code=status.HTTP_200_OK)
async def get_documents():
    return list(documents_db.values())


@router.get("/{document_id}", response_model=DocumentResponse, status_code=status.HTTP_200_OK)
async def get_document(document_id: int):
    if document_id not in documents_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return documents_db[document_id]


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile,
    request: Request,
    document_type: Optional[str] = Form("other"),
    category: Optional[str] = Form("asset"),
    entity_id: Optional[int] = Form(None),
    entity_type: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    is_primary: Optional[bool] = Form(False),
    sort_order: Optional[int] = Form(0),
):
    global document_id_counter
    
    allowed_types = [
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/gif",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ]
    
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: Excel, PDF, Images, Word documents. Got: {file.content_type or 'None'}",
        )
    
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    file_id = uuid.uuid4().hex
    file_extension = Path(file.filename).suffix
    filename = f"{file_id}{file_extension}"
    
    file_path = UPLOAD_DIR / filename
    
    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)
    
    try:
        dt = DocumentType(document_type)
    except ValueError:
        dt = DocumentType.OTHER
    
    try:
        dc = DocumentCategory(category)
    except ValueError:
        dc = DocumentCategory.ASSET
    
    document = DocumentResponse(
        id=document_id_counter,
        filename=file.filename,
        file_path=str(file_path),
        file_size=len(contents),
        mime_type=file.content_type,
        uploaded_by=1,
        document_type=dt.value,
        category=dc.value,
        entity_id=entity_id,
        entity_type=entity_type,
        title=title,
        description=description,
        uploaded_at=datetime.now(),
        is_primary=is_primary,
        sort_order=sort_order,
        file_hash=None,
    )
    
    documents_db[document_id_counter] = document
    document_id_counter += 1
    
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: int):
    if document_id not in documents_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    
    del documents_db[document_id]
    return None
