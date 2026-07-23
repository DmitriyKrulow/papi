from datetime import datetime
from typing import Optional, Dict, Any, List

from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class ImportStatusEnum(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


class ImportTypeEnum(str, Enum):
    ASSETS = "assets"
    EMPLOYEES = "employees"
    DEPARTMENTS = "departments"
    SUPPLIERS = "suppliers"
    CONTRACTS = "contracts"
    INVENTORY = "inventory"


class ImportJobCreate(BaseModel):
    filename: str = Field(..., min_length=1, max_length=255)
    import_type: ImportTypeEnum = ImportTypeEnum.ASSETS
    created_by: int = Field(..., gt=0)
    parameters: Optional[Dict[str, Any]] = None


class ImportJobResponse(BaseModel):
    id: int
    filename: str
    import_type: ImportTypeEnum
    created_by: int
    status: ImportStatusEnum
    total_rows: int
    processed_rows: int
    successful_rows: int
    failed_rows: int
    errors: Optional[List[Dict[str, Any]]] = None
    error_file_id: Optional[int] = None
    result_file_id: Optional[int] = None
    summary: Optional[Dict[str, Any]] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    parameters: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)
