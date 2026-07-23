# src/core/value_objects/year_period.py
from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(frozen=True)
class YearPeriod:
    """
    Годовой период (для учета и амортизации).
    """
    year: int
    
    def __post_init__(self) -> None:
        if not (1900 <= self.year <= 2100):
            raise ValueError(f"Invalid year: {self.year}")
    
    @classmethod
    def current(cls) -> 'YearPeriod':
        """Текущий год"""
        return cls(date.today().year)
    
    @classmethod
    def from_inventory_number(cls, value: str) -> Optional['YearPeriod']:
        """
        Извлекает год из инвентарного номера.
        """
        # Ищем 4 цифры подряд, которые похожи на год (20xx)
        import re
        matches = re.findall(r'(20\d{2})', value)
        if matches:
            try:
                year = int(matches[0])
                return cls(year)
            except ValueError:
                pass
        return None
    
    @property
    def decade(self) -> int:
        """Десятилетие (2020-е, 2030-е)"""
        return (self.year // 10) * 10
    
    @property
    def is_leap(self) -> bool:
        """Високосный год?"""
        return (self.year % 4 == 0 and self.year % 100 != 0) or (self.year % 400 == 0)
    
    def next(self) -> 'YearPeriod':
        """Следующий год"""
        return YearPeriod(self.year + 1)
    
    def previous(self) -> 'YearPeriod':
        """Предыдущий год"""
        return YearPeriod(self.year - 1)
    
    def __str__(self) -> str:
        return str(self.year)
    
    def __repr__(self) -> str:
        return f"YearPeriod({self.year})"