# src/presentation/http/schemas/documents.py
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class DocumentBase(BaseModel):
    filename: str = Field(..., min_length=1, max_length=255, description="Имя файла")
    file_size: int = Field(..., ge=0, description="Размер файла в байтах")
    mime_type: str = Field(..., max_length=100, description="MIME тип файла")
    title: Optional[str] = Field(None, max_length=255, description="Заголовок документа")
    description: Optional[str] = Field(None, max_length=1000, description="Описание")


class DocumentCreate(DocumentBase):
    document_type: Optional[str] = Field("other", description="Тип документа")
    category: Optional[str] = Field("asset", description="Категория документа")
    entity_id: Optional[int] = Field(None, description="ID сущности")
    entity_type: Optional[str] = Field(None, description="Тип сущности")
    is_primary: Optional[bool] = Field(False, description="Основной документ")


class DocumentResponse(DocumentBase):
    id: int = Field(..., description="ID документа")
    document_type: str
    category: str
    entity_id: Optional[int]
    entity_type: Optional[str]
    file_path: str
    uploaded_by: int
    uploaded_at: datetime
    is_primary: bool
    sort_order: int
    file_hash: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class DocumentListResponse(BaseModel):
    total: int
    items: list[DocumentResponse]
