from typing import List, Tuple, Optional

from backend.src.infrastructure.db.models.asset_photo import AssetPhoto as AssetPhotoModel
from backend.src.core.entities.asset_photo import AssetPhoto, PhotoStage
from backend.src.use_cases.interfaces.repositories import IAssetPhotoRepository


class AssetPhotoRepository(IAssetPhotoRepository):
    """Реализация репозитория для работы с фотографиями активов"""

    def __init__(self, session):
        self.session = session

    async def get_all(self, skip: int = 0, limit: int = 100) -> Tuple[List[AssetPhoto], int]:
        query = self.session.query(AssetPhotoModel)
        total = query.count()
        photos = query.offset(skip).limit(limit).all()
        
        return [self._to_entity(photo) for photo in photos], total

    async def get_by_id(self, photo_id: int) -> Optional[AssetPhoto]:
        photo = self.session.query(AssetPhotoModel).filter(AssetPhotoModel.id == photo_id).first()
        if not photo:
            return None
        return self._to_entity(photo)

    async def add(self, photo: AssetPhoto) -> int:
        db_photo = AssetPhotoModel(
            asset_id=photo.asset_id,
            document_id=photo.document_id,
            uploaded_by=photo.uploaded_by,
            stage=photo.stage,
            description=photo.description,
            taken_at=photo.taken_at,
            taken_by=photo.taken_by,
            inventory_check_id=photo.inventory_check_id,
            repair_request_id=photo.repair_request_id,
            is_before=photo.is_before,
            is_after=photo.is_after,
            sort_order=photo.sort_order,
        )
        self.session.add(db_photo)
        self.session.flush()
        return db_photo.id

    async def delete(self, photo_id: int) -> None:
        photo = self.session.query(AssetPhotoModel).filter(AssetPhotoModel.id == photo_id).first()
        if photo:
            self.session.delete(photo)

    async def get_by_asset(self, asset_id: int) -> List[AssetPhoto]:
        photos = self.session.query(AssetPhotoModel).filter(AssetPhotoModel.asset_id == asset_id).all()
        return [self._to_entity(photo) for photo in photos]

    def _to_entity(self, model: AssetPhotoModel) -> AssetPhoto:
        return AssetPhoto(
            id=model.id,
            asset_id=model.asset_id,
            document_id=model.document_id,
            uploaded_by=model.uploaded_by,
            stage=model.stage,
            description=model.description,
            taken_at=model.taken_at,
            taken_by=model.taken_by,
            uploaded_at=model.uploaded_at,
            inventory_check_id=model.inventory_check_id,
            repair_request_id=model.repair_request_id,
            is_before=model.is_before,
            is_after=model.is_after,
            sort_order=model.sort_order,
        )
