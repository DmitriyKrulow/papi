from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class DepreciationCreate(BaseModel):
    asset_id: int = Field(..., gt=0)
    period_start: date = Field(...)
    period_end: date = Field(...)
    depreciation_amount: Decimal = Field(..., gt=0)
    accumulated_depreciation: Decimal = Field(..., ge=0)
    book_value_before: Decimal = Field(..., gt=0)
    book_value_after: Decimal = Field(..., ge=0)
    rate: Decimal = Field(..., ge=0, le=100)
    method: str = Field(..., min_length=1, max_length=50)
    posted_by: Optional[int] = None
    notes: Optional[str] = Field(None, max_length=65535)
    document_number: Optional[str] = Field(None, max_length=100)


class DepreciationResponse(BaseModel):
    id: int
    asset_id: int
    period_start: date
    period_end: date
    depreciation_amount: Decimal
    accumulated_depreciation: Decimal
    book_value_before: Decimal
    book_value_after: Decimal
    rate: Decimal
    method: str
    created_at: datetime
    posted_at: Optional[datetime] = None
    posted_by: Optional[int] = None
    notes: Optional[str] = None
    document_number: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
