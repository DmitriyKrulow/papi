# src/core/exceptions/inventory.py
from backend.src.core.exceptions.base import (
    DomainException,
    NotFoundException,
    ValidationException,
    InvalidStateException,
)


class InventoryCheckNotFoundException(NotFoundException):
    """Инвентаризация не найдена"""
    def __init__(self, check_id: int):
        super().__init__("InventoryCheck", check_id)


class InventoryCheckInvalidStateException(InvalidStateException):
    """Недопустимый статус инвентаризации"""
    def __init__(self, check_id: int, current_state: str, expected_state: str):
        super().__init__("InventoryCheck", current_state, expected_state)
        self.details['check_id'] = check_id


class InventoryCheckAlreadyCompletedException(DomainException):
    """Инвентаризация уже завершена"""
    def __init__(self, check_id: int):
        super().__init__(
            message=f"Inventory check {check_id} is already completed",
            code="INVENTORY_ALREADY_COMPLETED",
            details={'check_id': check_id},
        )


class InventoryMismatchException(DomainException):
    """Расхождение при инвентаризации"""
    def __init__(self, asset_id: int, expected: str, actual: str):
        super().__init__(
            message=f"Inventory mismatch for asset {asset_id}: expected {expected}, found {actual}",
            code="INVENTORY_MISMATCH",
            details={'asset_id': asset_id, 'expected': expected, 'actual': actual},
        )