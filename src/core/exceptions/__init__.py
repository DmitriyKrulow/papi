# src/core/exceptions/__init__.py
from .base import (
    DomainException,
    NotFoundException,
    ValidationException,
    DuplicateException,
    PermissionDeniedException,
    BusinessRuleViolationException,
    InvalidStateException,
)

from .asset import (
    AssetNotFoundException,
    AssetAlreadyExistsException,
    AssetValidationException,
    AssetNotAvailableException,
    AssetUnderWarrantyException,
    AssetDepreciationException,
)

from .user import (
    UserNotFoundException,
    UserByEmailNotFoundException,
    UserAlreadyExistsException,
    InvalidCredentialsException,
    UserInactiveException,
    PasswordTooWeakException,
    UserPermissionDeniedException,
)

from .repair import (
    RepairRequestNotFoundException,
    RepairRequestInvalidStateException,
    RepairRequestAlreadyAssignedException,
    RepairRequestOverdueException,
)

from .inventory import (
    InventoryCheckNotFoundException,
    InventoryCheckInvalidStateException,
    InventoryCheckAlreadyCompletedException,
    InventoryMismatchException,
)

from .document import (
    DocumentNotFoundException,
    DocumentUploadException,
    DocumentTooLargeException,
    InvalidFileTypeException,
)

__all__ = [
    # Base
    'DomainException',
    'NotFoundException',
    'ValidationException',
    'DuplicateException',
    'PermissionDeniedException',
    'BusinessRuleViolationException',
    'InvalidStateException',
    
    # Asset
    'AssetNotFoundException',
    'AssetAlreadyExistsException',
    'AssetValidationException',
    'AssetNotAvailableException',
    'AssetUnderWarrantyException',
    'AssetDepreciationException',
    
    # User
    'UserNotFoundException',
    'UserByEmailNotFoundException',
    'UserAlreadyExistsException',
    'InvalidCredentialsException',
    'UserInactiveException',
    'PasswordTooWeakException',
    'UserPermissionDeniedException',
    
    # Repair
    'RepairRequestNotFoundException',
    'RepairRequestInvalidStateException',
    'RepairRequestAlreadyAssignedException',
    'RepairRequestOverdueException',
    
    # Inventory
    'InventoryCheckNotFoundException',
    'InventoryCheckInvalidStateException',
    'InventoryCheckAlreadyCompletedException',
    'InventoryMismatchException',
    
    # Document
    'DocumentNotFoundException',
    'DocumentUploadException',
    'DocumentTooLargeException',
    'InvalidFileTypeException',
]