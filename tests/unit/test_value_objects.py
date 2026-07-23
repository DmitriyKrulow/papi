# tests/unit/test_value_objects.py
import pytest
from backend.src.core.value_objects import Email, InventoryNumber, PasswordHash


class TestEmail:
    """Тесты value object Email"""

    def test_valid_email(self):
        """Валидный email"""
        email = Email("user@example.com")
        assert email.value == "user@example.com"

    def test_invalid_email_raises_error(self):
        """Невалидный email"""
        with pytest.raises(ValueError):
            Email("invalid-email")

    def test_empty_email_raises_error(self):
        """Пустой email"""
        with pytest.raises(ValueError):
            Email("")


class TestInventoryNumber:
    """Тесты value object InventoryNumber"""

    def test_valid_inventory_number(self):
        """Валидный инвентарный номер"""
        inv_num = InventoryNumber("IN-001")
        assert inv_num.value == "IN-001"

    def test_empty_inventory_number_raises_error(self):
        """Пустой инвентарный номер"""
        with pytest.raises(ValueError):
            InventoryNumber("")

    def test_long_inventory_number(self):
        """Длинный инвентарный номер"""
        long_num = "IN-" + "A" * 50
        inv_num = InventoryNumber(long_num)
        assert len(inv_num.value) <= 50


class TestPasswordHash:
    """Тесты value object PasswordHash"""

    def test_valid_password_hash(self):
        """Валидный хэш пароля"""
        pwd_hash = PasswordHash("hashed_password_123")
        assert pwd_hash.value == "hashed_password_123"

    def test_empty_password_hash_raises_error(self):
        """Пустой хэш пароля"""
        with pytest.raises(ValueError):
            PasswordHash("")
