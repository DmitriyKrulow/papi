# src/core/exceptions/asset.py
from src.core.exceptions.base import (
    DomainException,
    NotFoundException,
    ValidationException,
    DuplicateException,
    BusinessRuleViolationException,
)


class AssetNotFoundException(NotFoundException):
    """Актив не найден"""
    def __init__(self, asset_id: int):
        super().__init__("Asset", asset_id)


class AssetAlreadyExistsException(DuplicateException):
    """Актив с таким инвентарным номером уже существует"""
    def __init__(self, inventory_number: str):
        super().__init__("Asset", "inventory_number", inventory_number)


class AssetValidationException(ValidationException):
    """Ошибка валидации актива"""
    def __init__(self, message: str, field: str):
        super().__init__(message, field)


class AssetNotAvailableException(BusinessRuleViolationException):
    """Актив недоступен для операции"""
    def __init__(self, asset_id: int, reason: str):
        super().__init__(
            rule="ASSET_AVAILABILITY",
            message=f"Asset {asset_id} is not available: {reason}",
        )


class AssetUnderWarrantyException(BusinessRuleViolationException):
    """Актив под гарантией - нельзя списать/ремонтировать без разрешения"""
    def __init__(self, asset_id: int, warranty_expiry: str):
        super().__init__(
            rule="ASSET_WARRANTY",
            message=f"Asset {asset_id} is under warranty until {warranty_expiry}",
        )


class AssetDepreciationException(BusinessRuleViolationException):
    """Ошибка при расчете амортизации"""
    def __init__(self, asset_id: int, reason: str):
        super().__init__(
            rule="ASSET_DEPRECIATION",
            message=f"Depreciation error for asset {asset_id}: {reason}",
        )