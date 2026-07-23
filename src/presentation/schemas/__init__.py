from .asset import AssetCreate, AssetUpdate, AssetResponse, AssetListResponse
from .user import UserCreate, UserUpdate, UserResponse, UserLogin, UserToken
from .repair import (
    RepairCreate,
    RepairUpdate,
    RepairResponse,
    RepairListResponse,
    RepairStatusUpdate,
    RepairPriorityUpdate,
)
from .document import DocumentCreate, DocumentResponse, DocumentListResponse
from .employee import EmployeeCreate, EmployeeUpdate, EmployeeResponse
from .department import DepartmentCreate, DepartmentUpdate, DepartmentResponse
from .movement import MovementCreate, MovementResponse
from .maintenance import MaintenanceCreate, MaintenanceResponse
from .depreciation import DepreciationCreate, DepreciationResponse
from .inventory import InventoryCreate, InventoryResponse
from .import_job import ImportJobCreate, ImportJobResponse
from .asset_photo import AssetPhotoCreate, AssetPhotoResponse

__all__ = [
    "AssetCreate",
    "AssetUpdate",
    "AssetResponse",
    "AssetListResponse",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserLogin",
    "UserToken",
    "RepairCreate",
    "RepairUpdate",
    "RepairResponse",
    "RepairListResponse",
    "RepairStatusUpdate",
    "RepairPriorityUpdate",
    "DocumentCreate",
    "DocumentResponse",
    "DocumentListResponse",
    "EmployeeCreate",
    "EmployeeUpdate",
    "EmployeeResponse",
    "DepartmentCreate",
    "DepartmentUpdate",
    "DepartmentResponse",
    "MovementCreate",
    "MovementResponse",
    "MaintenanceCreate",
    "MaintenanceResponse",
    "DepreciationCreate",
    "DepreciationResponse",
    "InventoryCreate",
    "InventoryResponse",
    "ImportJobCreate",
    "ImportJobResponse",
    "AssetPhotoCreate",
    "AssetPhotoResponse",
]
