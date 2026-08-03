import os
import hashlib
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from src.infrastructure.db.init_db import get_db
from src.infrastructure.db.models.asset_photo import AssetPhoto as AssetPhotoModel
from src.infrastructure.db.models.document import Document
from src.infrastructure.db.models.asset import Asset
from src.infrastructure.db.models.user import User
from src.presentation.http.dependencies.auth import get_current_user

router = APIRouter(prefix="/asset-photos", tags=["asset-photos"])

# Настройки загрузки
UPLOAD_DIR = "uploads/asset_photos"
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB
ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'}

os.makedirs(UPLOAD_DIR, exist_ok=True)


def _guess_mime_type(extension: str) -> str:
    """Определяет mime-type по расширению"""
    mime_types = {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'webp': 'image/webp',
        'bmp': 'image/bmp',
    }
    return mime_types.get(extension, 'application/octet-stream')


@router.post("/{asset_id}/upload")
async def upload_asset_photo(
    asset_id: int,
    file: UploadFile = File(...),
    stage: str = "other",
    photo_category: Optional[str] = None,
    description: Optional[str] = None,
    is_before: bool = False,
    is_after: bool = False,
    sort_order: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Загружает фотографию для актива.
    """
    # Проверяем существование актива
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

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
    
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed image types: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}"
        )

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

    # Создаем запись документа
    document = Document(
        filename=filename,
        file_path=file_path,
        file_size=len(content),
        mime_type=mime_type,
        document_type="photo",
        category="asset_photo",
        entity_id=asset_id,
        entity_type="asset",
        title=description or filename,
        description=description,
        uploaded_by=current_user.id,
        uploaded_at=datetime.now(),
        is_primary=False,
        sort_order=sort_order,
        file_hash=file_hash,
    )
    db.add(document)
    db.flush()

    # Создаем запись фотографии
    photo = AssetPhotoModel(
        asset_id=asset_id,
        document_id=document.id,
        uploaded_by=current_user.id,
        stage=stage,
        photo_category=photo_category,
        description=description,
        uploaded_at=datetime.now(),
        is_before=is_before,
        is_after=is_after,
        sort_order=sort_order,
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)
    db.refresh(document)

    return {
        "id": photo.id,
        "asset_id": photo.asset_id,
        "document_id": photo.document_id,
        "uploaded_by": photo.uploaded_by,
        "stage": photo.stage,
        "photo_category": photo.photo_category,
        "description": photo.description,
        "is_before": photo.is_before,
        "is_after": photo.is_after,
        "sort_order": photo.sort_order,
        "uploaded_at": photo.uploaded_at.isoformat(),
        "filename": document.filename,
        "file_size": document.file_size,
        "mime_type": document.mime_type,
    }


@router.get("/")
def list_asset_photos(
    asset_id: Optional[int] = Query(None),
    stage: Optional[str] = Query(None),
    photo_category: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Список фотографий с фильтрацией.
    """
    query = db.query(AssetPhotoModel).join(Document, AssetPhotoModel.document_id == Document.id)

    if asset_id is not None:
        query = query.filter(AssetPhotoModel.asset_id == asset_id)
    if stage:
        query = query.filter(AssetPhotoModel.stage == stage)
    if photo_category:
        query = query.filter(AssetPhotoModel.photo_category == photo_category)

    query = query.order_by(AssetPhotoModel.sort_order, AssetPhotoModel.uploaded_at.desc())
    total = query.count()
    photos = query.offset(skip).limit(limit).all()

    items = []
    for photo in photos:
        doc = db.query(Document).filter(Document.id == photo.document_id).first()
        items.append({
            "id": photo.id,
            "asset_id": photo.asset_id,
            "document_id": photo.document_id,
            "uploaded_by": photo.uploaded_by,
            "stage": photo.stage,
            "photo_category": photo.photo_category,
            "description": photo.description,
            "is_before": photo.is_before,
            "is_after": photo.is_after,
            "sort_order": photo.sort_order,
            "uploaded_at": photo.uploaded_at.isoformat() if photo.uploaded_at else None,
            "filename": doc.filename if doc else None,
            "file_size": doc.file_size if doc else None,
            "mime_type": doc.mime_type if doc else None,
        })

    return {"items": items, "total": total}


@router.get("/{photo_id}")
def get_asset_photo(
    photo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Получает информацию о фотографии.
    """
    photo = db.query(AssetPhotoModel).filter(AssetPhotoModel.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    doc = db.query(Document).filter(Document.id == photo.document_id).first()

    return {
        "id": photo.id,
        "asset_id": photo.asset_id,
        "document_id": photo.document_id,
        "uploaded_by": photo.uploaded_by,
        "stage": photo.stage,
        "photo_category": photo.photo_category,
        "description": photo.description,
        "is_before": photo.is_before,
        "is_after": photo.is_after,
        "sort_order": photo.sort_order,
        "uploaded_at": photo.uploaded_at.isoformat() if photo.uploaded_at else None,
        "filename": doc.filename if doc else None,
        "file_size": doc.file_size if doc else None,
        "mime_type": doc.mime_type if doc else None,
    }


@router.get("/{photo_id}/download")
async def download_asset_photo(
    photo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Скачивает/просматривает файл фотографии.
    """
    photo = db.query(AssetPhotoModel).filter(AssetPhotoModel.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    doc = db.query(Document).filter(Document.id == photo.document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="File not found on server")

    return FileResponse(
        path=doc.file_path,
        filename=doc.filename,
        media_type=doc.mime_type,
    )


@router.delete("/{photo_id}")
def delete_asset_photo(
    photo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Удаляет фотографию актива (запись в БД и файл).
    """
    photo = db.query(AssetPhotoModel).filter(AssetPhotoModel.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    doc = db.query(Document).filter(Document.id == photo.document_id).first()

    # Удаляем файл с диска
    if doc and os.path.exists(doc.file_path):
        os.remove(doc.file_path)

    # Удаляем записи из БД
    if doc:
        db.delete(doc)
    db.delete(photo)
    db.commit()

    return {"message": "Photo deleted successfully"}
