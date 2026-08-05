# src/infrastructure/db/models/__init__.py
from sqlalchemy.orm import declarative_base

# Создаем Base
Base = declarative_base()

# Импортируем все модели ПОСЛЕ создания Base
from .user import User
from .asset import Asset
from .department import Department
from .asset_category import AssetCategory
from .asset_type_config import AssetTypeConfig
from .maintenance_event import MaintenanceEvent
from .document import Document
from .report import Report
from .depreciation_record import DepreciationRecord
from .repair_request import RepairRequest
from .repair_template import RepairTemplate
from .maintenance_record import MaintenanceRecord
from .movement_record import MovementRecord
from .inventory_check import InventoryCheck
from .inventory_check_item import InventoryCheckItem
from .employee import Employee
from .asset_type import AssetType
from .asset_photo import AssetPhoto
from .document_link import DocumentLink
from .import_job import ImportJob
from .brute_force_log import BruteForceLog
from .department import Room

__all__ = [
    "Base",
    "User",
    "Asset",
    "Department",
    "Room",
    "AssetCategory",
    "AssetTypeConfig",
    "MaintenanceEvent",
    "Document",
    "DocumentLink",
    "Report",
    "DepreciationRecord",
    "RepairRequest",
    "RepairTemplate",
    "MaintenanceRecord",
    "MovementRecord",
    "InventoryCheck",
    "InventoryCheckItem",
    "Employee",
    "AssetType",
    "AssetPhoto",
    "ImportJob",
    "BruteForceLog",
]