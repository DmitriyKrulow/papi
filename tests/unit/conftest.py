# tests/unit/conftest.py
import pytest
from backend.src.core.value_objects import Email, InventoryNumber, PasswordHash


@pytest.fixture
def sample_email():
    """Фикстура для валидного email"""
    return Email("test@example.com")


@pytest.fixture
def sample_inventory_number():
    """Фикстура для валидного инвентарного номера"""
    return InventoryNumber("IN-001")


@pytest.fixture
def sample_password_hash():
    """Фикстура для хэша пароля"""
    return PasswordHash("hashed_password_123")
