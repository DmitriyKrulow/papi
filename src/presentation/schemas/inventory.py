from datetime import date, datetime
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict


class InventoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    check_date: date = Field(...)
    department_id: Optional[int] = Field(None, gt=0)
    responsible_id: Optional[int] = None
    commission_members: Optional[List[int]] = None
    status: str = Field("created", max_length=50)


class InventoryResponse(BaseModel):
    id: int
    name: str
    check_date: date
    department_id: Optional[int] = None
    total_checked: int
    found: int
    missing: int
    surplus: int
    status: str
    responsible_id: Optional[int] = None
    commission_members: Optional[List[int]] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
