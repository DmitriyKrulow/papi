# src/presentation/http/schemas/asset_photos.py
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class AssetPhotoBase(BaseModel):
    description: Optional[str] = Field(None, max_length=1000, description="???????? ????")
    taken_at: Optional[datetime] = Field(None, description="????? ??????")
    taken_by: Optional[int] = Field(None, description="??? ?????? ????")
    sort_order: Optional[int] = Field(0, ge=0, description="??????? ??????????")


class AssetPhotoCreate(AssetPhotoBase):
    stage: str = Field("other", description="???? ?????????? ????? (receiving, inventory, write_off, repair, maintenance, movement)")
    is_before: Optional[bool] = Field(False, description="???? ?? ?????????")
    is_after: Optional[bool] = Field(False, description="???? ????? ?????????")
    inventory_check_id: Optional[int] = Field(None, description="ID ??????????????")
    repair_request_id: Optional[int] = Field(None, description="ID ?????? ?? ??????")


class AssetPhotoResponse(AssetPhotoBase):
    id: int = Field(..., description="ID ????")
    asset_id: int
    document_id: int
    uploaded_by: int
    stage: str
    inventory_check_id: Optional[int]
    repair_request_id: Optional[int]
    is_before: bool
    is_after: bool
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AssetPhotoListResponse(BaseModel):
    total: int
    items: list[AssetPhotoResponse]


