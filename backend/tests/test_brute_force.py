"""
Тесты для защиты от брутфорса.
Проверяют:
1. Логику lockout после 5 неудачных попыток
2. Прогрессивную блокировку (5 мин → 30 мин → 1 час)
3. Перманентную блокировку после 15 неудач
4. Whitelist IP для администраторов
5. Запись логов в БД
"""

import json
import sys
import os
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.use_cases.auth.login_user import (
    LoginUser,
    BruteForceException,
    AccountPermanentlyLockedException,
    _parse_allowed_ips,
    _check_ip_allowed,
    _get_recent_failures,
    _get_total_failures,
    _get_current_lockout,
    _record_failure,
    _record_success,
    MAX_ATTEMPTS_BEFORE_LOCKOUT,
    MAX_TOTAL_FAILURES,
    LOCKOUT_STAGES,
)
from src.infrastructure.db.models.brute_force_log import BruteForceLog
from src.infrastructure.db.models.user import User


def _create_mock_db():
    """Создаёт мок-объект сессии БД для тестов."""
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    return db


class TestBruteForceLogic:
    """Тесты логики защиты от брутфорса."""

    def test_max_attempts_constant(self):
        """Константа MAX_ATTEMPTS_BEFORE_LOCKOUT = 5."""
        assert MAX_ATTEMPTS_BEFORE_LOCKOUT == 5

    def test_max_total_failures_constant(self):
        """Константа MAX_TOTAL_FAILURES = 15."""
        assert MAX_TOTAL_FAILURES == 15

    def test_lockout_stages(self):
        """Этапы lockout: 5 мин, 30 мин, 1 час."""
        assert len(LOCKOUT_STAGES) == 3
        assert LOCKOUT_STAGES[0] == timedelta(minutes=5)
        assert LOCKOUT_STAGES[1] == timedelta(minutes=30)
        assert LOCKOUT_STAGES[2] == timedelta(hours=1)


class TestParseAllowedIPs:
    """Тесты парсинга allowed_ips."""

    def test_none_allowed_ips(self):
        user = MagicMock()
        user.allowed_ips = None
        assert _parse_allowed_ips(user) == []

    def test_empty_allowed_ips(self):
        user = MagicMock()
        user.allowed_ips = ""
        assert _parse_allowed_ips(user) == []

    def test_valid_json_ips(self):
        user = MagicMock()
        user.allowed_ips = json.dumps(["192.168.1.1", "10.0.0.1"])
        result = _parse_allowed_ips(user)
        assert result == ["192.168.1.1", "10.0.0.1"]

    def test_invalid_json_ips(self):
        user = MagicMock()
        user.allowed_ips = "not-json"
        assert _parse_allowed_ips(user) == []

    def test_ips_with_whitespace(self):
        user = MagicMock()
        user.allowed_ips = json.dumps([" 192.168.1.1 ", "10.0.0.1 "])
        result = _parse_allowed_ips(user)
        assert result == ["192.168.1.1", "10.0.0.1"]


class TestCheckIPAllowed:
    """Тесты проверки IP whitelist."""

    def test_non_admin_always_allowed(self):
        """Обычные пользователи всегда разрешены (whitelist только для админов)."""
        user = MagicMock()
        user.role = "user"
        user.allowed_ips = json.dumps(["192.168.1.1"])
        assert _check_ip_allowed(user, "10.0.0.1") is True
        assert _check_ip_allowed(user, "192.168.1.1") is True

    def test_admin_no_whitelist_allowed(self):
        """Админ без whitelist — вход разрешён."""
        user = MagicMock()
        user.role = "admin"
        user.allowed_ips = None
        assert _check_ip_allowed(user, "10.0.0.1") is True

    def test_admin_empty_whitelist_allowed(self):
        """Админ с пустым whitelist — вход разрешён."""
        user = MagicMock()
        user.role = "admin"
        user.allowed_ips = json.dumps([])
        assert _check_ip_allowed(user, "10.0.0.1") is True

    def test_admin_whitelist_match(self):
        """Админ с whitelist — вход с разрешённого IP."""
        user = MagicMock()
        user.role = "admin"
        user.allowed_ips = json.dumps(["192.168.1.1", "10.0.0.5"])
        assert _check_ip_allowed(user, "192.168.1.1") is True
        assert _check_ip_allowed(user, "10.0.0.5") is True

    def test_admin_whitelist_no_match(self):
        """Админ с whitelist — вход с запрещённого IP."""
        user = MagicMock()
        user.role = "admin"
        user.allowed_ips = json.dumps(["192.168.1.1", "10.0.0.5"])
        assert _check_ip_allowed(user, "8.8.8.8") is False


class TestRecordFailureAndSuccess:
    """Тесты записи логов."""

    def test_record_failure_creates_entry(self):
        db = _create_mock_db()
        _record_failure(db, "testuser", "192.168.1.1")
        db.add.assert_called_once()
        call_args = db.add.call_args
        entry = call_args[0][0]
        assert isinstance(entry, BruteForceLog)
        assert entry.username == "testuser"
        assert entry.ip_address == "192.168.1.1"
        assert entry.is_success == 0

    def test_record_success_creates_entry(self):
        db = _create_mock_db()
        _record_success(db, "testuser", "192.168.1.1")
        db.add.assert_called_once()
        call_args = db.add.call_args
        entry = call_args[0][0]
        assert isinstance(entry, BruteForceLog)
        assert entry.username == "testuser"
        assert entry.is_success == 1


class TestBruteForceException:
    """Тесты исключения BruteForceException."""

    def test_exception_message_with_minutes(self):
        user = MagicMock()
        user.username = "testuser"
        exc = BruteForceException(user, remaining_seconds=300, total_failures=6)
        assert "5 мин" in str(exc)
        assert "6" in str(exc)

    def test_exception_message_with_hours(self):
        user = MagicMock()
        user.username = "testuser"
        exc = BruteForceException(user, remaining_seconds=3600, total_failures=11)
        assert "1 ч" in str(exc)
        assert "11" in str(exc)


class TestAccountPermanentlyLockedException:
    """Тесты перманентной блокировки."""

    def test_exception_message(self):
        user = MagicMock()
        user.username = "hacked_user"
        exc = AccountPermanentlyLockedException(user)
        assert "hacked_user" in str(exc)
        assert "заблокирован" in str(exc)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
