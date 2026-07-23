# src/core/entities/asset_category.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class AssetCategory:
    """Сущность "Категория активов" """
    id: int
    name: str
    code: str  # Код категории
    
    parent_id: Optional[int] = None
    description: Optional[str] = None
    
    # Нормы амортизации
    default_depreciation_rate: Optional[float] = None  # в процентах
    useful_life_years: Optional[int] = None  # Срок полезного использования
    
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def get_full_path(self) -> List[str]:
        """Возвращает полный путь категории"""
        # Здесь логика получения родительских категорий
        return [self.name]
    
    def __str__(self) -> str:
        return f"AssetCategory(id={self.id}, name='{self.name}', code='{self.code}')"