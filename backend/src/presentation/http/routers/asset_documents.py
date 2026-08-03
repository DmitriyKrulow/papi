# backend/src/presentation/http/routers/asset_documents.py
import os
import hashlib
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload

from src.infrastructure.db.init_db import get_db
from src.infrastructure.db.models.document import Document
from src.infrastructure.db.models.document_link import DocumentLink
from src.infrastructure.db.models.asset import Asset
from src.infrastructure.db.models.user import User
from src.presentation.http.dependencies.auth import get_current_user

router = APIRouter(prefix="/asset-documents", tags=["asset-documents"])

UPLOAD_DIR = "uploads/documents"
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_EXTENSIONS = {
    'image': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'],
    'document': ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt', 'rtf', 'odt'],
    'archive': ['zip', 'rar', '7z'],
}

os.makedirs(UPLOAD_DIR, exist_ok=True)


def _guess_mime_type(extension: str) -> str:
    mime_types = {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'webp': 'image/webp',
        'bmp': 'image/bmp',
        'pdf': 'application/pdf',
        'doc': 'application/msword',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'xls': 'application/vnd.ms-excel',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'txt': 'text/plain',
        'rtf': 'application/rtf',
        'odt': 'application/vnd.oasis.opendocument.text',
        'zip': 'application/zip',
        'rar': 'application/x-rar-compressed',
        '7z': 'application/x-7z-compressed',
    }
    return mime_types.get(extension, 'application/octet-stream')


@router.post("/upload")
async def upload_and_link_document(
    file: UploadFile = File(...),
    asset_ids: str = Query(..., description="JSON-массив ID активов, например [1,2,3]"),
    document_type: str = Query("other", description="Тип документа: order, invoice, receipt, other"),
    title: Optional[str] = Query(None),
    description: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Загружает документ и привязывает его к одному или нескольким активам.
    """
    # Парсим asset_ids
    try:
        import json
        asset_id_list = json.loads(asset_ids)
        if not isinstance(asset_id_list, list) or len(asset_id_list) == 0:
            raise ValueError
        asset_id_list = [int(aid) for aid in asset_id_list]
    except (json.JSONDecodeError, ValueError, TypeError):
        raise HTTPException(status_code=400, detail="asset_ids должен быть JSON-массивом ID активов, например [1,2,3]")

    # Проверяем существование всех активов
    existing_assets = db.query(Asset).filter(Asset.id.in_(asset_id_list)).all()
    existing_ids = {a.id for a in existing_assets}
    missing_ids = [aid for aid in asset_id_list if aid not in existing_ids]
    if missing_ids:
        raise HTTPException(status_code=404, detail=f"Активы с ID {missing_ids} не найдены")

    # Проверяем размер
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Файл слишком большой. Максимальный размер: {MAX_FILE_SIZE // (1024 * 1024)} MB"
        )

    # Проверяем расширение
    filename = file.filename or "unknown"
    extension = filename.split('.')[-1].lower() if '.' in filename else ''
    
    allowed_exts = [ext for exts in ALLOWED_EXTENSIONS.values() for ext in exts]
    if extension not in allowed_exts:
        raise HTTPException(
            status_code=400,
            detail=f"Тип файла не разрешён. Разрешённые: {', '.join(allowed_exts)}"
        )

    mime_type = file.content_type or _guess_mime_type(extension)

    # Генерируем уникальное имя файла
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    # Сохраняем файл
    with open(file_path, "wb") as f:
        f.write(content)

    # Вычисляем хеш
    file_hash = hashlib.md5(content).hexdigest()

    # Создаём запись документа
    document = Document(
        filename=filename,
        file_path=file_path,
        file_size=len(content),
        mime_type=mime_type,
        document_type=document_type,
        category="asset",
        title=title or filename,
        description=description,
        uploaded_by=current_user.id,
        uploaded_at=datetime.now(),
        is_primary=False,
        sort_order=0,
        file_hash=file_hash,
    )
    db.add(document)
    db.flush()

    # Привязываем ко всем указанным активам
    for asset_id in asset_id_list:
        # Проверяем, не существует ли уже такая связь
        existing_link = db.query(DocumentLink).filter(
            DocumentLink.document_id == document.id,
            DocumentLink.asset_id == asset_id,
        ).first()
        if not existing_link:
            link = DocumentLink(
                document_id=document.id,
                asset_id=asset_id,
                linked_at=datetime.now(),
            )
            db.add(link)

    db.commit()
    db.refresh(document)

    return {
        "id": document.id,
        "filename": document.filename,
        "file_size": document.file_size,
        "mime_type": document.mime_type,
        "document_type": document.document_type,
        "title": document.title,
        "description": document.description,
        "uploaded_at": document.uploaded_at.isoformat(),
        "uploaded_by": document.uploaded_by,
        "linked_asset_ids": asset_id_list,
    }


@router.get("/")
def list_asset_documents(
    asset_id: Optional[int] = Query(None),
    document_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Список документов с фильтрацией по активу, типу, поиску.
    """
    query = db.query(Document).distinct()

    # Если указан asset_id — фильтруем через DocumentLink
    if asset_id is not None:
        query = query.join(DocumentLink, Document.id == DocumentLink.document_id).filter(
            DocumentLink.asset_id == asset_id
        )

    if document_type:
        query = query.filter(Document.document_type == document_type)

    if search:
        like_pattern = f"%{search}%"
        query = query.filter(
            Document.filename.ilike(like_pattern) |
            Document.title.ilike(like_pattern) |
            Document.description.ilike(like_pattern)
        )

    query = query.order_by(Document.uploaded_at.desc())
    total = query.count()
    documents = query.offset(skip).limit(limit).all()

    items = []
    for doc in documents:
        # Получаем список ID активов, к которым привязан документ
        links = db.query(DocumentLink).filter(DocumentLink.document_id == doc.id).all()
        linked_asset_ids = [link.asset_id for link in links]
        link_count = len(links)

        items.append({
            "id": doc.id,
            "filename": doc.filename,
            "file_path": doc.file_path,
            "file_size": doc.file_size,
            "mime_type": doc.mime_type,
            "document_type": doc.document_type,
            "category": doc.category,
            "title": doc.title,
            "description": doc.description,
            "uploaded_by": doc.uploaded_by,
            "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
            "linked_asset_ids": linked_asset_ids,
            "link_count": link_count,
        })

    return {"items": items, "total": total}


@router.get("/{document_id}")
def get_asset_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Получает информацию о документе.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    links = db.query(DocumentLink).filter(DocumentLink.document_id == doc.id).all()
    linked_asset_ids = [link.asset_id for link in links]

    return {
        "id": doc.id,
        "filename": doc.filename,
        "file_path": doc.file_path,
        "file_size": doc.file_size,
        "mime_type": doc.mime_type,
        "document_type": doc.document_type,
        "category": doc.category,
        "title": doc.title,
        "description": doc.description,
        "uploaded_by": doc.uploaded_by,
        "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
        "linked_asset_ids": linked_asset_ids,
        "link_count": len(links),
    }


@router.get("/{document_id}/download")
async def download_asset_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Скачивает/просматривает файл документа.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="File not found on server")

    return FileResponse(
        path=doc.file_path,
        filename=doc.filename,
        media_type=doc.mime_type,
    )


