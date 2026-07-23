# src/core/entities/repair_request.py
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List
from enum import Enum

from backend.src.core.value_objects import Money


class RepairPriority(Enum):
    """Приоритет ремонта"""
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
    """
    Сущность "Заявка на ремонт".
    """
    id: int
    asset_id: int
    title: str
    description: str
    created_by: int  # ID сотрудника
    
    # Поля со значениями по умолчанию
    priority: RepairPriority = RepairPriority.MEDIUM
    status: RepairStatus = RepairStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.now)
    
    assigned_to: Optional[int] = None
    assigned_at: Optional[datetime] = None
    
    desired_completion_date: Optional[date] = None
    actual_completion_date: Optional[date] = None
    deadline: Optional[date] = None
    
    estimated_cost: Optional[Money] = None
    actual_cost: Optional[Money] = None
    
    completion_notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    
    maintenance_record_id: Optional[int] = None
    
    updated_at: datetime = field(default_factory=datetime.now)
    updated_by: Optional[int] = None
    
    def submit(self) -> None:
        """Подать заявку"""
        if self.status != RepairStatus.DRAFT:
            raise ValueError(f"Cannot submit request with status {self.status}")
        self.status = RepairStatus.SUBMITTED
        self.updated_at = datetime.now()
    
    def approve(self, assigned_to: int) -> None:
        """Одобрить заявку"""
        if self.status != RepairStatus.SUBMITTED:
            raise ValueError(f"Cannot approve request with status {self.status}")
        self.status = RepairStatus.APPROVED
        self.assigned_to = assigned_to
        self.assigned_at = datetime.now()
        self.updated_at = datetime.now()
    
    def start_work(self) -> None:
        """Начать работу над заявкой"""
        if self.status != RepairStatus.APPROVED:
            raise ValueError(f"Cannot start work on request with status {self.status}")
        self.status = RepairStatus.IN_PROGRESS
        self.updated_at = datetime.now()
    
    def complete(self, actual_cost: Optional[Money] = None, notes: Optional[str] = None) -> None:
        """Завершить заявку"""
        if self.status not in (RepairStatus.IN_PROGRESS, RepairStatus.APPROVED):
            raise ValueError(f"Cannot complete request with status {self.status}")
        self.status = RepairStatus.COMPLETED
        self.actual_completion_date = date.today()
        if actual_cost:
            self.actual_cost = actual_cost
        if notes:
            self.completion_notes = notes
        self.updated_at = datetime.now()
    
    def reject(self, reason: str) -> None:
        """Отклонить заявку"""
        if self.status in (RepairStatus.COMPLETED, RepairStatus.CANCELLED):
            raise ValueError(f"Cannot reject request with status {self.status}")
        self.status = RepairStatus.REJECTED
        self.rejection_reason = reason
        self.updated_at = datetime.now()
    
    def cancel(self) -> None:
        """Отменить заявку"""
        if self.status in (RepairStatus.COMPLETED, RepairStatus.REJECTED):
            raise ValueError(f"Cannot cancel request with status {self.status}")
        self.status = RepairStatus.CANCELLED
        self.updated_at = datetime.now()
    
    def is_active(self) -> bool:
        """Активна ли заявка"""
        return self.status not in (RepairStatus.COMPLETED, RepairStatus.REJECTED, RepairStatus.CANCELLED)
    
    def is_overdue(self) -> bool:
        """Просрочена ли заявка"""
        if not self.deadline:
            return False
        if self.status in (RepairStatus.COMPLETED, RepairStatus.REJECTED, RepairStatus.CANCELLED):
            return False
        return date.today() > self.deadline
    
    def get_status_display(self) -> str:
        """Читаемое название статуса"""
        statuses = {
            RepairStatus.DRAFT: "Черновик",
            RepairStatus.SUBMITTED: "Подана",
            RepairStatus.APPROVED: "Одобрена",
            RepairStatus.IN_PROGRESS: "В работе",
            RepairStatus.COMPLETED: "Выполнена",
            RepairStatus.REJECTED: "Отклонена",
            RepairStatus.CANCELLED: "Отменена",
        }
        return statuses.get(self.status, str(self.status))
    
    def get_priority_display(self) -> str:
        """Читаемое название приоритета"""
        priorities = {
            RepairPriority.LOW: "Низкий",
            RepairPriority.MEDIUM: "Средний",
            RepairPriority.HIGH: "Высокий",
            RepairPriority.URGENT: "Срочный",
        }
        return priorities.get(self.priority, str(self.priority))
    
    def __str__(self) -> str:
        return f"RepairRequest(id={self.id}, asset_id={self.asset_id}, title='{self.title}')"