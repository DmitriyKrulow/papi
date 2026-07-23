# tests/unit/test_user.py
import pytest
from backend.src.core.entities.user import User
from backend.src.core.value_objects import Email, PasswordHash


class TestUserEntity:
    """Тесты сущности User"""

    def test_create_user_with_valid_data(self):
        """Создание пользователя с валидными данными"""
        email = Email("ivanov@example.com")
        password_hash = PasswordHash("hashed_password_123")
        user = User(
            id=1,
            email=email,
            username="ivanov",
            password_hash=password_hash,
            full_name="Иванов Иван",
            is_active=True
        )
        
        assert user.id == 1
        assert user.email.value == "ivanov@example.com"
        assert user.username == "ivanov"
        assert user.full_name == "Иванов Иван"

    def test_user_with_optional_fields(self):
        """Пользователь с дополнительными полями"""
        email = Email("petrov@example.com")
        password_hash = PasswordHash("hashed_password_456")
        user = User(
            id=2,
            email=email,
            username="petrov",
            password_hash=password_hash,
            full_name="Петров Петр",
            phone="+7 (999) 123-45-67",
            department="IT",
            role="admin",
            is_active=True
        )
        
        assert user.phone == "+7 (999) 123-45-67"
        assert user.department == "IT"
        assert user.role == "admin"

    def test_user_inactive(self):
        """Неактивный пользователь"""
        email = Email("sidorov@example.com")
        password_hash = PasswordHash("hashed_password_789")
        user = User(
            id=3,
            email=email,
            username="sidorov",
            password_hash=password_hash,
            full_name="Сидоров Сидор",
            is_active=False
        )
        
        assert user.is_active is False

    def test_user_invalid_email(self):
        """Пользователь с невалидной почтой"""
        with pytest.raises(ValueError):
            Email("invalid-email")

    def test_user_str_representation(self):
        """Строковое представление пользователя"""
        email = Email("test@example.com")
        password_hash = PasswordHash("hashed_password")
        user = User(
            id=4,
            email=email,
            username="testuser",
            password_hash=password_hash,
            full_name="Тестовый Пользователь",
            is_active=True
        )
        
        assert "testuser" in str(user)
        assert "Тестовый Пользователь" in str(user)
