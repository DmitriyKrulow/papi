from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class MaintenanceCreate(BaseModel):
    asset_id: int = Field(..., gt=0)
    maintenance_date: date = Field(...)
    maintenance_type: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=65535)
    cost: Optional[Decimal] = Field(None, ge=0)
    performed_by: Optional[str] = Field(None, max_length=255)
    contractor: Optional[str] = Field(None, max_length=255)
    result: Optional[str] = Field(None, max_length=100)
    next_maintenance_date: Optional[date] = None
    document_number: Optional[str] = Field(None, max_length=100)
    document_date: Optional[date] = None
    created_by: Optional[int] = None


class MaintenanceResponse(BaseModel):
    id: int
    asset_id: int
    maintenance_date: date
    maintenance_type: str
    description: Optional[str] = None
    cost: Optional[Decimal] = None
    performed_by: Optional[str] = None
    contractor: Optional[str] = None
    result: Optional[str] = None
    next_maintenance_date: Optional[date] = None
    document_number: Optional[str] = None
    document_date: Optional[date] = None
    created_at: datetime
    created_by: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
