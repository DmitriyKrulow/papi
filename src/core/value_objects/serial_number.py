# src/core/value_objects/serial_number.py
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SerialNumber:
    """
    Порядковый номер единицы в партии.
    """
    value: int  # 1-9999999999
    digits: int  # Количество знаков (для форматирования)
    
    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("Serial number cannot be negative")
        if self.digits < 1:
            raise ValueError("Digits must be positive")
    
    @classmethod
    def from_string(cls, value: str) -> 'SerialNumber':
        """Создает из строки (автоматически определяет длину)"""
        if not value.isdigit():
            raise ValueError(f"Invalid serial number: {value}")
        return cls(int(value), len(value))
    
    @classmethod
    def create_allow_null(cls, value: Optional[str]) -> Optional['SerialNumber']:
        """Безопасное создание: возвращает None для пустых значений"""
        if not value or not value.strip():
            return None
        try:
            return cls.from_string(value)
        except ValueError:
            return None
    
    def format_with_padding(self) -> str:
        """Форматирует с ведущими нулями"""
        return str(self.value).zfill(self.digits)
    
    def increment(self) -> 'SerialNumber':
        """Увеличивает серийный номер на 1"""
        return SerialNumber(self.value + 1, self.digits)
    
    def __str__(self) -> str:
        return self.format_with_padding()
    
    def __repr__(self) -> str:
        return f"SerialNumber(value={self.value}, digits={self.digits})"