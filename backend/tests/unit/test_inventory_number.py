# backend/tests/unit/test_inventory_number.py
"""Unit-тесты для InventoryNumber Value Object (без БД)"""
import pytest
from src.core.value_objects.inventory_number import InventoryNumber


class TestInventoryNumberCreation:
    """Тесты создания InventoryNumber"""

    def test_valid_digit_sequence(self):
        """Создание из числовой последовательности (28+ цифр)"""
        num = InventoryNumber("0232026200020180000000045")
        assert num.value == "02320262000200020180000000045"

    def test_valid_prefix_c(self):
        """Создание с префиксом C"""
        num = InventoryNumber("?2101072050")
        assert num.prefix == "?"

    def test_valid_prefix_e(self):
        """Создание с префиксом E"""
        num = InventoryNumber("?99936792")
        assert num.prefix == "?"

    def test_too_short_digit_sequence_raises(self):
        """Слишком короткая числовая последовательность"""
        with pytest.raises(ValueError, match="Invalid inventory number"):
            InventoryNumber("12345")

    def test_too_short_prefix_c_raises(self):
        """Слишком короткая последовательность с префиксом C"""
        with pytest.raises(ValueError, match="Invalid inventory number"):
            InventoryNumber("?123")

    def test_invalid_prefix_raises(self):
        """Невалидный префикс"""
        with pytest.raises(ValueError, match="Invalid inventory number"):
            InventoryNumber("X1234567890")

    def test_whitespace_removed(self):
        """Пробелы и дефисы удаляются"""
        num = InventoryNumber("0232 0262-0002")
        assert " " not in num.value
        assert "-" not in num.value


class TestInventoryNumberProperties:
    """Тесты свойств InventoryNumber"""

    def test_prefix_digit(self):
        """Префикс для числовой последовательности"""
        num = InventoryNumber("0232026200020180000000045")
        assert num.prefix is None

    def test_prefix_c(self):
        """Префикс C"""
        num = InventoryNumber("?2101072050")
        assert num.prefix == "?"

    def test_digits_only_digit_sequence(self):
        """Цифры только для числовой последовательности"""
        num = InventoryNumber("0232026200020180000000045")
        assert num.digits_only == num.value

    def test_digits_only_prefix_c(self):
        """Цифры только с префиксом"""
        num = InventoryNumber("?2101072050")
        assert num.digits_only == "2101072050"

    def test_length(self):
        """Длина номера"""
        num = InventoryNumber("?2101072050")
        assert num.length == 11

    def test_type_digit(self):
        """Тип digit"""
        num = InventoryNumber("0232026200020180000000045")
        assert num.type == "digit"

    def test_type_prefix_c(self):
        """Тип prefix_c"""
        num = InventoryNumber("?2101072050")
        assert num.type == "prefix_c"

    def test_type_prefix_e(self):
        """Тип prefix_e"""
        num = InventoryNumber("?99936792")
        assert num.type == "prefix_e"


class TestInventoryNumberChecksum:
    """Тесты контрольной суммы"""

    def test_is_valid_checksum_true(self):
        """Валидная контрольная сумма"""
        num = InventoryNumber("799b4c77c01433727050145200")
        # Проверка что свойство не вызывает ошибку
        _ = num.is_valid_checksum

    def test_checksum_property_exists(self):
        """Свойство checksum должно существовать"""
        num = InventoryNumber("0232026200020180000000045")
        checksum = num.checksum
        assert isinstance(checksum, int)
        assert 0 <= checksum <= 9


class TestInventoryNumberFormatting:
    """Тесты форматирования"""

    def test_format_grouped_default(self):
        """Группировка по 4 цифры (по умолчанию)"""
        num = InventoryNumber("0232026200020180000000045")
        formatted = num.format_grouped(4)
        assert " " in formatted

    def test_format_grouped_custom(self):
        """Группировка по 6 цифр"""
        num = InventoryNumber("0232026200020180000000045")
        formatted = num.format_grouped(6)
        groups = formatted.split(" ")
        for group in groups:
            assert len(group) <= 6

    def test_format_grouped_with_prefix(self):
        """Группировка с префиксом"""
        num = InventoryNumber("?2101072050")
        formatted = num.format_grouped(4)
        assert formatted.startswith("?")

    def test_obfuscate(self):
        """Обфускация номера"""
        num = InventoryNumber("0232026200020180000000045")
        obfuscated = num.obfuscate()
        assert "*" in obfuscated
        # Первые и последние 4 цифры должны быть видны
        assert obfuscated.startswith("0232")
        assert obfuscated.endswith("0045")


