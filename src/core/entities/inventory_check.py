# src/core/entities/inventory_check.py
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional, List


@dataclass
class InventoryCheck:
    """
    Сущность "Инвентаризация".
    """
    id: int
    name: str
    check_date: date
    
    # Поля со значениями по умолчанию
    department_id: Optional[int] = None
    
    total_checked: int = 0
    found: int = 0
    missing: int = 0
    surplus: int = 0
    
    status: str = "created"  # created, in_progress, completed, cancelled
    
    responsible_id: Optional[int] = None
    commission_members: List[int] = field(default_factory=list)
    
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    def get_summary(self) -> dict:
        """Сводка по инвентаризации"""
        return {
            'total': self.total_checked,
            'found': self.found,
            'missing': self.missing,
            'surplus': self.surplus,
            'accuracy': f"{(self.found / self.total_checked * 100):.1f}%" if self.total_checked > 0 else "0%",
        }
    
    def is_completed(self) -> bool:
        return self.status == "completed"
    
    def __str__(self) -> str:
        return f"InventoryCheck(id={self.id}, name='{self.name}', date={self.check_date})"