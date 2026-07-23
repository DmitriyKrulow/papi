# src/core/exceptions/repair.py
from backend.src.core.exceptions.base import (
    DomainException,
    NotFoundException,
    ValidationException,
    InvalidStateException,
    BusinessRuleViolationException,
)


class RepairRequestNotFoundException(NotFoundException):
    """Заявка на ремонт не найдена"""
    def __init__(self, request_id: int):
        super().__init__("RepairRequest", request_id)


class RepairRequestInvalidStateException(InvalidStateException):
    """Недопустимый статус заявки"""
    def __init__(self, request_id: int, current_state: str, expected_state: str):
        super().__init__("RepairRequest", current_state, expected_state)
        self.details['request_id'] = request_id


class RepairRequestAlreadyAssignedException(DomainException):
    """Заявка уже назначена другому сотруднику"""
    def __init__(self, request_id: int, assigned_to: int):
        super().__init__(
            message=f"Repair request {request_id} already assigned to {assigned_to}",
            code="REPAIR_ALREADY_ASSIGNED",
            details={'request_id': request_id, 'assigned_to': assigned_to},
        )


class RepairRequestOverdueException(BusinessRuleViolationException):
    """Заявка просрочена"""
    def __init__(self, request_id: int, deadline: str):
        super().__init__(
            rule="REPAIR_DEADLINE",
            message=f"Repair request {request_id} is overdue. Deadline: {deadline}",
        )