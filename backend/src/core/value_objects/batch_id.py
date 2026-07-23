# src/core/value_objects/batch_id.py
from dataclasses import dataclass
import re
from typing import Optional

@dataclass(frozen=True)
class BatchId:
    """
    Идентификатор партии/серии.
    Извлекается из инвентарного номера.
    """
    value: str  # 16 цифр
    
    _PATTERN = re.compile(r'^\d{16}$')
    
    def __post_init__(self):
        if not self._PATTERN.match(self.value):
            raise ValueError(f"Batch ID must be 16 digits, got {self.value}")
    
    @property
    def year(self) -> int:
        """Год из номера партии"""
        return int(self.value[:4])
    
    @property
    def plant_code(self) -> str:
        """Код завода/производителя (первые 3 цифры)"""
        return self.value[:3]
    
    @property
    def product_code(self) -> str:
        """Код продукции (следующие 3 цифры)"""
        return self.value[3:6]
    
    @property
    def batch_number(self) -> int:
        """Номер партии (последние 10 цифр)"""
        return int(self.value[6:])
    
    def __str__(self):
        return self.value