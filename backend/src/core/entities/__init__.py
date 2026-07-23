# src/core/entities/__init__.py
from .asset import Asset
from .organization import Organization
from .department import Department
from .employee import Employee
from .asset_category import AssetCategory
from .maintenance_record import MaintenanceRecord
from .depreciation_record import DepreciationRecord, DepreciationMethod
from .movement_record import MovementRecord
from .inventory_check import InventoryCheck
from .repair_request import RepairRequest, RepairPriority, RepairStatus
from .document import Document, DocumentType, DocumentCategory
from .report import Report, ReportType, ReportFormat, ReportStatus
from .asset_photo import AssetPhoto, PhotoStage
from .import_job import ImportJob, ImportStatus, ImportType

__all__ = [
    # Основные сущности
    'Asset',
    'Organization',
    'Department',
    'Employee',
    'AssetCategory',
    
    # Учет и обслуживание
    'MaintenanceRecord',
    'DepreciationRecord',
    'DepreciationMethod',
    'MovementRecord',
    'InventoryCheck',
    
    # Заявки и документы
    'RepairRequest',
    'RepairPriority',
    'RepairStatus',
    'Document',
    'DocumentType',
    'DocumentCategory',
    'Report',
    'ReportType',
    'ReportFormat',
    'ReportStatus',
    'AssetPhoto',
    'PhotoStage',
    
    # Импорт
    'ImportJob',
    'ImportStatus',
    'ImportType',
]