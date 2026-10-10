# backend/tests/integration/test_analytics.py
"""Интеграционные тесты для API аналитики"""
import pytest


class TestAnalyticsOverviewEndpoint:
    """Тесты endpoint overview аналитики"""

    def test_analytics_overview_requires_auth(self, client):
        """GET /api/analytics/overview требует авторизацию"""
        response = client.get("/api/analytics/overview")
        assert response.status_code in [401, 403, 405]

    def test_analytics_overview_endpoint_exists(self, client):
        """Проверка что endpoint существует"""
        response = client.get("/api/analytics/overview")
        assert response.status_code not in [404]


class TestAnalyticsBreakdownTrendsEndpoint:
    """Тесты endpoint трендов поломок"""

    def test_breakdown_trends_requires_auth(self, client):
        """GET /api/analytics/breakdown-trends требует авторизацию"""
        response = client.get("/api/analytics/breakdown-trends")
        assert response.status_code in [401, 403, 405]

    def test_breakdown_trends_endpoint_exists(self, client):
        """Проверка что endpoint существует"""
        response = client.get("/api/analytics/breakdown-trends")
        assert response.status_code not in [404]

    def test_breakdown_trends_with_date_range(self, client):
        """GET /api/analytics/breakdown-trends с параметрами"""
        response = client.get("/api/analytics/breakdown-trends?months=6")
        assert response.status_code not in [404]


class TestAnalyticsDiscrepanciesEndpoint:
    """Тесты endpoint расхождений"""

    def test_discrepancies_requires_auth(self, client):
        """GET /api/analytics/discrepancies требует авторизацию"""
        response = client.get("/api/analytics/discrepancies")
        assert response.status_code in [401, 403, 405]

    def test_discrepancies_endpoint_exists(self, client):
        """Проверка что endpoint существует"""
        response = client.get("/api/analytics/discrepancies")
        assert response.status_code not in [404]


class TestAnalyticsPurchaseRecommendationsEndpoint:
    """Тесты endpoint рекомендаций по закупкам"""

    def test_purchase_recommendations_requires_auth(self, client):
        """GET /api/analytics/purchase-recommendations требует авторизацию"""
        response = client.get("/api/analytics/purchase-recommendations")
        assert response.status_code in [401, 403, 405]

    def test_purchase_recommendations_endpoint_exists(self, client):
        """Проверка что endpoint существует"""
        response = client.get("/api/analytics/purchase-recommendations")
        assert response.status_code not in [404]


class TestAnalyticsDepreciationEndpoint:
    """Тесты endpoint амортизации"""

    def test_depreciation_requires_auth(self, client):
        """GET /api/analytics/depreciation требует авторизацию"""
        response = client.get("/api/analytics/depreciation")
        assert response.status_code in [401, 403, 405]

    def test_depreciation_endpoint_exists(self, client):
        """Проверка что endpoint существует"""
        response = client.get("/api/analytics/depreciation")
        assert response.status_code not in [404]
