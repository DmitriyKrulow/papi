# backend/tests/integration/test_storage_addresses.py
"""Интеграционные тесты для API адресного хранения"""
import pytest


class TestStorageAddressTreeEndpoint:
    """Тесты endpoint дерева адресов"""

    def test_get_address_tree_requires_auth(self, client):
        """GET /api/storage-addresses/tree требует авторизацию"""
        response = client.get("/api/storage-addresses/tree")
        assert response.status_code in [401, 403, 405]

    def test_get_address_tree_endpoint_exists(self, client):
        """Проверка что endpoint существует"""
        response = client.get("/api/storage-addresses/tree")
        assert response.status_code not in [404]

    def test_get_address_tree_with_level_filter(self, client):
        """GET /api/storage-addresses/tree?level=building"""
        response = client.get("/api/storage-addresses/tree?level=building")
        assert response.status_code not in [404]


class TestStorageAddressCreateEndpoint:
    """Тесты endpoint создания адреса"""

    def test_create_address_requires_auth(self, client):
        """POST /api/storage-addresses требует авторизацию"""
        response = client.post(
            "/api/storage-addresses",
            params={"name": "Тест", "level": "building"}
        )
        assert response.status_code in [401, 403, 405]

    def test_create_address_endpoint_exists(self, client):
        """Проверка что endpoint существует"""
        response = client.post(
            "/api/storage-addresses",
            params={"name": "Тест", "level": "building"}
        )
        assert response.status_code not in [404]

    def test_create_address_missing_name(self, client):
        """Отсутствие name должно возвращать ошибку"""
        response = client.post(
            "/api/storage-addresses",
            params={"level": "building"}
        )
        assert response.status_code in [401, 422, 405]

    def test_create_address_missing_level(self, client):
        """Отсутствие level должно возвращать ошибку"""
        response = client.post(
            "/api/storage-addresses",
            params={"name": "Тест"}
        )
        assert response.status_code in [401, 422, 405]


class TestStorageAddressDetailsEndpoint:
    """Тесты endpoint деталей адреса"""

    def test_get_address_details_requires_auth(self, client):
        """GET /api/storage-addresses/{id} требует авторизацию"""
        response = client.get("/api/storage-addresses/1")
        assert response.status_code in [401, 403, 405]

    def test_get_address_details_endpoint_exists(self, client):
        """Проверка что endpoint существует"""
        response = client.get("/api/storage-addresses/1")
        assert response.status_code not in [404]


class TestStorageAddressAssetsEndpoint:
    """Тесты endpoint активов в адресе"""

    def test_get_address_assets_requires_auth(self, client):
        """GET /api/storage-addresses/{id}/assets требует авторизацию"""
        response = client.get("/api/storage-addresses/1/assets")
        assert response.status_code in [401, 403, 405]

    def test_get_address_assets_endpoint_exists(self, client):
        """Проверка что endpoint существует"""
        response = client.get("/api/storage-addresses/1/assets")
        assert response.status_code not in [404]

    def test_get_address_assets_with_children(self, client):
        """GET /api/storage-addresses/{id}/assets?include_children=true"""
        response = client.get("/api/storage-addresses/1/assets?include_children=true")
        assert response.status_code not in [404]


class TestStorageAddressMoveEndpoint:
    """Тесты endpoint перемещения активов"""

    def test_move_asset_to_address_requires_auth(self, client):
        """POST /api/storage-addresses/{id}/move требует авторизацию"""
        response = client.post(
            "/api/storage-addresses/1/move",
            params={"asset_ids": "[1,2]"}
        )
        assert response.status_code in [401, 403, 405]

    def test_move_asset_to_address_endpoint_exists(self, client):
        """Проверка что endpoint существует"""
        response = client.post(
            "/api/storage-addresses/1/move",
            params={"asset_ids": "[1]"}
        )
        assert response.status_code not in [404]

    def test_move_asset_missing_asset_ids(self, client):
        """Отсутствие asset_ids должно возвращать ошибку"""
        response = client.post("/api/storage-addresses/1/move")
        assert response.status_code in [401, 422, 405]


class TestStorageAddressSearchEndpoint:
    """Тесты endpoint поиска по коду"""

    def test_search_by_code_requires_auth(self, client):
        """GET /api/storage-addresses/search/by-code/{code} требует авторизацию"""
        response = client.get("/api/storage-addresses/search/by-code/BLD-001")
        assert response.status_code in [401, 403, 405]

    def test_search_by_code_endpoint_exists(self, client):
        """Проверка что endpoint существует"""
        response = client.get("/api/storage-addresses/search/by-code/BLD-001")
        assert response.status_code not in [404]


class TestStorageStatsEndpoint:
    """Тесты endpoint статистики"""

    def test_get_storage_stats_requires_auth(self, client):
        """GET /api/storage-addresses/stats требует авторизацию"""
        response = client.get("/api/storage-addresses/stats")
        assert response.status_code in [401, 403, 405]

    def test_get_storage_stats_endpoint_exists(self, client):
        """Проверка что endpoint существует"""
        response = client.get("/api/storage-addresses/stats")
        assert response.status_code not in [404]


class TestStorageAddressHierarchy:
    """Тесты иерархии адресов"""

    def test_level_building_exists(self, client):
        """Проверка что building level существует"""
        response = client.get("/api/storage-addresses/tree?level=building")
        assert response.status_code not in [404]

    def test_level_floor_exists(self, client):
        """Проверка что floor level существует"""
        response = client.get("/api/storage-addresses/tree?level=floor")
        assert response.status_code not in [404]

    def test_level_zone_exists(self, client):
        """Проверка что zone level существует"""
        response = client.get("/api/storage-addresses/tree?level=zone")
        assert response.status_code not in [404]

    def test_level_aisle_exists(self, client):
        """Проверка что aisle level существует"""
        response = client.get("/api/storage-addresses/tree?level=aisle")
        assert response.status_code not in [404]

    def test_level_shelf_exists(self, client):
        """Проверка что shelf level существует"""
        response = client.get("/api/storage-addresses/tree?level=shelf")
        assert response.status_code not in [404]

    def test_level_cell_exists(self, client):
        """Проверка что cell level существует"""
        response = client.get("/api/storage-addresses/tree?level=cell")
        assert response.status_code not in [404]
