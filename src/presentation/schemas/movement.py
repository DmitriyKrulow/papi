from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class MovementCreate(BaseModel):
    asset_id: int = Field(..., gt=0)
    movement_date: date = Field(...)
    from_department_id: Optional[int] = Field(None, gt=0)
    from_department_name: Optional[str] = Field(None, max_length=255)
    from_location: Optional[str] = Field(None, max_length=255)
    to_department_id: Optional[int] = Field(None, gt=0)
    to_department_name: Optional[str] = Field(None, max_length=255)
    to_location: Optional[str] = Field(None, max_length=255)
    from_responsible_id: Optional[int] = None
    to_responsible_id: Optional[int] = None
    reason: Optional[str] = Field(None, max_length=65535)
    document_number: Optional[str] = Field(None, max_length=100)
    created_by: Optional[int] = None


class MovementResponse(BaseModel):
    id: int
    asset_id: int
    movement_date: date
    from_department_id: Optional[int] = None
    from_department_name: Optional[str] = None
    from_location: Optional[str] = None
    to_department_id: Optional[int] = None
    to_department_name: Optional[str] = None
    to_location: Optional[str] = None
    from_responsible_id: Optional[int] = None
    to_responsible_id: Optional[int] = None
    reason: Optional[str] = None
    document_number: Optional[str] = None
    created_at: datetime
    created_by: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
