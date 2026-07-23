from .assets import router as assets_router
from .users import router as users_router
from .repairs import router as repairs_router
from .documents import router as documents_router
from .employees import router as employees_router
from .departments import router as departments_router
from .movements import router as movements_router
from .maintenance import router as maintenance_router
from .depreciation import router as depreciation_router
from .inventory import router as inventory_router
from .imports import router as imports_router
from .asset_photos import router as asset_photos_router

__all__ = [
    "assets_router",
    "users_router",
    "repairs_router",
    "documents_router",
    "employees_router",
    "departments_router",
    "movements_router",
    "maintenance_router",
    "depreciation_router",
    "inventory_router",
    "imports_router",
    "asset_photos_router",
]
