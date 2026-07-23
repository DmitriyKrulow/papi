from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from src.infrastructure.db.models import AssetPhoto as AssetPhotoModel
from src.core.entities.asset_photo import AssetPhoto, PhotoStage


class AssetPhotoRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, photo: AssetPhoto) -> None:
        model = self._to_model(photo)
        self.session.add(model)
        self.session.flush()

    def get_by_id(self, id: int) -> Optional[AssetPhoto]:
        model = self.session.get(AssetPhotoModel, id)
        if model:
            return self._to_entity(model)
        return None

    def list_all(self) -> List[AssetPhoto]:
        statement = select(AssetPhotoModel)
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def list_by_asset(self, asset_id: int) -> List[AssetPhoto]:
        statement = select(AssetPhotoModel).where(AssetPhotoModel.asset_id == asset_id)
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def list_by_document(self, document_id: int) -> List[AssetPhoto]:
        statement = select(AssetPhotoModel).where(AssetPhotoModel.document_id == document_id)
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def list_by_stage(self, stage: PhotoStage) -> List[AssetPhoto]:
        statement = select(AssetPhotoModel).where(AssetPhotoModel.stage == str(stage.value))
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def list_before_repair(self, repair_request_id: int) -> List[AssetPhoto]:
        statement = select(AssetPhotoModel).where(
            AssetPhotoModel.repair_request_id == repair_request_id,
            AssetPhotoModel.is_before == True
        )
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def list_after_repair(self, repair_request_id: int) -> List[AssetPhoto]:
        statement = select(AssetPhotoModel).where(
            AssetPhotoModel.repair_request_id == repair_request_id,
            AssetPhotoModel.is_after == True
        )
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def list_by_inventory_check(self, inventory_check_id: int) -> List[AssetPhoto]:
        statement = select(AssetPhotoModel).where(AssetPhotoModel.inventory_check_id == inventory_check_id)
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def count(self) -> int:
        statement = select(func.count(AssetPhotoModel.id))
        return self.session.scalar(statement) or 0

    def _to_model(self, entity: AssetPhoto) -> AssetPhotoModel:
        return AssetPhotoModel(
            id=entity.id,
            asset_id=entity.asset_id,
            document_id=entity.document_id,
            uploaded_by=entity.uploaded_by,
            stage=str(entity.stage.value) if entity.stage else None,
            description=entity.description,
            taken_at=entity.taken_at,
            taken_by=entity.taken_by,
            uploaded_at=entity.uploaded_at,
            inventory_check_id=entity.inventory_check_id,
            repair_request_id=entity.repair_request_id,
            is_before=entity.is_before,
            is_after=entity.is_after,
            sort_order=entity.sort_order,
        )

    def _to_entity(self, model: AssetPhotoModel) -> AssetPhoto:
        return AssetPhoto(
            id=model.id,
            asset_id=model.asset_id,
            document_id=model.document_id,
            uploaded_by=model.uploaded_by,
            stage=PhotoStage(model.stage) if model.stage else PhotoStage.OTHER,
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