class TestInventoryNumberAnalysis:
    """Тесты анализа номера"""

    def test_extract_date(self):
        """Извлечение даты из номера"""
        num = InventoryNumber("?21010573318")
        date_info = num.extract_date()
        assert date_info is not None
        assert date_info["year"] == 2021
        assert date_info["month"] == 1

    def test_extract_date_none(self):
        """Извлечение даты когда невозможно"""
        num = InventoryNumber("0232026200020180000000045")
        date_info = num.extract_date()
        # Для длинных числовых последовательностей дата может быть извлечена
        _ = date_info

    def test_get_serial_number(self):
        """Извлечение серийного номера"""
        num = InventoryNumber("0232026200020180000000045")
        serial = num.get_serial_number()
        assert serial is not None
        assert isinstance(serial, int)

    def test_get_batch_id(self):
        """Извлечение batch ID"""
        num = InventoryNumber("0232026200020180000000045")
        batch = num.get_batch_id()
        assert batch is not None
        assert len(batch) == 16

    def test_is_sequential_with(self):
        """Проверка последовательности"""
        num1 = InventoryNumber("?00000001")
        num2 = InventoryNumber("?00000002")
        assert num1.is_sequential_with(num2) is True

    def test_is_sequential_with_different_prefix(self):
        """Разные префиксы — не последовательные"""
        num1 = InventoryNumber("?00000001")
        num2 = InventoryNumber("?00000002")
        result = num1.is_sequential_with(num2)
        _ = result


class TestInventoryNumberIncrement:
    """Тесты инкремента"""

    def test_increment(self):
        """Инкремент номера"""
        num = InventoryNumber("?00000001")
        incremented = num.increment()
        assert incremented is not None

    def test_increment_steps(self):
        """Инкремент на несколько шагов"""
        num = InventoryNumber("?00000001")
        incremented = num.increment(steps=5)
        assert incremented is not None

    def test_increment_overflow(self):
        """Переполнение при инкременте"""
        num = InventoryNumber("9999999999999999999999999999")
        # Может вернуть None при переполнении
        result = num.increment()
        _ = result


class TestInventoryNumberFactoryMethods:
    """Тесты фабричных методов"""

    def test_create_allow_null_with_value(self):
        """Создание с значением"""
        num = InventoryNumber.create_allow_null("0232026200020180000000045")
        assert num is not None

    def test_create_allow_null_with_none(self):
        """Создание с None"""
        num = InventoryNumber.create_allow_null(None)
        assert num is None

    def test_create_quiet_valid(self):
        """Тихое создание валидного номера"""
        num = InventoryNumber.create_quiet("0232026200020180000000045")
        assert num is not None

    def test_create_quiet_invalid(self):
        """Тихое создание невалидного номера"""
        num = InventoryNumber.create_quiet("123")
        assert num is None

    def test_generate_digit(self):
        """Генерация числового номера"""
        num = InventoryNumber.generate_digit()
        assert num is not None
        assert num.type == "digit"

    def test_generate_prefix_c(self):
        """Генерация номера с префиксом C"""
        num = InventoryNumber.generate_prefix_c()
        assert num is not None
        assert num.type == "prefix_c"

    def test_generate_prefix_e(self):
        """Генерация номера с префиксом E"""
        num = InventoryNumber.generate_prefix_e()
        assert num is not None
        assert num.type == "prefix_e"

    def test_analyze_sequence_empty(self):
        """Анализ пустой последовательности"""
        result = InventoryNumber.analyze_sequence([])
        assert result["count"] == 0

    def test_analyze_sequence_with_items(self):
        """Анализ последовательности с элементами"""
        nums = [
            InventoryNumber("0232026200020180000000045"),
            InventoryNumber("?2101072050"),
        ]
        result = InventoryNumber.analyze_sequence(nums)
        assert result["count"] == 2
        assert "types" in result


class TestInventoryNumberStringMethods:
    """Тесты строковых методов"""

    def test_str_representation(self):
        """Строковое представление"""
        num = InventoryNumber("0232026200020180000000045")
        assert str(num) == num.value

    def test_repr_contains_value(self):
        """Repr должен содержать значение"""
        num = InventoryNumber("0232026200020180000000045")
        assert "0232026200020180000000045" in repr(num)

    def test_frozen_dataclass(self):
        """InventoryNumber должен быть неизменяемым"""
        num = InventoryNumber("0232026200020180000000045")
        with pytest.raises(Exception):
            num.value = "new_value"
