# src/core/exceptions/base.py
from typing import Optional, Any, Dict


class DomainException(Exception):
    """
    ??????? ????? ??? ???? ??????-??????????.
    """
    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """??????????? ?????????? ? ??????? ??? API ??????"""
        return {
            'error': self.code,
            'message': self.message,
            'details': self.details,
        }


class NotFoundException(DomainException):
    """??????????: ???????? ?? ???????"""
    def __init__(self, entity_name: str, entity_id: Any):
        super().__init__(
            message=f"{entity_name} with id '{entity_id}' not found",
            code="NOT_FOUND",
            details={'entity': entity_name, 'id': str(entity_id)},
        )


class ValidationException(DomainException):
    """??????????: ?????? ?????????"""
    def __init__(self, message: str, field: Optional[str] = None):
        details = {'field': field} if field else {}
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details=details,
        )


class DuplicateException(DomainException):
    """??????????: ???????? ????????"""
    def __init__(self, entity_name: str, field: str, value: Any):
        super().__init__(
            message=f"{entity_name} with {field} '{value}' already exists",
            code="DUPLICATE_ENTITY",
            details={'entity': entity_name, 'field': field, 'value': str(value)},
        )


class PermissionDeniedException(DomainException):
    """??????????: ???????????? ????"""
    def __init__(self, action: str, resource: str):
        super().__init__(
            message=f"Permission denied for action '{action}' on '{resource}'",
            code="PERMISSION_DENIED",
            details={'action': action, 'resource': resource},
        )


class BusinessRuleViolationException(DomainException):
    """??????????: ????????? ??????-???????"""
    def __init__(self, rule: str, message: str):
        super().__init__(
            message=message,
            code="BUSINESS_RULE_VIOLATION",
            details={'rule': rule},
        )


class InvalidStateException(DomainException):
    """??????????: ???????????? ????????? ????????"""
    def __init__(self, entity: str, current_state: str, expected_state: str):
        super().__init__(
            message=f"Cannot perform operation on {entity} in state '{current_state}'. Expected: {expected_state}",
            code="INVALID_STATE",
            details={
                'entity': entity,
                'current_state': current_state,
                'expected_state': expected_state,
            },
        )

