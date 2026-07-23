from datetime import datetime
from typing import Optional, List
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class DocumentType(str, Enum):
    PHOTO = "photo"
    SCAN = "scan"
    CONTRACT = "contract"
    INVOICE = "invoice"
    ACT = "act"
    WARRANTY = "warranty"
    PASSPORT = "passport"
    MANUAL = "manual"
    CERTIFICATE = "certificate"
    REPORT = "report"
    OTHER = "other"


class DocumentCategory(str, Enum):
    ASSET = "asset"
    REPAIR = "repair"
    INVENTORY = "inventory"
    MOVEMENT = "movement"
    WRITE_OFF = "write_off"
    CONTRACT = "contract"
    SUPPLIER = "supplier"
    EMPLOYEE = "employee"


class DocumentCreate(BaseModel):
    filename: str = Field(..., min_length=1, max_length=255)
    file_path: str = Field(..., min_length=1, max_length=500)
    file_size: int = Field(..., ge=0)
    mime_type: str = Field(..., min_length=1, max_length=100)
    uploaded_by: int = Field(..., gt=0)
    document_type: Optional[DocumentType] = DocumentType.OTHER
    category: Optional[DocumentCategory] = DocumentCategory.ASSET
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=65535)
    entity_id: Optional[int] = None
    entity_type: Optional[str] = Field(None, max_length=50)
    is_primary: bool = False
    sort_order: int = 0
    file_hash: Optional[str] = Field(None, max_length=255)


class DocumentResponse(BaseModel):
    id: int
    filename: str
    file_path: str
    file_size: int
    mime_type: str
    uploaded_by: int
    document_type: DocumentType
    category: DocumentCategory
    title: Optional[str] = None
    description: Optional[str] = None
    entity_id: Optional[int] = None
    entity_type: Optional[str] = None
    uploaded_at: datetime
    is_primary: bool
    sort_order: int
    file_hash: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DocumentListResponse(BaseModel):
    total: int
    items: List[DocumentResponse]
