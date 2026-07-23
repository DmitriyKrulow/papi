from pathlib import Path
import uuid
from typing import TYPE_CHECKING

from backend.src.core.entities.asset_photo import PhotoStage

if TYPE_CHECKING:
    from backend.src.use_cases.interfaces.unit_of_work import IUnitOfWork


class UploadAssetPhotoService:
    def __init__(self, unit_of_work: "IUnitOfWork"):
        self.uow = unit_of_work

    async def __call__(self, asset_id: int, file, uploaded_by: int, data: dict):
        file_path = await self._save_file(file)
        
        stage_value = data.get("stage", "other")
        try:
            stage = PhotoStage(stage_value)
        except ValueError:
            stage = PhotoStage.OTHER
        
        photo_id = await self.uow.asset_photos.add(
            asset_id=asset_id,
            document_id=None,
            uploaded_by=uploaded_by,
            stage=stage,
            description=data.get("description"),
            taken_at=data.get("taken_at"),
            taken_by=data.get("taken_by"),
            inventory_check_id=data.get("inventory_check_id"),
            repair_request_id=data.get("repair_request_id"),
            is_before=data.get("is_before", False),
            is_after=data.get("is_after", False),
            sort_order=data.get("sort_order", 0),
        )
        
        await self.uow.commit()
        
        return photo_id

    async def _save_file(self, file) -> Path:
        upload_dir = Path("uploads/assets")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_id = uuid.uuid4().hex
        file_extension = Path(file.filename).suffix
        filename = f"{file_id}{file_extension}"
        
        file_path = upload_dir / filename
        
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        
        return file_path
