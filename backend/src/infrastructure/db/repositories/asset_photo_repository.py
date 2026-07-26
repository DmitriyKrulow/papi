from src.infrastructure.db.models.asset_photo import AssetPhoto as AssetPhotoModel
from src.core.entities.asset_photo import AssetPhoto, PhotoStage
from src.use_cases.interfaces.repositories import IAssetPhotoRepository


class AssetPhotoRepository(IAssetPhotoRepository):
    """Repository for asset photo operations"""
    pass
