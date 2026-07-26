# src/infrastructure/db/models/__init__.py
from sqlalchemy.orm import declarative_base

# Создаем Base
Base = declarative_base()

# Импортируем все модели ПОСЛЕ создания Base
from .user import User
from .asset import Asset
from .department import Department
from .asset_category import AssetCategory
from .document import Document
from .report import Report
from .depreciation_record import DepreciationRecord
from .repair_request import RepairRequest
from .repair_template import RepairTemplate
from .maintenance_record import MaintenanceRecord
from .movement_record import MovementRecord
from .inventory_check import InventoryCheck
from .employee import Employee
from .asset_type import AssetType
from .asset_photo import AssetPhoto
from .import_job import ImportJob

__all__ = [
    "Base",
    "User",
    "Asset",
    "Department",
    "AssetCategory",
    "Document",
    "Report",
    "DepreciationRecord",
    "RepairRequest",
    "RepairTemplate",
    "MaintenanceRecord",
    "MovementRecord",
    "InventoryCheck",
    "Employee",
    "AssetType",
    "AssetPhoto",
    "ImportJob",
]