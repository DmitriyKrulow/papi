from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class AssetPhotoCreate(BaseModel):
    asset_id: int = Field(..., gt=0)
    document_id: int = Field(..., gt=0)
    uploaded_by: int = Field(..., gt=0)
    stage: str = Field("other", max_length=50)
    description: Optional[str] = Field(None, max_length=65535)
    taken_at: Optional[datetime] = None
    taken_by: Optional[int] = None
    inventory_check_id: Optional[int] = None
    repair_request_id: Optional[int] = None
    is_before: bool = False
    is_after: bool = False
    sort_order: int = 0


class AssetPhotoResponse(BaseModel):
    id: int
    asset_id: int
    document_id: int
    uploaded_by: int
    stage: str
    description: Optional[str] = None
    taken_at: Optional[datetime] = None
    taken_by: Optional[int] = None
    uploaded_at: datetime
    inventory_check_id: Optional[int] = None
    repair_request_id: Optional[int] = None
    is_before: bool
    is_after: bool
    sort_order: int

    model_config = ConfigDict(from_attributes=True)
