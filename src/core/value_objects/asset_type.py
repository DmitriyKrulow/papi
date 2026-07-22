# src/core/value_objects/asset_type.py
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class AssetCategory(Enum):
    """Категории активов"""
    EQUIPMENT = "equipment"       # Оборудование
    VEHICLE = "vehicle"           # Транспорт
    BUILDING = "building"         # Здания
    INVENTORY = "inventory"       # Товарно-материальные ценности
    OFFICE = "office"             # Офисная техника
    SPECIAL = "special"           # Специальное оборудование
    UNKNOWN = "unknown"           # Неизвестно


@dataclass(frozen=True)
class AssetType:
    """
    Тип актива (на основе кода или префикса).
    """
    code: str
    category: AssetCategory
    description: str
    
    @classmethod
    def from_inventory_prefix(cls, prefix: Optional[str]) -> 'AssetType':
        """Определяет тип актива по префиксу инвентарного номера"""
        if prefix is None:
            return cls('UNKNOWN', AssetCategory.UNKNOWN, "Неизвестный тип")
        
        if prefix in ('С', 'C'):
            return cls('C', AssetCategory.SPECIAL, "Специальное оборудование")
        elif prefix in ('Э', 'E'):
            return cls('E', AssetCategory.EQUIPMENT, "Электрооборудование")
        elif prefix.isdigit():
            # Префикс может быть 1-3 цифры
            code = prefix[:3] if len(prefix) >= 3 else prefix
            try:
                code_int = int(code)
                if 20 <= code_int <= 29:  # 023, 0232 и т.д.
                    return cls(code, AssetCategory.VEHICLE, "Транспортные средства")
                elif 40 <= code_int <= 49:  # 041, 043 и т.д.
                    return cls(code, AssetCategory.EQUIPMENT, "Промышленное оборудование")
                elif 50 <= code_int <= 59:  # 053 и т.д.
                    return cls(code, AssetCategory.INVENTORY, "Производственные запасы")
                elif 30 <= code_int <= 39:  # 031, 033 и т.д.
                    return cls(code, AssetCategory.BUILDING, "Здания и сооружения")
            except ValueError:
                pass
        
        return cls('UNKNOWN', AssetCategory.UNKNOWN, "Неизвестный тип")
    
    def __str__(self) -> str:
        return f"{self.code} - {self.description}"
    
    def __repr__(self) -> str:
        return f"AssetType(code='{self.code}', category={self.category}, description='{self.description}')"