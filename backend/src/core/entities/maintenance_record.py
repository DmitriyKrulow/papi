# src/core/entities/maintenance_record.py
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

from backend.src.core.value_objects import Money


@dataclass
class MaintenanceRecord:
    """
    Сущность "Запись о техническом обслуживании".
    """
    id: int
    asset_id: int
    maintenance_date: date
    maintenance_type: str  # Плановое, Внеплановое, Капитальный ремонт, ТО
    
    # Поля со значениями по умолчанию
    description: Optional[str] = None
    cost: Optional[Money] = None
    
    performed_by: Optional[str] = None
    contractor: Optional[str] = None
    
    result: Optional[str] = None  # Выполнено, Требуется повтор, Неисправность
    next_maintenance_date: Optional[date] = None
    
    document_number: Optional[str] = None
    document_date: Optional[date] = None
    
    created_at: datetime = field(default_factory=datetime.now)
    created_by: Optional[int] = None
    
    def is_completed(self) -> bool:
        """Выполнено ли ТО"""
        return self.result == "Выполнено"
    
    def requires_repeat(self) -> bool:
        """Требуется ли повторное ТО"""
        return self.result == "Требуется повтор"
    
    def __str__(self) -> str:
        return f"MaintenanceRecord(id={self.id}, asset_id={self.asset_id}, date={self.maintenance_date})"