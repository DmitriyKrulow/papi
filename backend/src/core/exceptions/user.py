# src/core/exceptions/user.py
from backend.src.core.exceptions.base import (
    DomainException,
    NotFoundException,
    ValidationException,
    DuplicateException,
    PermissionDeniedException,
)


class UserNotFoundException(NotFoundException):
    """Пользователь не найден"""
    def __init__(self, user_id: int):
        super().__init__("User", user_id)


class UserByEmailNotFoundException(NotFoundException):
    """Пользователь с таким email не найден"""
    def __init__(self, email: str):
        super().__init__("User with email", email)


class UserAlreadyExistsException(DuplicateException):
    """Пользователь с таким email уже существует"""
    def __init__(self, email: str):
        super().__init__("User", "email", email)


class InvalidCredentialsException(DomainException):
    """Неверные учетные данные"""
    def __init__(self):
        super().__init__(
            message="Invalid email or password",
            code="INVALID_CREDENTIALS",
        )


class UserInactiveException(DomainException):
    """Пользователь неактивен"""
    def __init__(self, user_id: int):
        super().__init__(
            message=f"User {user_id} is inactive",
            code="USER_INACTIVE",
            details={'user_id': user_id},
        )


class PasswordTooWeakException(ValidationException):
    """Пароль слишком слабый"""
    def __init__(self, reason: str):
        super().__init__(
            message=f"Password is too weak: {reason}",
            field="password",
        )


class UserPermissionDeniedException(PermissionDeniedException):
    """Пользователю запрещен доступ"""
    def __init__(self, user_id: int, action: str, resource: str):
        super().__init__(action, resource)
        self.details['user_id'] = user_id