# src/core/value_objects/__init__.py
from .phone import Phone
from .coordinates import Coordinates
from .password_hash import PasswordHash
from .date_range import DateRange
from .money import Money
from .inventory_number import InventoryNumber
from .batch_id import BatchId
from .serial_number import SerialNumber
from .year_period import YearPeriod
from .asset_type import AssetType, AssetCategory
from .status import Status, AssetStatus
from .email import Email  # Простой импорт

__all__ = [
    'Phone',
    'Coordinates',
    'PasswordHash',
    'DateRange',
    'Money',
    'InventoryNumber',
    'BatchId',
    'SerialNumber',
    'YearPeriod',
    'AssetType',
    'AssetCategory',
    'Status',
    'AssetStatus',
    'Email',
]