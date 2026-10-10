# backend/tests/integration/test_disposal.py
"""Интеграционные тесты для API списания активов"""
import pytest


class TestDisposalDecommissionEndpoint:
    """Тесты endpoint decommission"""

    def test_decommission_requires_auth(self, client):
        """POST /api/disposal/decommission требует авторизацию"""
        response = client.post("/api/disposal/decommission", params={"asset_id": 1, "reason": "test"})
        assert response.status_code in [401, 403, 405]

    def test_decommission_endpoint_exists(self, client):
        """Проверка что endpoint существует"""
        response = client.post("/api/disposal/decommission", params={"asset_id": 1, "reason": "test"})
        assert response.status_code not in [404]

    def test_decommission_missing_asset_id(self, client):
        """Отсутствие asset_id должно возвращать ошибку"""
        response = client.post("/api/disposal/decommission", params={"reason": "test"})
        assert response.status_code in [401, 422, 405]

    def test_decommission_missing_reason(self, client):
        """Отсутствие reason должно возвращать ошибку"""
        response = client.post("/api/disposal/decommission", params={"asset_id": 1})
        assert response.status_code in [401, 422, 405]


class TestDisposalHistoryEndpoint:
    """Тесты endpoint истории списаний"""

    def test_disposal_history_requires_auth(self, client):
        """GET /api/disposal/history требует авторизацию"""
        response = client.get("/api/disposal/history")
        assert response.status_code in [401, 403, 405]

    def test_disposal_history_endpoint_exists(self, client):
        """Проверка что endpoint существует"""
        response = client.get("/api/disposal/history")
        assert response.status_code not in [404]

    def test_disposal_history_with_date_filter(self, client):
        """GET /api/disposal/history с фильтром по дате"""
        response = client.get("/api/disposal/history?from_date=2024-01-01")
        assert response.status_code not in [404]


class TestDisposalRestoreEndpoint:
    """Тесты endpoint восстановления из списания"""

    def test_restore_from_disposal_requires_auth(self, client):
        """POST /api/disposal/restore требует авторизацию"""
        response = client.post("/api/disposal/restore", params={"asset_id": 1})
        assert response.status_code in [401, 403, 405]

    def test_restore_from_disposal_endpoint_exists(self, client):
        """Проверка что endpoint существует"""
        response = client.post("/api/disposal/restore", params={"asset_id": 1})
        assert response.status_code not in [404]
