from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from dataclasses import dataclass, field
from enum import Enum

from src.core.value_objects import Money


class RepairPriority(Enum):
    """Приоритет заявки на ремонт"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class RepairStatus(Enum):
    """Статус заявки на ремонт"""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


@dataclass
class RepairRequest:
    """Сущность заявки на ремонт"""
    id: Optional[int] = None
    asset_id: Optional[int] = None
    title: str = ""
    description: str = ""
    
    priority: RepairPriority = RepairPriority.MEDIUM
    status: RepairStatus = RepairStatus.DRAFT
    
    created_by: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    assigned_to: Optional[int] = None
    assigned_at: Optional[datetime] = None
    
    desired_completion_date: Optional[date] = None
    actual_completion_date: Optional[date] = None
    deadline: Optional[date] = None
    
    estimated_cost: Optional[Decimal] = None
    actual_cost: Optional[Decimal] = None
    
    completion_notes: str = ""
    rejection_reason: str = ""
    
    maintenance_record_id: Optional[int] = None
    
    updated_at: datetime = field(default_factory=datetime.now)
    updated_by: Optional[int] = None
    
    asset_name: Optional[str] = None
    creator_name: Optional[str] = None
    assignee_name: Optional[str] = None
    inventory_number: Optional[str] = None
    
    def submit(self) -> None:
        """Отправить заявку на рассмотрение"""
        if self.status == RepairStatus.DRAFT:
            self.status = RepairStatus.SUBMITTED
    
    def approve(self, assigned_to: int) -> None:
        """Утвердить заявку и назначить исполнителя"""
        if self.status in (RepairStatus.SUBMITTED, RepairStatus.DRAFT):
            self.status = RepairStatus.APPROVED
            self.assigned_to = assigned_to
            self.assigned_at = datetime.now()
    
    def reject(self, reason: str) -> None:
        """Отклонить заявку"""
        if self.status == RepairStatus.SUBMITTED:
            self.status = RepairStatus.REJECTED
            self.rejection_reason = reason
    
    def start(self) -> None:
        """Начать выполнение"""
        if self.status == RepairStatus.APPROVED:
            self.status = RepairStatus.IN_PROGRESS
    
    def complete(self, actual_cost: Decimal, completion_notes: str) -> None:
        """Завершить выполнение"""
        if self.status == RepairStatus.IN_PROGRESS:
            self.status = RepairStatus.COMPLETED
            self.actual_completion_date = date.today()
            self.actual_cost = actual_cost
            self.completion_notes = completion_notes
    
    def cancel(self) -> None:
        """Отменить заявку"""
        if self.status in (RepairStatus.DRAFT, RepairStatus.SUBMITTED, RepairStatus.APPROVED):
            self.status = RepairStatus.CANCELLED
    
    def update_priority(self, priority: RepairPriority) -> None:
        """Обновить приоритет"""
        self.priority = priority
        self.updated_at = datetime.now()
    
    def is_admin_or_responsible(self, user_role: str, user_id: int) -> bool:
        """Проверка, является ли пользователь администратором или ответственным"""
        return user_role in ("admin", "responsible")