@router.delete("/{document_id}/unlink")
def unlink_document_from_assets(
    document_id: int,
    asset_ids: Optional[str] = Query(None, description="JSON-массив ID активов, от которых отвязать документ. Если не указан — отвязывается от всех"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Отвязывает документ от указанных активов (или от всех, если asset_ids не указан).
    Если после отвязки не осталось ссылок — документ и файл удаляются.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Парсим asset_ids
    if asset_ids:
        try:
            import json
            asset_id_list = json.loads(asset_ids)
            if not isinstance(asset_id_list, list):
                raise ValueError
            asset_id_list = [int(aid) for aid in asset_id_list]
        except (json.JSONDecodeError, ValueError, TypeError):
            raise HTTPException(status_code=400, detail="asset_ids должен быть JSON-массивом ID активов")
    else:
        asset_id_list = None

    # Удаляем связи
    query = db.query(DocumentLink).filter(DocumentLink.document_id == document_id)
    if asset_id_list:
        query = query.filter(DocumentLink.asset_id.in_(asset_id_list))
    deleted_count = query.delete(synchronize_session=False)
    db.commit()

    # Проверяем, остались ли ещё ссылки
    remaining_links = db.query(DocumentLink).filter(
        DocumentLink.document_id == document_id
    ).count()

    file_deleted = False
    if remaining_links == 0:
        # Нет больше ссылок — удаляем документ и файл
        if os.path.exists(doc.file_path):
            os.remove(doc.file_path)
            file_deleted = True
        db.delete(doc)
        db.commit()
        return {
            "message": "Document fully deleted (no more references)",
            "unlinked_from_count": deleted_count,
            "file_deleted": file_deleted,
            "document_deleted": True,
        }

    return {
        "message": f"Document unlinked from {deleted_count} asset(s)",
        "remaining_links": remaining_links,
        "file_deleted": False,
        "document_deleted": False,
    }


@router.delete("/{document_id}")
def delete_asset_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Полностью удаляет документ и все его связи.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Удаляем все связи
    db.query(DocumentLink).filter(DocumentLink.document_id == document_id).delete()

    # Удаляем файл
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)

    db.delete(doc)
    db.commit()

    return {"message": "Document and all its links deleted successfully"}