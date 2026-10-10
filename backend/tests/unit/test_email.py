# backend/tests/unit/test_email.py
"""Unit-тесты для Email Value Object (без БД)"""
import pytest
from src.core.value_objects.email import Email


class TestEmailCreation:
    """Тесты создания Email"""

    def test_valid_email_creation(self):
        """Создание валидного email"""
        email = Email("user@example.com")
        assert email.value == "user@example.com"

    def test_email_normalized_to_lowercase(self):
        """Email должен нормализоваться к нижнему регистру"""
        email = Email("USER@EXAMPLE.COM")
        assert email.value == "user@example.com"

    def test_email_strips_whitespace(self):
        """Email должен обрезать пробелы"""
        email = Email("  user@example.com  ")
        assert email.value == "user@example.com"

    def test_invalid_email_format_raises(self):
        """Невалидный формат должен вызывать ошибку"""
        with pytest.raises(ValueError, match="Invalid email format"):
            Email("invalid-email")

    def test_empty_email_raises(self):
        """Пустой email должен вызывать ошибку"""
        with pytest.raises(ValueError, match="Invalid email format"):
            Email("")

    def test_no_at_symbol_raises(self):
        """Email без @ должен отклоняться"""
        with pytest.raises(ValueError, match="Invalid email format"):
            Email("userexample.com")

    def test_no_domain_raises(self):
        """Email без домена должен отклоняться"""
        with pytest.raises(ValueError, match="Invalid email format"):
            Email("user@")


class TestEmailDomains:
    """Тесты доменов email"""

    def test_domain_extraction(self):
        """Извлечение домена"""
        email = Email("user@example.com")
        assert email.domain == "example.com"

    def test_local_part_extraction(self):
        """Извлечение локальной части"""
        email = Email("user.name@example.com")
        assert email.local_part == "user.name"

    def test_subdomain_extraction(self):
        """Извлечение поддомена"""
        email = Email("user@mail.example.com")
        assert email.domain == "mail.example.com"

    def test_allowed_tld_com(self):
        """.com должен быть разрешён"""
        email = Email("user@example.com")
        assert email is not None

    def test_allowed_tld_ru(self):
        """.ru должен быть разрешён"""
        email = Email("user@example.ru")
        assert email is not None

    def test_allowed_tld_local(self):
        """.local должен быть разрешён"""
        email = Email("user@example.local")
        assert email is not None

    def test_disallowed_tld_raises(self):
        """Запрещённый TLD должен отклоняться"""
        with pytest.raises(ValueError, match="Domain not allowed"):
            Email("user@example.xyz")


class TestEmailProperties:
    """Тесты свойств Email"""

    def test_is_gmail_true(self):
        """Gmail должен определяться"""
        email = Email("user@gmail.com")
        assert email.is_gmail is True

    def test_is_gmail_googlemail(self):
        """Googlemail тоже должен определяться"""
        email = Email("user@googlemail.com")
        assert email.is_gmail is True

    def test_is_gmail_false(self):
        """Не-Gmail должен возвращать False"""
        email = Email("user@yandex.ru")
        assert email.is_gmail is False

    def test_str_representation(self):
        """Строковое представление"""
        email = Email("user@example.com")
        assert str(email) == "user@example.com"

    def test_repr_contains_email(self):
        """Repr должен содержать email"""
        email = Email("user@example.com")
        assert "user@example.com" in repr(email)

    def test_frozen_dataclass(self):
        """Email должен быть неизменяемым"""
        email = Email("user@example.com")
        with pytest.raises(Exception):
            email.value = "new@example.com"


class TestEmailMethods:
    """Тесты методов Email"""

    def test_obfuscate_short_local(self):
        """Обфускация короткой локальной части"""
        email = Email("ab@example.com")
        obfuscated = email.obfuscate()
        assert "***" in obfuscated
        assert "@example.com" in obfuscated

    def test_obfuscate_long_local(self):
        """Обфускация длинной локальной части"""
        email = Email("username@example.com")
        obfuscated = email.obfuscate()
        assert "***" in obfuscated
        assert "us" in obfuscated  # первые 2 символа

    def test_is_same_domain_true(self):
        """Один домен должен определяться"""
        e1 = Email("user1@example.com")
        e2 = Email("user2@example.com")
        assert e1.is_same_domain(e2) is True

    def test_is_same_domain_false(self):
        """Разные домены должны определяться"""
        e1 = Email("user1@example.com")
        e2 = Email("user2@other.com")
        assert e1.is_same_domain(e2) is False

    def test_is_organization_email_true(self):
        """Организационный email должен определяться"""
        email = Email("user@company.com")
        assert email.is_organization_email(("company.com",)) is True

    def test_is_organization_email_false(self):
        """Не-организационный email"""
        email = Email("user@gmail.com")
        assert email.is_organization_email(("company.com",)) is False

    def test_get_normalized_gmail(self):
        """Нормализация Gmail"""
        email = Email("user.name+tag@gmail.com")
        normalized = email.get_normalized_gmail()
        assert normalized is not None
        assert normalized.value == "username@gmail.com"

    def test_get_normalized_gmail_non_gmail(self):
        """Не-Gmail должен возвращать None"""
        email = Email("user@yandex.ru")
        assert email.get_normalized_gmail() is None


class TestEmailFactoryMethods:
    """Тесты фабричных методов Email"""

    def test_create_allow_null_with_value(self):
        """Создание с значением"""
        email = Email.create_allow_null("user@example.com")
        assert email is not None
        assert email.value == "user@example.com"

    def test_create_allow_null_with_none(self):
        """Создание с None"""
        email = Email.create_allow_null(None)
        assert email is None

    def test_create_allow_null_with_empty_string(self):
        """Создание с пустой строкой"""
        email = Email.create_allow_null("")
        assert email is None

    def test_create_quiet_valid(self):
        """Тихое создание валидного email"""
        email = Email.create_quiet("user@example.com")
        assert email is not None

    def test_create_quiet_invalid(self):
        """Тихое создание невалидного email"""
        email = Email.create_quiet("invalid")
        assert email is None

    def test_random_email(self):
        """Генерация случайного email"""
        email = Email.random()
        assert email is not None
        assert "@test.com" in email.value
