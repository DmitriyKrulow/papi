# src/core/entities/movement_record.py
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

from src.core.value_objects import Coordinates


@dataclass
class MovementRecord:
    """
    Сущность "Запись о перемещении актива".
    """
    id: int
    asset_id: int
    movement_date: date
    
    # Поля со значениями по умолчанию
    from_department_id: Optional[int] = None
    from_department_name: Optional[str] = None
    from_location: Optional[str] = None
    from_coordinates: Optional[Coordinates] = None
    
    to_department_id: Optional[int] = None
    to_department_name: Optional[str] = None
    to_location: Optional[str] = None
    to_coordinates: Optional[Coordinates] = None
    
    from_responsible_id: Optional[int] = None
    to_responsible_id: Optional[int] = None
    
    reason: Optional[str] = None
    document_number: Optional[str] = None
    
    created_at: datetime = field(default_factory=datetime.now)
    created_by: Optional[int] = None
    
    def is_completed(self) -> bool:
        """Завершено ли перемещение"""
        return self.to_department_id is not None
    
    def __str__(self) -> str:
        return f"MovementRecord(id={self.id}, asset_id={self.asset_id}, date={self.movement_date})"