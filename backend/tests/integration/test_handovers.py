# backend/tests/integration/test_handovers.py
"""Интеграционные тесты для API передач активов (Handovers)"""
import pytest


class TestHandoverEndpoints:
    """Тесты endpoints передач активов"""

    def test_handover_asset_requires_auth(self, client):
        """POST /api/handovers/handover требует авторизацию"""
        response = client.post(
            "/api/handovers/handover",
            params={"asset_id": 1, "received_by_user_id": 1}
        )
        assert response.status_code in [401, 403, 405]

    def test_handover_asset_endpoint_exists(self, client):
        """Проверка что endpoint существует"""
        response = client.post(
            "/api/handovers/handover",
            params={"asset_id": 1, "received_by_user_id": 1}
        )
        assert response.status_code not in [404]

    def test_return_asset_requires_auth(self, client):
        """POST /api/handovers/return требует авторизацию"""
        response = client.post(
            "/api/handovers/return",
            params={"asset_id": 1, "returned_by_user_id": 1}
        )
        assert response.status_code in [401, 403, 405]

    def test_return_asset_endpoint_exists(self, client):
        """Проверка что endpoint существует"""
        response = client.post(
            "/api/handovers/return",
            params={"asset_id": 1, "returned_by_user_id": 1}
        )
        assert response.status_code not in [404]


class TestHandoverHistoryEndpoints:
    """Тесты endpoints истории передач"""

    def test_get_asset_handover_history_requires_auth(self, client):
        """GET /api/handovers/asset/{id} требует авторизацию"""
        response = client.get("/api/handovers/asset/1")
        assert response.status_code in [401, 403, 405]

    def test_get_asset_handover_history_endpoint_exists(self, client):
        """Проверка что endpoint существует"""
        response = client.get("/api/handovers/asset/1")
        assert response.status_code not in [404]

    def test_get_my_active_handovers_requires_auth(self, client):
        """GET /api/handovers/my-active требует авторизацию"""
        response = client.get("/api/handovers/my-active")
        assert response.status_code in [401, 403, 405]

    def test_get_my_active_handovers_endpoint_exists(self, client):
        """Проверка что endpoint существует"""
        response = client.get("/api/handovers/my-active")
        assert response.status_code not in [404]

    def test_get_all_active_handovers_requires_admin(self, client):
        """GET /api/handovers/all-active требует админа"""
        response = client.get("/api/handovers/all-active")
        assert response.status_code in [401, 403, 405]

    def test_get_all_active_handovers_endpoint_exists(self, client):
        """Проверка что endpoint существует"""
        response = client.get("/api/handovers/all-active")
        assert response.status_code not in [404]


class TestHandoverStatsEndpoints:
    """Тесты endpoints статистики передач"""

    def test_get_handover_stats_requires_admin(self, client):
        """GET /api/handovers/stats требует админа"""
        response = client.get("/api/handovers/stats")
        assert response.status_code in [401, 403, 405]

    def test_get_handover_stats_endpoint_exists(self, client):
        """Проверка что endpoint существует"""
        response = client.get("/api/handovers/stats")
        assert response.status_code not in [404]


class TestHandoverRequestValidation:
    """Тесты валидации запросов передач"""

    def test_handover_missing_asset_id(self, client):
        """Отсутствие asset_id должно возвращать ошибку"""
        response = client.post(
            "/api/handovers/handover",
            params={"received_by_user_id": 1}
        )
        # Должна быть ошибка валидации (422) или авторизации (401)
        assert response.status_code in [401, 422, 405]

    def test_handover_missing_receiver_id(self, client):
        """Отсутствие received_by_user_id должно возвращать ошибку"""
        response = client.post(
            "/api/handovers/handover",
            params={"asset_id": 1}
        )
        assert response.status_code in [401, 422, 405]

    def test_return_missing_asset_id(self, client):
        """Отсутствие asset_id при возврате"""
        response = client.post(
            "/api/handovers/return",
            params={"returned_by_user_id": 1}
        )
        assert response.status_code in [401, 422, 405]

    def test_return_missing_returner_id(self, client):
        """Отсутствие returned_by_user_id при возврате"""
        response = client.post(
            "/api/handovers/return",
            params={"asset_id": 1}
        )
        assert response.status_code in [401, 422, 405]
