# tests/unit/test_department.py
import pytest
from backend.src.core.entities.department import Department


class TestDepartmentEntity:
    """Тесты сущности Department"""

    def test_create_department_with_valid_data(self):
        """Создание подразделения с валидными данными"""
        department = Department(
            id=1,
            code="IT",
            name="Отдел информационных технологий",
            full_name="Отдел информационных технологий",
            parent_code=None,
            is_active=True
        )
        
        assert department.id == 1
        assert department.code == "IT"
        assert department.name == "Отдел информационных технологий"

    def test_department_with_parent(self):
        """Подразделение с родителем"""
        department = Department(
            id=2,
            code="IT-DEV",
            name="Группа разработки",
            full_name="Группа разработки",
            parent_code="IT",
            is_active=True
        )
        
        assert department.parent_code == "IT"

    def test_department_inactive(self):
        """Неактивное подразделение"""
        department = Department(
            id=3,
            code="HR",
            name="Отдел кадров",
            full_name="Отдел кадров",
            is_active=False
        )
        
        assert department.is_active is False
