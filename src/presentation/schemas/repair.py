from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from enum import Enum

from pydantic import BaseModel, Field, field_validator, ConfigDict


class RepairPriorityEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class RepairStatusEnum(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class RepairCreate(BaseModel):
    asset_id: int = Field(..., gt=0)
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    priority: RepairPriorityEnum = RepairPriorityEnum.MEDIUM
    created_by: int = Field(..., gt=0)
    desired_completion_date: Optional[date] = None
    deadline: Optional[date] = None
    estimated_cost: Optional[Decimal] = Field(None, ge=0)


class RepairUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    priority: Optional[RepairPriorityEnum] = None
    assigned_to: Optional[int] = Field(None, gt=0)
    desired_completion_date: Optional[date] = None
    actual_completion_date: Optional[date] = None
    deadline: Optional[date] = None
    estimated_cost: Optional[Decimal] = Field(None, ge=0)
    actual_cost: Optional[Decimal] = Field(None, ge=0)
    completion_notes: Optional[str] = Field(None, max_length=65535)
    rejection_reason: Optional[str] = Field(None, max_length=65535)
    maintenance_record_id: Optional[int] = None
    updated_by: Optional[int] = Field(None, gt=0)


class RepairStatusUpdate(BaseModel):
    status: RepairStatusEnum = Field(...)
    updated_by: int = Field(..., gt=0)


class RepairPriorityUpdate(BaseModel):
    priority: RepairPriorityEnum = Field(...)
    updated_by: int = Field(..., gt=0)


class RepairResponse(BaseModel):
    id: int
    asset_id: int
    title: str
    description: str
    priority: RepairPriorityEnum
    status: RepairStatusEnum
    created_at: datetime
    created_by: int
    assigned_to: Optional[int] = None
    assigned_at: Optional[datetime] = None
    desired_completion_date: Optional[date] = None
    actual_completion_date: Optional[date] = None
    deadline: Optional[date] = None
    estimated_cost: Optional[Decimal] = None
    actual_cost: Optional[Decimal] = None
    completion_notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    maintenance_record_id: Optional[int] = None
    updated_at: datetime
    updated_by: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class RepairListResponse(BaseModel):
    total: int
    items: List[RepairResponse]
