# src/presentation/http/routers/documents.py
import os
import hashlib
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from src.infrastructure.db.init_db import get_db
from src.infrastructure.db.models.document import Document
from src.infrastructure.db.models.user import User
from src.presentation.http.dependencies.auth import get_current_user

router = APIRouter(prefix="/documents", tags=["documents"])

# Настройки загрузки
UPLOAD_DIR = "uploads/documents"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {
    'image': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'],
    'document': ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt'],
    'archive': ['zip', 'rar', '7z'],
}

os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    document_type: str = "other",
    category: str = "asset",
    title: Optional[str] = None,
    description: Optional[str] = None,
    is_primary: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Загружает документ.
    """
    # Проверяем размер
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max size: {MAX_FILE_SIZE // (1024 * 1024)} MB"
        )

    # Проверяем расширение
    filename = file.filename or "unknown"
    extension = filename.split('.')[-1].lower() if '.' in filename else ''
    
    if extension not in [ext for exts in ALLOWED_EXTENSIONS.values() for ext in exts]:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed: {', '.join([ext for exts in ALLOWED_EXTENSIONS.values() for ext in exts])}"
        )

    # Определяем mime_type
    mime_type = file.content_type or _guess_mime_type(extension)

    # Генерируем уникальное имя файла
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    # Сохраняем файл
    with open(file_path, "wb") as f:
        f.write(content)

    # Вычисляем хеш файла
    file_hash = hashlib.md5(content).hexdigest()

    # Создаем запись в БД
    document = Document(
        filename=filename,
        file_path=file_path,
        file_size=len(content),
        mime_type=mime_type,
        document_type=document_type,
        category=category,
        entity_id=entity_id,
        entity_type=entity_type,
        title=title or filename,
        description=description,
        uploaded_by=current_user.id,
        uploaded_at=datetime.now(),
        is_primary=is_primary,
        file_hash=file_hash,
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return {
        "id": document.id,
        "filename": document.filename,
        "file_path": document.file_path,
        "file_size": document.file_size,
        "mime_type": document.mime_type,
        "document_type": document.document_type,
        "category": document.category,
        "entity_id": document.entity_id,
        "entity_type": document.entity_type,
        "title": document.title,
        "description": document.description,
        "is_primary": document.is_primary,
        "uploaded_at": document.uploaded_at,
    }


@router.get("/")
def list_documents(
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    category: Optional[str] = None,
    document_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Список документов с фильтрацией.
    """
    query = db.query(Document)

    if entity_type and entity_id is not None:
        query = query.filter(
            Document.entity_type == entity_type,
            Document.entity_id == entity_id
        )

    if category:
        query = query.filter(Document.category == category)

    if document_type:
        query = query.filter(Document.document_type == document_type)

    documents = query.offset(skip).limit(limit).all()
    total = query.count()

    return {
        "items": [
            {
                "id": d.id,
                "filename": d.filename,
                "file_path": d.file_path,
                "file_size": d.file_size,
                "mime_type": d.mime_type,
                "document_type": d.document_type,
                "category": d.category,
                "entity_id": d.entity_id,
                "entity_type": d.entity_type,
                "title": d.title,
                "description": d.description,
                "is_primary": d.is_primary,
                "uploaded_at": d.uploaded_at,
            }
            for d in documents
        ],
        "total": total,
    }


@router.get("/{document_id}")
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Получает документ по ID.
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {
        "id": document.id,
        "filename": document.filename,
        "file_path": document.file_path,
        "file_size": document.file_size,
        "mime_type": document.mime_type,
        "document_type": document.document_type,
        "category": document.category,
        "entity_id": document.entity_id,
        "entity_type": document.entity_type,
        "title": document.title,
        "description": document.description,
        "is_primary": document.is_primary,
        "uploaded_at": document.uploaded_at,
    }


@router.get("/{document_id}/download")
async def download_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Скачивает файл документа.
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Получаем значения атрибутов
    file_path = document.file_path
    filename = document.filename
    mime_type = document.mime_type

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on server")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=mime_type,
    )


@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Удаляет документ.
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    file_path = document.file_path
    
    # Удаляем файл с диска
    if os.path.exists(file_path):
        os.remove(file_path)

    db.delete(document)
    db.commit()

    return {"message": "Document deleted"}


def _guess_mime_type(extension: str) -> str:
    """Определяет mime-type по расширению"""
    mime_types = {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'webp': 'image/webp',
        'pdf': 'application/pdf',
        'doc': 'application/msword',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'xls': 'application/vnd.ms-excel',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'txt': 'text/plain',
        'zip': 'application/zip',
        'rar': 'application/x-rar-compressed',
    }
    return mime_types.get(extension, 'application/octet-stream')