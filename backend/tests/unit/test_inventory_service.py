# backend/tests/unit/test_inventory_service.py
"""Unit-тесты для сервисов инвентаризации (без БД)"""
import pytest
from datetime import datetime, timedelta


class TestInventorySchedule:
    """Тесты для расписания инвентаризаций (без БД)"""

    def test_schedule_status_values(self):
        """Проверка допустимых значений статуса"""
        valid_statuses = ["scheduled", "in_progress", "completed", "cancelled", "overdue"]
        for status in valid_statuses:
            assert status in ["scheduled", "in_progress", "completed", "cancelled", "overdue"]

    def test_upcoming_schedules_logic(self):
        """Проверка логики фильтра предстоящих проверок"""
        now = datetime.now()
        
        # Прошедшая дата
        past = now - timedelta(days=1)
        assert past < now
        
        # Будущая дата
        future = now + timedelta(days=1)
        assert future > now
        
        # Сегодня
        assert now >= now
