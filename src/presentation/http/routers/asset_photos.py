from typing import List

from fastapi import APIRouter, HTTPException, Depends
from src.presentation.schemas.asset_photo import AssetPhotoCreate, AssetPhotoResponse
from src.infrastructure.db.unit_of_work import UnitOfWork

router = APIRouter(prefix="/asset-photos", tags=["AssetPhotos"])


@router.get("/", response_model=List[AssetPhotoResponse])
def list_asset_photos(uow: UnitOfWork = Depends()):
    photos = uow.asset_photo_repository.list_all()
    return photos


@router.get("/{photo_id}", response_model=AssetPhotoResponse)
def get_asset_photo(photo_id: int, uow: UnitOfWork = Depends()):
    photo = uow.asset_photo_repository.get_by_id(photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Asset photo not found")
    return photo


@router.get("/asset/{asset_id}", response_model=List[AssetPhotoResponse])
def get_asset_photos_by_asset(asset_id: int, uow: UnitOfWork = Depends()):
    photos = uow.asset_photo_repository.list_by_asset(asset_id)
    return photos


@router.get("/document/{document_id}", response_model=List[AssetPhotoResponse])
def get_asset_photos_by_document(document_id: int, uow: UnitOfWork = Depends()):
    photos = uow.asset_photo_repository.list_by_document(document_id)
    return photos


@router.post("/", response_model=AssetPhotoResponse, status_code=201)
def create_asset_photo(photo: AssetPhotoCreate, uow: UnitOfWork = Depends()):
    try:
        uow.asset_photo_repository.save(photo)
        uow.commit()
        return uow.asset_photo_repository.get_by_id(photo.id)
    except Exception as e:
        uow.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{photo_id}", status_code=204)
def delete_asset_photo(photo_id: int, uow: UnitOfWork = Depends()):
    existing_photo = uow.asset_photo_repository.get_by_id(photo_id)
    if not existing_photo:
        raise HTTPException(status_code=404, detail="Asset photo not found")
    try:
        uow.asset_photo_repository.delete(photo_id)
        uow.commit()
    except Exception as e:
        uow.rollback()
        raise HTTPException(status_code=400, detail=str(e))
