# backend/tests/integration/test_inventory_schedule.py
"""Интеграционные тесты для API расписания инвентаризаций"""
import pytest


class TestInventoryScheduleCalendarEndpoint:
    """Тесты endpoint календаря расписания"""

    def test_calendar_requires_auth(self, client):
        """GET /api/inventory-schedule/calendar требует авторизацию"""
        response = client.get("/api/inventory-schedule/calendar")
        assert response.status_code in [401, 403, 405]

    def test_calendar_endpoint_exists(self, client):
        """Проверка что endpoint существует"""
        response = client.get("/api/inventory-schedule/calendar")
        assert response.status_code not in [404]

    def test_calendar_with_month_param(self, client):
        """GET /api/inventory-schedule/calendar с параметром месяца"""
        response = client.get("/api/inventory-schedule/calendar?month=2024-10")
        assert response.status_code not in [404]


class TestInventoryScheduleUpcomingEndpoint:
    """Тесты endpoint предстоящих проверок"""

    def test_upcoming_requires_auth(self, client):
        """GET /api/inventory-schedule/upcoming требует авторизацию"""
        response = client.get("/api/inventory-schedule/upcoming")
        assert response.status_code in [401, 403, 405]

    def test_upcoming_endpoint_exists(self, client):
        """Проверка что endpoint существует"""
        response = client.get("/api/inventory-schedule/upcoming")
        assert response.status_code not in [404]

    def test_upcoming_with_limit_param(self, client):
        """GET /api/inventory-schedule/upcoming с лимитом"""
        response = client.get("/api/inventory-schedule/upcoming?limit=10")
        assert response.status_code not in [404]


class TestInventoryScheduleCreateEndpoint:
    """Тесты endpoint создания расписания"""

    def test_create_schedule_requires_auth(self, client):
        """POST /api/inventory-schedule требует авторизацию"""
        response = client.post(
            "/api/inventory-schedule",
            params={
                "name": "Тестовая проверка",
                "check_type": "room",
                "target_id": "1",
                "scheduled_date": "2024-10-15T10:00:00"
            }
        )
        assert response.status_code in [401, 403, 405]

    def test_create_schedule_endpoint_exists(self, client):
        """Проверка что endpoint существует"""
        response = client.post(
            "/api/inventory-schedule",
            params={
                "name": "Тест",
                "check_type": "room",
                "target_id": "1",
                "scheduled_date": "2024-10-15T10:00:00"
            }
        )
        assert response.status_code not in [404]

    def test_create_schedule_missing_name(self, client):
        """Отсутствие name должно возвращать ошибку"""
        response = client.post(
            "/api/inventory-schedule",
            params={
                "check_type": "room",
                "target_id": "1",
                "scheduled_date": "2024-10-15T10:00:00"
            }
        )
        assert response.status_code in [401, 422, 405]


class TestInventoryScheduleUpdateEndpoint:
    """Тесты endpoint обновления расписания"""

    def test_update_schedule_requires_auth(self, client):
        """PUT /api/inventory-schedule/{id} требует авторизацию"""
        response = client.put(
            "/api/inventory-schedule/1",
            params={"status": "completed"}
        )
        assert response.status_code in [401, 403, 405]

    def test_update_schedule_endpoint_exists(self, client):
        """Проверка что endpoint существует"""
        response = client.put(
            "/api/inventory-schedule/1",
            params={"status": "completed"}
        )
        assert response.status_code not in [404]


class TestInventoryScheduleDeleteEndpoint:
    """Тесты endpoint удаления расписания"""

    def test_delete_schedule_requires_auth(self, client):
        """DELETE /api/inventory-schedule/{id} требует авторизацию"""
        response = client.delete("/api/inventory-schedule/1")
        assert response.status_code in [401, 403, 405]

    def test_delete_schedule_endpoint_exists(self, client):
        """Проверка что endpoint существует"""
        response = client.delete("/api/inventory-schedule/1")
        assert response.status_code not in [404]


class TestInventoryScheduleStatsEndpoint:
    """Тесты endpoint статистики расписания"""

    def test_schedule_stats_requires_auth(self, client):
        """GET /api/inventory-schedule/stats требует авторизацию"""
        response = client.get("/api/inventory-schedule/stats")
        assert response.status_code in [401, 403, 405]

    def test_schedule_stats_endpoint_exists(self, client):
        """Проверка что endpoint существует"""
        response = client.get("/api/inventory-schedule/stats")
        assert response.status_code not in [404]
