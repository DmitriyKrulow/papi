# src/core/entities/document.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class DocumentType(Enum):
    """Типы документов"""
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


class DocumentCategory(Enum):
    """Категории документов"""
    ASSET = "asset"
    REPAIR = "repair"
    INVENTORY = "inventory"
    MOVEMENT = "movement"
    WRITE_OFF = "write_off"
    CONTRACT = "contract"
    SUPPLIER = "supplier"
    EMPLOYEE = "employee"


@dataclass
class Document:
    """
    Сущность "Документ/Файл".
    """
    id: int
    filename: str
    file_path: str
    file_size: int
    mime_type: str
    uploaded_by: int
    
    # Поля со значениями по умолчанию
    document_type: DocumentType = DocumentType.OTHER
    category: DocumentCategory = DocumentCategory.ASSET
    
    entity_id: Optional[int] = None
    entity_type: Optional[str] = None
    
    title: Optional[str] = None
    description: Optional[str] = None
    uploaded_at: datetime = field(default_factory=datetime.now)
    
    is_primary: bool = False
    sort_order: int = 0
    
    file_hash: Optional[str] = None
    
    def get_file_extension(self) -> str:
        """Возвращает расширение файла"""
        if '.' in self.filename:
            return self.filename.split('.')[-1].lower()
        return ''
    
    def get_file_size_display(self) -> str:
        """Размер файла в читаемом формате"""
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        elif self.file_size < 1024 * 1024 * 1024:
            return f"{self.file_size / (1024 * 1024):.1f} MB"
        else:
            return f"{self.file_size / (1024 * 1024 * 1024):.1f} GB"
    
    def is_image(self) -> bool:
        """Проверяет, является ли файл изображением"""
        return self.mime_type.startswith('image/')
    
    def is_pdf(self) -> bool:
        """Проверяет, является ли файл PDF"""
        return self.mime_type == 'application/pdf'
    
    def is_document(self) -> bool:
        """Проверяет, является ли файл документом"""
        return self.mime_type in (
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
    
    def get_type_display(self) -> str:
        """Читаемое название типа документа"""
        types = {
            DocumentType.PHOTO: "Фотография",
            DocumentType.SCAN: "Скан",
            DocumentType.CONTRACT: "Договор",
            DocumentType.INVOICE: "Счет-фактура",
            DocumentType.ACT: "Акт",
            DocumentType.WARRANTY: "Гарантийный талон",
            DocumentType.PASSPORT: "Паспорт",
            DocumentType.MANUAL: "Руководство",
            DocumentType.CERTIFICATE: "Сертификат",
            DocumentType.REPORT: "Отчет",
            DocumentType.OTHER: "Другое",
        }
        return types.get(self.document_type, str(self.document_type))
    
    def get_category_display(self) -> str:
        """Читаемое название категории"""
        categories = {
            DocumentCategory.ASSET: "Актив",
            DocumentCategory.REPAIR: "Ремонт",
            DocumentCategory.INVENTORY: "Инвентаризация",
            DocumentCategory.MOVEMENT: "Перемещение",
            DocumentCategory.WRITE_OFF: "Списание",
            DocumentCategory.CONTRACT: "Договор",
            DocumentCategory.SUPPLIER: "Поставщик",
            DocumentCategory.EMPLOYEE: "Сотрудник",
        }
        return categories.get(self.category, str(self.category))
    
    def __str__(self) -> str:
        return f"Document(id={self.id}, filename='{self.filename}')"