# src/core/entities/employee.py
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

from backend.src.core.value_objects import Phone, Email


@dataclass
class Employee:
    """Сущность "Сотрудник" """
    id: int
    department_id: int
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    
    # Контакты
    phone: Optional[Phone] = None
    email: Optional[Email] = None
    
    # Должность
    position: Optional[str] = None
    position_code: Optional[str] = None
    
    # Кадровые данные
    employee_number: Optional[str] = None  # Табельный номер
    hire_date: Optional[date] = None
    termination_date: Optional[date] = None
    
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def get_full_name(self) -> str:
        """Полное имя"""
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return " ".join(parts)
    
    def get_short_name(self) -> str:
        """Краткое имя (Иванов И.И.)"""
        result = self.last_name
        if self.first_name:
            result += f" {self.first_name[0]}."
        if self.middle_name:
            result += f" {self.middle_name[0]}."
        return result
    
    def is_employed(self) -> bool:
        """Работает ли сотрудник в данный момент"""
        if not self.is_active:
            return False
        if self.termination_date and self.termination_date <= date.today():
            return False
        return True
    
    def __str__(self) -> str:
        return f"Employee(id={self.id}, name='{self.get_full_name()}')"