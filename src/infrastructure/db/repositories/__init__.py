from .asset_repository import AssetRepository
from .user_repository import UserRepository
from .repair_repository import RepairRepository
from .document_repository import DocumentRepository
from .employee_repository import EmployeeRepository
from .department_repository import DepartmentRepository
from .movement_repository import MovementRepository
from .maintenance_repository import MaintenanceRepository
from .depreciation_repository import DepreciationRepository
from .inventory_repository import InventoryRepository
from .import_repository import ImportRepository
from .asset_photo_repository import AssetPhotoRepository

__all__ = [
    "AssetRepository",
    "UserRepository",
    "RepairRepository",
    "DocumentRepository",
    "EmployeeRepository",
    "DepartmentRepository",
    "MovementRepository",
    "MaintenanceRepository",
    "DepreciationRepository",
    "InventoryRepository",
    "ImportRepository",
    "AssetPhotoRepository",
]
