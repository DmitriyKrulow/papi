# src/presentation/http/routers/asset_photos.py
from fastapi import APIRouter, HTTPException, status, UploadFile, Form
from typing import Optional
from datetime import datetime

from backend.src.presentation.http.schemas.asset_photos import (
    AssetPhotoCreate,
    AssetPhotoResponse,
    AssetPhotoListResponse,
)

router = APIRouter()


asset_photos_db: dict = {}
asset_photo_id_counter = 1


@router.get("/", response_model=AssetPhotoListResponse, status_code=status.HTTP_200_OK)
async def get_asset_photos():
    return AssetPhotoListResponse(total=len(asset_photos_db), items=list(asset_photos_db.values()))


@router.get("/asset-photos/{photo_id}", response_model=AssetPhotoResponse, status_code=status.HTTP_200_OK)
async def get_asset_photo(photo_id: int):
    if photo_id not in asset_photos_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
    return asset_photos_db[photo_id]


@router.post("/asset-photos/{asset_id}/upload", response_model=AssetPhotoResponse, status_code=status.HTTP_201_CREATED)
async def add_asset_photo(
    asset_id: int,
    file: UploadFile,
    stage: Optional[str] = Form("other"),
    description: Optional[str] = Form(None),
    taken_at: Optional[str] = Form(None),
    taken_by: Optional[int] = Form(None),
    inventory_check_id: Optional[int] = Form(None),
    repair_request_id: Optional[int] = Form(None),
    is_before: Optional[bool] = Form(False),
    is_after: Optional[bool] = Form(False),
    sort_order: Optional[int] = Form(0),
):
    global asset_photo_id_counter
    
    allowed_types = [
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ]
    
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: Excel, PDF, Images, Word documents. Got: {file.content_type or 'None'}",
        )
    
    from pathlib import Path
    import uuid
    import os
    
    upload_dir = Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))) / "uploads" / "assets"
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_id = uuid.uuid4().hex
    file_extension = Path(file.filename).suffix
    filename = f"{file_id}{file_extension}"
    
    file_path = upload_dir / filename
    
    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)
    
    try:
        from backend.src.core.entities.asset_photo import PhotoStage
        photo_stage = PhotoStage(stage)
    except ValueError:
        photo_stage = PhotoStage.OTHER
    
    photo = AssetPhotoResponse(
        id=asset_photo_id_counter,
        asset_id=asset_id,
        document_id=0,
        uploaded_by=1,
        stage=photo_stage.value,
        description=description,
        taken_at=datetime.now() if taken_at is None else datetime.fromisoformat(taken_at),
        taken_by=taken_by,
        inventory_check_id=inventory_check_id,
        repair_request_id=repair_request_id,
        is_before=is_before,
        is_after=is_after,
        sort_order=sort_order,
        uploaded_at=datetime.now(),
    )
    
    asset_photos_db[asset_photo_id_counter] = photo
    asset_photo_id_counter += 1
    
    return photo


@router.delete("/asset-photos/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset_photo(photo_id: int):
    if photo_id not in asset_photos_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
    
    del asset_photos_db[photo_id]
    return None
