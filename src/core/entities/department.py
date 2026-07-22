# src/core/entities/department.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List

from src.core.value_objects import Phone, Email


@dataclass
class Department:
    """Сущность "Подразделение/Отдел" """
    id: int
    organization_id: int
    name: str
    code: str  # Код подразделения (например, DEPT-001)
    
    parent_id: Optional[int] = None  # Для иерархии
    head: Optional[str] = None       # Руководитель
    phone: Optional[Phone] = None
    email: Optional[Email] = None
    location: Optional[str] = None
    
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def get_full_path(self) -> str:
        """Возвращает полный путь подразделения"""
        # Здесь может быть логика получения родительских подразделений
        return self.name
    
    def __str__(self) -> str:
        return f"Department(id={self.id}, name='{self.name}', code='{self.code}')"