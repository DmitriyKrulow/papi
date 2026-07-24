# src/presentation/http/schemas/documents.py
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DocumentBase(BaseModel):
    filename: str
    file_path: str
    file_size: int
    mime_type: str
    document_type: str = "other"
    category: str = "asset"
    entity_id: Optional[int] = None
    entity_type: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    is_primary: bool = False
    sort_order: int = 0
    file_hash: Optional[str] = None


class DocumentCreate(DocumentBase):
    uploaded_by: int


class DocumentResponse(DocumentBase):
    id: int
    uploaded_by: int
    uploaded_at: datetime

    class Config:
        from_attributes = True


# Типы документов
class DocumentType:
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


# Категории документов
class DocumentCategory:
    ASSET = "asset"
    REPAIR = "repair"
    INVENTORY = "inventory"
    MOVEMENT = "movement"
    WRITE_OFF = "write_off"
    CONTRACT = "contract"
    SUPPLIER = "supplier"
    EMPLOYEE = "employee"
    REPORT = "report"