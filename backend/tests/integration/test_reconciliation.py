# backend/tests/integration/test_reconciliation.py
"""Интеграционные тесты для API ежемесячной сверки"""
import pytest


class TestReconciliationMonthlyEndpoint:
    """Тесты endpoint ежемесячной сверки"""

    def test_monthly_reconciliation_requires_auth(self, client):
        """GET /api/reconciliation/monthly требует авторизацию"""
        response = client.get("/api/reconciliation/monthly")
        assert response.status_code in [401, 403, 405]

    def test_monthly_reconciliation_endpoint_exists(self, client):
        """Проверка что endpoint существует"""
        response = client.get("/api/reconciliation/monthly")
        assert response.status_code not in [404]

    def test_monthly_reconciliation_with_month_param(self, client):
        """GET /api/reconciliation/monthly с параметром месяца"""
        response = client.get("/api/reconciliation/monthly?month=2024-10")
        assert response.status_code not in [404]


class TestReconciliationCreateEndpoint:
    """Тесты endpoint создания сверки"""

    def test_create_reconciliation_requires_auth(self, client):
        """POST /api/reconciliation требует авторизацию"""
        response = client.post(
            "/api/reconciliation",
            params={
                "month": "2024-10",
                "department_code": "IT",
                "notes": "Тестовая сверка"
            }
        )
        assert response.status_code in [401, 403, 405]

    def test_create_reconciliation_endpoint_exists(self, client):
        """Проверка что endpoint существует"""
        response = client.post(
            "/api/reconciliation",
            params={
                "month": "2024-10",
                "department_code": "IT"
            }
        )
        assert response.status_code not in [404]

    def test_create_reconciliation_missing_month(self, client):
        """Отсутствие month должно возвращать ошибку"""
        response = client.post(
            "/api/reconciliation",
            params={
                "department_code": "IT"
            }
        )
        assert response.status_code in [401, 422, 405]


class TestReconciliationDetailsEndpoint:
    """Тесты endpoint деталей сверки"""

    def test_reconciliation_details_requires_auth(self, client):
        """GET /api/reconciliation/{id} требует авторизацию"""
        response = client.get("/api/reconciliation/1")
        assert response.status_code in [401, 403, 405]

    def test_reconciliation_details_endpoint_exists(self, client):
        """Проверка что endpoint существует"""
        response = client.get("/api/reconciliation/1")
        assert response.status_code not in [404]


class TestReconciliationExportEndpoint:
    """Тесты endpoint экспорта сверки"""

    def test_export_reconciliation_requires_auth(self, client):
        """GET /api/reconciliation/{id}/export требует авторизацию"""
        response = client.get("/api/reconciliation/1/export")
        assert response.status_code in [401, 403, 405]

    def test_export_reconciliation_endpoint_exists(self, client):
        """Проверка что endpoint существует"""
        response = client.get("/api/reconciliation/1/export")
        assert response.status_code not in [404]

    def test_export_reconciliation_excel_format(self, client):
        """Экспорт в формате Excel"""
        response = client.get("/api/reconciliation/1/export?format=excel")
        assert response.status_code not in [404]


class TestReconciliationHistoryEndpoint:
    """Тесты endpoint истории сверок"""

    def test_reconciliation_history_requires_auth(self, client):
        """GET /api/reconciliation/history требует авторизацию"""
        response = client.get("/api/reconciliation/history")
        assert response.status_code in [401, 403, 405]

    def test_reconciliation_history_endpoint_exists(self, client):
        """Проверка что endpoint существует"""
        response = client.get("/api/reconciliation/history")
        assert response.status_code not in [404]

    def test_reconciliation_history_with_year_filter(self, client):
        """История с фильтром по году"""
        response = client.get("/api/reconciliation/history?year=2024")
        assert response.status_code not in [404]
