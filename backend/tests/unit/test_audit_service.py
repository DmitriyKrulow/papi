# backend/tests/unit/test_audit_service.py
"""Unit-тесты для AuditService (без БД)"""
import json
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from src.core.services.audit_service import AuditEntry, AuditAction


class TestAuditEntry:
    """Тесты для AuditEntry"""

    def test_diff_summary_with_changes(self):
        """Проверка генерации diff_summary при изменениях"""
        entry = AuditEntry(
            entity_type="Asset",
            entity_id=1,
            action=AuditAction.UPDATE,
            old_values={"status": "active", "responsible": "Иванов"},
            new_values={"status": "maintenance", "responsible": "Петров"},
        )
        
        summary = entry.diff_summary
        assert summary is not None
        assert "responsible" in summary
        assert "status" in summary
        # Статусы переводятся в русский
        assert "Активен" in summary or "active" in summary
        assert "На ремонте" in summary or "maintenance" in summary

    def test_format_value(self):
        """Проверка форматирования значений"""
        # Метод принимает 2 аргумента: key и value
        assert AuditEntry._format_value("status", None) == "пусто"
        assert AuditEntry._format_value("status", True) == "да"
        assert AuditEntry._format_value("status", False) == "нет"


class TestAuditAction:
    """Тесты для AuditAction enum"""

    def test_all_actions_exist(self):
        """Проверка что все действия существуют"""
        actions = [
            "create", "update", "delete", "login", "logout",
            "status_change", "import", "export",
            "inventory_start", "inventory_complete",
            "repair_create", "repair_update",
        ]
        for action in actions:
            assert action in [a.value for a in AuditAction]
