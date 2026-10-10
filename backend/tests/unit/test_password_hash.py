# backend/tests/unit/test_password_hash.py
"""Unit-тесты для PasswordHash (без БД)"""
import pytest
from src.core.value_objects.password_hash import PasswordHash


class TestPasswordHashCreation:
    """Тесты создания хешей паролей"""

    def test_create_from_plain_password(self):
        """Создание хеша из обычного пароля"""
        ph = PasswordHash.from_plain_password("secure_password_123")
        assert ph is not None
        assert ph.hash_value is not None
        assert len(ph.hash_value) > 0

    def test_create_from_plain_password_empty_raises(self):
        """Пустой пароль должен создаваться (без валидации на уровне VO)"""
        ph = PasswordHash.from_plain_password("")
        assert ph is not None

    def test_random_hash(self):
        """Создание случайного хеша"""
        ph1 = PasswordHash.random()
        ph2 = PasswordHash.random()
        assert ph1.hash_value != ph2.hash_value

    def test_from_hash_string(self):
        """Создание хеша из строки"""
        original = PasswordHash.from_plain_password("test_password")
        restored = PasswordHash.from_hash_string(original.hash_value)
        assert restored.hash_value == original.hash_value

    def test_from_hash_string_none_raises(self):
        """None должен вызывать ValueError"""
        with pytest.raises(ValueError, match="cannot be None"):
            PasswordHash.from_hash_string(None)


class TestPasswordHashVerification:
    """Тесты верификации паролей"""

    def test_correct_password_verifies(self):
        """Правильный пароль должен верифицироваться"""
        ph = PasswordHash.from_plain_password("my_secret_password")
        assert ph.verify("my_secret_password") is True

    def test_incorrect_password_fails(self):
        """Неправильный пароль должен отклоняться"""
        ph = PasswordHash.from_plain_password("my_secret_password")
        assert ph.verify("wrong_password") is False

    def test_case_sensitive_password(self):
        """Пароль должен быть чувствителен к регистру"""
        ph = PasswordHash.from_plain_password("Password123")
        assert ph.verify("Password123") is True
        assert ph.verify("password123") is False
        assert ph.verify("PASSWORD123") is False

    def test_special_characters_in_password(self):
        """Пароль с спецсимволами должен работать"""
        ph = PasswordHash.from_plain_password("p@ss!w0rd#$%")
        assert ph.verify("p@ss!w0rd#$%") is True

    def test_unicode_password(self):
        """Пароль с unicode-символами должен работать"""
        ph = PasswordHash.from_plain_password("пароль123")
        assert ph.verify("пароль123") is True

    def test_long_password(self):
        """Длинный пароль должен работать"""
        long_pw = "a" * 1000
        ph = PasswordHash.from_plain_password(long_pw)
        assert ph.verify(long_pw) is True


class TestPasswordHashProperties:
    """Тесты свойств PasswordHash"""

    def test_is_empty_true(self):
        """Пустой хеш должен определяться"""
        ph = PasswordHash("$$")
        assert ph.is_empty is True

    def test_is_empty_false(self):
        """Непустой хеш не должен быть empty"""
        ph = PasswordHash.from_plain_password("test")
        assert ph.is_empty is False

    def test_str_representation(self):
        """Строковое представление должно возвращать хеш"""
        ph = PasswordHash.from_plain_password("test")
        assert str(ph) == ph.hash_value

    def test_repr_contains_class_name(self):
        """Repr должен содержать имя класса"""
        ph = PasswordHash.from_plain_password("test")
        assert "PasswordHash" in repr(ph)

    def test_frozen_dataclass(self):
        """Dataclass должен быть frozen (неизменяемый)"""
        ph = PasswordHash.from_plain_password("test")
        with pytest.raises(Exception):
            ph.hash_value = "new_value"


class TestPasswordHashFormat:
    """Тесты формата хеша"""

    def test_invalid_hash_format_raises(self):
        """Неверный формат хеша должен вызывать ошибку"""
        with pytest.raises(ValueError, match="Invalid hash format"):
            PasswordHash("invalid_format")

    def test_invalid_hash_format_missing_parts(self):
        """Хеш с неправильным количеством частей должен отклоняться"""
        with pytest.raises(ValueError, match="Invalid hash format"):
            PasswordHash("salt$hash")

    def test_empty_salt_raises(self):
        """Пустой salt должен вызывать ошибку"""
        with pytest.raises(ValueError, match="Salt cannot be empty"):
            PasswordHash("$100000$hash")

    def test_non_numeric_iterations_raises(self):
        """Нечисловые итерации должны вызывать ошибку"""
        with pytest.raises(ValueError, match="Iterations must be a number"):
            PasswordHash("salt$abc$hash")
