# backend/tests/integration/test_rfid.py
"""Интеграционные тесты для RFID API endpoints"""
import pytest


class TestRFIDAuthEndpoint:
    """Тесты аутентификации RFID-сканера"""

    def test_rfid_auth_verify_requires_api_key(self, client):
        """Проверка что /api/rfid/auth/verify требует API key"""
        response = client.post("/api/rfid/auth/verify")
        # Без API key должен вернуть 401/403
        assert response.status_code in [401, 403, 405]

    def test_rfid_auth_verify_endpoint_exists(self, client):
        """Проверка что endpoint существует"""
        response = client.post("/api/rfid/auth/verify")
        # Endpoint должен существовать (даже если 401)
        assert response.status_code not in [404]


class TestRFIDInventoriesEndpoint:
    """Тесты endpoints инвентаризаций RFID"""

    def test_get_active_inventories_requires_api_key(self, client):
        """GET /api/rfid/inventories требует API key"""
        response = client.get("/api/rfid/inventories")
        assert response.status_code in [401, 403, 405]

    def test_get_active_inventories_endpoint_exists(self, client):
        """Проверка что endpoint существует"""
        response = client.get("/api/rfid/inventories")
        assert response.status_code not in [404]


class TestRFIDInventoryAssetsEndpoint:
    """Тесты endpoints активов инвентаризации"""

    def test_get_inventory_assets_requires_api_key(self, client):
        """GET /api/rfid/inventories/{id}/assets требует API key"""
        response = client.get("/api/rfid/inventories/1/assets")
        assert response.status_code in [401, 403, 405, 404]

    def test_get_inventory_assets_endpoint_exists(self, client):
        """Проверка что endpoint существует"""
        response = client.get("/api/rfid/inventories/1/assets")
        assert response.status_code not in [404]


class TestRFIDAssetByRfid:
    """Тесты поиска актива по RFID"""

    def test_get_asset_by_rfid_requires_api_key(self, client):
        """GET /api/rfid/assets/by-rfid/{tag} требует API key"""
        response = client.get("/api/rfid/assets/by-rfid/test_tag_123")
        assert response.status_code in [401, 403, 405]

    def test_get_asset_by_rfid_endpoint_exists(self, client):
        """Проверка что endpoint существует"""
        response = client.get("/api/rfid/assets/by-rfid/test_tag_123")
        assert response.status_code not in [404]


class TestRFIDScanEndpoint:
    """Тесты endpoints сканирования RFID"""

    def test_scan_rfid_requires_api_key(self, client):
        """POST /api/rfid/inventories/{id}/scan требует API key"""
        response = client.post("/api/rfid/inventories/1/scan?rfid_tag=test_tag")
        assert response.status_code in [401, 403, 405]

    def test_scan_rfid_endpoint_exists(self, client):
        """Проверка что endpoint существует"""
        response = client.post("/api/rfid/inventories/1/scan?rfid_tag=test_tag")
        assert response.status_code not in [404]

    def test_scan_batch_requires_api_key(self, client):
        """POST /api/rfid/inventories/{id}/scan-batch требует API key"""
        response = client.post("/api/rfid/inventories/1/scan-batch", json={"rfid_tags": ["tag1", "tag2"]})
        assert response.status_code in [401, 403, 405]

    def test_scan_batch_endpoint_exists(self, client):
        """Проверка что endpoint существует"""
        response = client.post("/api/rfid/inventories/1/scan-batch", json={"rfid_tags": ["tag1"]})
        assert response.status_code not in [404]


class TestRFIDPassiveRoomScan:
    """Тесты пассивного сканирования помещения"""

    def test_passive_room_scan_requires_api_key(self, client):
        """POST /api/rfid/scan-room требует API key"""
        response = client.post("/api/rfid/scan-room?room_id=1&rfid_tags=[tag1]")
        assert response.status_code in [401, 403, 405]

    def test_passive_room_scan_endpoint_exists(self, client):
        """Проверка что endpoint существует"""
        response = client.post("/api/rfid/scan-room?room_id=1&rfid_tags=[]")
        assert response.status_code not in [404]


class TestRFIDReceiveEndpoint:
    """Тесты приёмки через RFID"""

    def test_receive_assets_requires_api_key(self, client):
        """POST /api/rfid/receive требует API key"""
        response = client.post(
            "/api/rfid/receive?department_code=TEST&responsible_person=Test&rfid_tags=[tag1]"
        )
        assert response.status_code in [401, 403, 405]

    def test_receive_assets_endpoint_exists(self, client):
        """Проверка что endpoint существует"""
        response = client.post("/api/rfid/receive?department_code=TEST&responsible_person=Test&rfid_tags=[]")
        assert response.status_code not in [404]


class TestRFIDMoveEndpoint:
    """Тесты перемещения через RFID"""

    def test_move_assets_requires_api_key(self, client):
        """POST /api/rfid/move требует API key"""
        response = client.post(
            "/api/rfid/move?from_room_id=1&to_room_id=2&rfid_tags=[tag1]"
        )
        assert response.status_code in [401, 403, 405]

    def test_move_assets_endpoint_exists(self, client):
        """Проверка что endpoint существует"""
        response = client.post("/api/rfid/move?from_room_id=1&to_room_id=2&rfid_tags=[]")
        assert response.status_code not in [404]


class TestRFIDInventoryStatus:
    """Тесты статуса инвентаризации RFID"""

    def test_inventory_status_requires_api_key(self, client):
        """GET /api/rfid/inventories/{id}/status требует API key"""
        response = client.get("/api/rfid/inventories/1/status")
        assert response.status_code in [401, 403, 405]

    def test_inventory_status_endpoint_exists(self, client):
        """Проверка что endpoint существует"""
        response = client.get("/api/rfid/inventories/1/status")
        assert response.status_code not in [404]
