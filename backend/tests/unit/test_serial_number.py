# backend/tests/unit/test_serial_number.py
"""Unit-тесты для SerialNumber Value Object (без БД)"""
import pytest
from src.core.value_objects.serial_number import SerialNumber


class TestSerialNumberCreation:
    """Тесты создания SerialNumber"""

    def test_valid_creation(self):
        """Создание валидного SerialNumber"""
        sn = SerialNumber(123, 3)
        assert sn.value == 123
        assert sn.digits == 3

    def test_zero_value(self):
        """Нулевое значение допустимо"""
        sn = SerialNumber(0, 5)
        assert sn.value == 0
        assert str(sn) == "00000"

    def test_large_value(self):
        """Большое значение"""
        sn = SerialNumber(999999999, 9)
        assert sn.value == 999999999

    def test_negative_value_raises(self):
        """Отрицательное значение должно вызывать ошибку"""
        with pytest.raises(ValueError, match="cannot be negative"):
            SerialNumber(-1, 3)

    def test_zero_digits_raises(self):
        """Нулевое количество цифр должно вызывать ошибку"""
        with pytest.raises(ValueError, match="Digits must be positive"):
            SerialNumber(123, 0)

    def test_negative_digits_raises(self):
        """Отрицательное количество цифр"""
        with pytest.raises(ValueError, match="Digits must be positive"):
            SerialNumber(123, -1)


class TestSerialNumberFromStrings:
    """Тесты создания из строк"""

    def test_from_string_valid(self):
        """Создание из валидной строки"""
        sn = SerialNumber.from_string("12345")
        assert sn.value == 12345
        assert sn.digits == 5

    def test_from_string_empty_raises(self):
        """Пустая строка"""
        with pytest.raises(ValueError, match="Invalid serial number"):
            SerialNumber.from_string("")

    def test_from_string_non_numeric_raises(self):
        """Не-числовая строка"""
        with pytest.raises(ValueError, match="Invalid serial number"):
            SerialNumber.from_string("abc123")

    def test_create_allow_null_with_value(self):
        """Создание с значением"""
        sn = SerialNumber.create_allow_null("12345")
        assert sn is not None
        assert sn.value == 12345

    def test_create_allow_null_with_none(self):
        """Создание с None"""
        sn = SerialNumber.create_allow_null(None)
        assert sn is None

    def test_create_allow_null_with_empty_string(self):
        """Создание с пустой строкой"""
        sn = SerialNumber.create_allow_null("")
        assert sn is None

    def test_create_allow_null_with_whitespace(self):
        """Создание с пробельной строкой"""
        sn = SerialNumber.create_allow_null("   ")
        assert sn is None

    def test_create_allow_null_invalid(self):
        """Создание с невалидной строкой возвращает None"""
        sn = SerialNumber.create_allow_null("abc")
        assert sn is None


class TestSerialNumberFormatting:
    """Тесты форматирования"""

    def test_format_with_padding(self):
        """Форматирование с заполнением"""
        sn = SerialNumber(42, 5)
        assert sn.format_with_padding() == "00042"

    def test_format_no_padding_needed(self):
        """Форматирование без дополнения"""
        sn = SerialNumber(123, 3)
        assert sn.format_with_padding() == "123"

    def test_str_representation(self):
        """Строковое представление"""
        sn = SerialNumber(42, 5)
        assert str(sn) == "00042"

    def test_repr_contains_values(self):
        """Repr должен содержать значения"""
        sn = SerialNumber(42, 5)
        assert "value=42" in repr(sn)
        assert "digits=5" in repr(sn)


class TestSerialNumberOperations:
    """Тесты операций"""

    def test_increment(self):
        """Инкремент"""
        sn = SerialNumber(99, 3)
        incremented = sn.increment()
        assert incremented.value == 100
        assert incremented.digits == 3

    def test_increment_with_padding(self):
        """Инкремент с сохранением форматирования"""
        sn = SerialNumber(999, 4)
        incremented = sn.increment()
        assert incremented.value == 1000
        assert str(incremented) == "1000"

    def test_frozen_dataclass(self):
        """SerialNumber должен быть неизменяемым"""
        sn = SerialNumber(123, 3)
        with pytest.raises(Exception):
            sn.value = 456
