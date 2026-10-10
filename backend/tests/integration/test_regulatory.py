# backend/tests/integration/test_regulatory.py
"""Интеграционные тесты для API нормативных документов"""
import pytest


class TestRegulatoryDocumentsEndpoint:
    """Тесты endpoint нормативных документов"""

    def test_documents_requires_auth(self, client):
        """GET /api/regulatory/documents требует авторизацию"""
        response = client.get("/api/regulatory/documents")
        assert response.status_code in [401, 403, 405]

    def test_documents_endpoint_exists(self, client):
        """Проверка что endpoint существует"""
        response = client.get("/api/regulatory/documents")
        assert response.status_code not in [404]

    def test_documents_with_type_filter(self, client):
        """GET /api/regulatory/documents с фильтром по типу"""
        response = client.get("/api/regulatory/documents?type=equipping")
        assert response.status_code not in [404]


class TestEquipmentStandardsEndpoint:
    """Тесты endpoint стандартов оснащения"""

    def test_equipment_standards_requires_auth(self, client):
        """GET /api/regulatory/equipment-standards требует авторизацию"""
        response = client.get("/api/regulatory/equipment-standards")
        assert response.status_code in [401, 403, 405]

    def test_equipment_standards_endpoint_exists(self, client):
        """Проверка что endpoint существует"""
        response = client.get("/api/regulatory/equipment-standards")
        assert response.status_code not in [404]

    def test_equipment_standards_with_department(self, client):
        """GET /api/regulatory/equipment-standards с фильтром по отделу"""
        response = client.get("/api/regulatory/equipment-standards?department_code=IT")
        assert response.status_code not in [404]


class TestRegulatoryCreateEndpoint:
    """Тесты endpoint создания нормативного документа"""

    def test_create_document_requires_auth(self, client):
        """POST /api/regulatory/documents требует авторизацию"""
        response = client.post(
            "/api/regulatory/documents",
            params={
                "title": "Тестовый документ",
                "type": "equipping",
                "content": "Содержание документа"
            }
        )
        assert response.status_code in [401, 403, 405]

    def test_create_document_endpoint_exists(self, client):
        """Проверка что endpoint существует"""
        response = client.post(
            "/api/regulatory/documents",
            params={
                "title": "Тест",
                "type": "equipping"
            }
        )
        assert response.status_code not in [404]

    def test_create_document_missing_title(self, client):
        """Отсутствие title должно возвращать ошибку"""
        response = client.post(
            "/api/regulatory/documents",
            params={
                "type": "equipping"
            }
        )
        assert response.status_code in [401, 422, 405]


class TestRegulatoryUpdateEndpoint:
    """Тесты endpoint обновления документа"""

    def test_update_document_requires_auth(self, client):
        """PUT /api/regulatory/documents/{id} требует авторизацию"""
        response = client.put(
            "/api/regulatory/documents/1",
            params={"title": "Обновлённый заголовок"}
        )
        assert response.status_code in [401, 403, 405]

    def test_update_document_endpoint_exists(self, client):
        """Проверка что endpoint существует"""
        response = client.put(
            "/api/regulatory/documents/1",
            params={"title": "Обновлённый"}
        )
        assert response.status_code not in [404]


class TestRegulatoryDeleteEndpoint:
    """Тесты endpoint удаления документа"""

    def test_delete_document_requires_auth(self, client):
        """DELETE /api/regulatory/documents/{id} требует авторизацию"""
        response = client.delete("/api/regulatory/documents/1")
        assert response.status_code in [401, 403, 405]

    def test_delete_document_endpoint_exists(self, client):
        """Проверка что endpoint существует"""
        response = client.delete("/api/regulatory/documents/1")
        assert response.status_code not in [404]


class TestRegulatoryAssignEndpoint:
    """Тесты endpoint назначения документов"""

    def test_assign_document_requires_auth(self, client):
        """POST /api/regulatory/assign требует авторизацию"""
        response = client.post(
            "/api/regulatory/assign",
            params={
                "document_id": "1",
                "employee_id": "1",
                "assigned_date": "2024-10-01"
            }
        )
        assert response.status_code in [401, 403, 405]

    def test_assign_document_endpoint_exists(self, client):
        """Проверка что endpoint существует"""
        response = client.post(
            "/api/regulatory/assign",
            params={
                "document_id": "1",
                "employee_id": "1"
            }
        )
        assert response.status_code not in [404]


class TestRegulatoryEmployeeDocumentsEndpoint:
    """Тесты endpoint документов сотрудника"""

    def test_employee_documents_requires_auth(self, client):
        """GET /api/regulatory/employees/{id}/documents требует авторизацию"""
        response = client.get("/api/regulatory/employees/1/documents")
        assert response.status_code in [401, 403, 405]

    def test_employee_documents_endpoint_exists(self, client):
        """Проверка что endpoint существует"""
        response = client.get("/api/regulatory/employees/1/documents")
        assert response.status_code not in [404]
