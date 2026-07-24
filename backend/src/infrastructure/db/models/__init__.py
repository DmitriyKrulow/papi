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

__all__ = [
    "Base",
    "User",
    "Asset",
    "Department",
    "AssetCategory",
    "Document",
    "Report",
    "DepreciationRecord",
]