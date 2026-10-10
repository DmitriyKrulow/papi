# backend/tests/integration/test_auth.py
"""Интеграционные тесты для endpoints авторизации"""
import pytest


@pytest.mark.skip(reason="Integration tests require PostgreSQL and full app setup")
class TestAuthEndpoints:
    """Тесты endpoints авторизации"""

    def test_login_endpoint_exists(self, client):
        """Тест что login endpoint существует"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "admin",
                "password": "admin123",
            },
        )
        # Ожидаем 200 или 401 (если пользователь не найден)
        assert response.status_code in [200, 401, 422]

    def test_register_endpoint_exists(self, client):
        """Тест что register endpoint существует"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "test_user",
                "email": "test@example.com",
                "password": "test_password",
                "full_name": "Test User",
            },
        )
        # Ожидаем 201 (создан) или 422 (валидация)
        assert response.status_code in [201, 422]

    def test_docs_endpoint_accessible(self, client):
        """Тест что docs endpoint доступен без авторизации"""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_openapi_json_accessible(self, client):
        """Тест что openapi.json доступен"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "info" in data
        assert "paths" in data
        assert data["info"]["title"] == "PAPI Backend"
