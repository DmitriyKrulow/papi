from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from enum import Enum

from pydantic import BaseModel, Field, field_validator, ConfigDict


class AssetStatusEnum(str, Enum):
    ACTIVE = "active"
    MAINTENANCE = "maintenance"
    RESERVED = "reserved"
    WRITTEN_OFF = "written_off"
    DECOMMISSIONED = "decommissioned"


class AssetCreate(BaseModel):
    inventory_number: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=65535)
    model: Optional[str] = Field(None, max_length=255)
    manufacturer_code: Optional[str] = Field(None, max_length=100)
    manufacturer_name: Optional[str] = Field(None, max_length=255)
    country_of_origin: Optional[str] = Field(None, max_length=100)
    accounting_code: Optional[str] = Field(None, max_length=100)
    department_code: Optional[str] = Field(None, max_length=100)
    responsible_person: Optional[str] = Field(None, max_length=255)
    purchase_price: Optional[Decimal] = Field(None, ge=0)
    current_value: Optional[Decimal] = Field(None, ge=0)
    residual_value: Optional[Decimal] = Field(None, ge=0)
    depreciation_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    location: Optional[str] = Field(None, max_length=255)
    location_address: Optional[str] = Field(None, max_length=500)
    responsible_phone: Optional[str] = Field(None, max_length=50)
    purchase_date: Optional[date] = None
    commissioning_date: Optional[date] = None
    warranty_expiry: Optional[date] = None
    last_maintenance_date: Optional[date] = None
    next_maintenance_date: Optional[date] = None
    decommissioning_date: Optional[date] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = Field(None, max_length=65535)
    is_active: bool = True
    created_by: Optional[int] = None


class AssetUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=65535)
    model: Optional[str] = Field(None, max_length=255)
    manufacturer_code: Optional[str] = Field(None, max_length=100)
    manufacturer_name: Optional[str] = Field(None, max_length=255)
    country_of_origin: Optional[str] = Field(None, max_length=100)
    accounting_code: Optional[str] = Field(None, max_length=100)
    department_code: Optional[str] = Field(None, max_length=100)
    responsible_person: Optional[str] = Field(None, max_length=255)
    purchase_price: Optional[Decimal] = Field(None, ge=0)
    current_value: Optional[Decimal] = Field(None, ge=0)
    residual_value: Optional[Decimal] = Field(None, ge=0)
    depreciation_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    location: Optional[str] = Field(None, max_length=255)
    location_address: Optional[str] = Field(None, max_length=500)
    responsible_phone: Optional[str] = Field(None, max_length=50)
    purchase_date: Optional[date] = None
    commissioning_date: Optional[date] = None
    warranty_expiry: Optional[date] = None
    last_maintenance_date: Optional[date] = None
    next_maintenance_date: Optional[date] = None
    decommissioning_date: Optional[date] = None
    status: Optional[AssetStatusEnum] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = Field(None, max_length=65535)
    is_active: Optional[bool] = None
    updated_by: Optional[int] = None


class AssetResponse(BaseModel):
    id: int
    inventory_number: str
    name: str
    description: Optional[str] = None
    model: Optional[str] = None
    manufacturer_code: Optional[str] = None
    manufacturer_name: Optional[str] = None
    country_of_origin: Optional[str] = None
    accounting_code: Optional[str] = None
    department_code: Optional[str] = None
    responsible_person: Optional[str] = None
    purchase_price: Optional[Decimal] = None
    current_value: Optional[Decimal] = None
    residual_value: Optional[Decimal] = None
    depreciation_rate: Optional[Decimal] = None
    location: Optional[str] = None
    location_address: Optional[str] = None
    responsible_phone: Optional[str] = None
    purchase_date: Optional[date] = None
    commissioning_date: Optional[date] = None
    warranty_expiry: Optional[date] = None
    last_maintenance_date: Optional[date] = None
    next_maintenance_date: Optional[date] = None
    decommissioning_date: Optional[date] = None
    status: AssetStatusEnum
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class AssetListResponse(BaseModel):
    total: int
    items: List[AssetResponse]
