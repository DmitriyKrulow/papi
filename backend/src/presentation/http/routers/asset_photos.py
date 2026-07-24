from fastapi import APIRouter

from ..schemas.asset_photos import AssetPhotoResponse

router = APIRouter(prefix="/asset-photos", tags=["asset-photos"])


@router.get("/")
def list_asset_photos():
    pass


@router.get("/{photo_id}")
def get_asset_photo(photo_id: int):
    pass


@router.post("/")
def upload_asset_photo():
    pass


@router.delete("/{photo_id}")
def delete_asset_photo(photo_id: int):
    pass
