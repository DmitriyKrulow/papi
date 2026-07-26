from datetime import date
from decimal import Decimal
from typing import Optional
from dataclasses import dataclass

from src.core.value_objects import (
    Money,
    Email,
    Phone,
    Status,
    AssetStatus,
    InventoryNumber,
    SerialNumber,
    DateRange,
    Coordinates,
    BatchId,
    AssetType,
)


@dataclass
class Asset:
    """Asset entity placeholder"""
    id: Optional[int] = None
    name: str = ""
    inventory_number: str = ""
    model: str = ""
    manufacturer_name: str = ""
    purchase_price: Optional[Decimal] = None
    current_value: Optional[Decimal] = None
    status: str = "active"
    department_code: str = ""
    responsible_person: str = ""
    location_address: str = ""
    purchase_date: Optional[date] = None
    commissioning_date: Optional[date] = None
