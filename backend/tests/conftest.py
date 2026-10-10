# backend/tests/conftest.py
"""Общие фикстуры для тестов"""
import os
import pytest
from unittest.mock import MagicMock, patch

# Устанавливаем тестовую БД
os.environ["DATABASE_URL"] = "postgresql://test:test@localhost/test"
os.environ["SECRET_KEY"] = "test-secret-key-for-unit-tests-only-12345"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"


# ============================================================================
# Фикстуры с тестовыми данными
# ============================================================================

@pytest.fixture
def sample_asset_data():
    """Тестовые данные актива"""
    return {
        "inventory_number": "INV001",
        "name": "Ноутбук Dell",
        "model": "Latitude 5520",
        "status": "active",
        "purchase_price": 75000,
        "purchase_date": "2024-01-15",
    }


@pytest.fixture
def sample_user_data():
    """Тестовые данные пользователя"""
    return {
        "username": "test_user",
        "email": "test@example.com",
        "full_name": "Тестовый Пользователь",
        "role": "user",
    }


@pytest.fixture
def sample_admin_data():
    """Тестовые данные администратора"""
    return {
        "username": "test_admin",
        "email": "admin@test.com",
        "full_name": "Тестовый Администратор",
        "role": "admin",
    }


@pytest.fixture
def sample_department_data():
    """Тестовые данные подразделения"""
    return {
        "code": "IT",
        "name": "Отдел информационных технологий",
        "head": "Иванов И.И.",
    }


@pytest.fixture
def sample_employee_data():
    """Тестовые данные сотрудника"""
    return {
        "first_name": "Иван",
        "last_name": "Иванов",
        "middle_name": "Иванович",
        "position": "Системный администратор",
        "department_code": "IT",
    }


@pytest.fixture
def sample_rfid_key_data():
    """Тестовые данные RFID ключа"""
    return {
        "name": "Тестовый сканер",
        "api_key": "rfid_test_key_12345",
        "is_active": True,
    }


@pytest.fixture
def sample_storage_address_data():
    """Тестовые данные адреса хранения"""
    return {
        "name": "Здание А",
        "level": "building",
        "code": "BLD-001",
        "capacity": 100,
    }


@pytest.fixture
def sample_handover_data():
    """Тестовые данные передачи актива"""
    return {
        "asset_id": 1,
        "received_by_user_id": 2,
        "reason": "Временная передача",
        "return_deadline_days": 7,
    }


@pytest.fixture
def sample_inventory_data():
    """Тестовые данные инвентаризации"""
    return {
        "name": "Инвентаризация IT отдела",
        "check_type": "department",
        "target_id": 1,
        "scheduled_date": "2024-10-15T10:00:00",
    }


# ============================================================================
# Фикстуры для моков
# ============================================================================

@pytest.fixture
def mock_db_session():
    """Мок сессии базы данных"""
    session = MagicMock()
    session.query.return_value = []
    session.add = MagicMock()
    session.commit = MagicMock()
    session.refresh = MagicMock()
    session.close = MagicMock()
    return session


@pytest.fixture
def mock_current_user():
    """Мок текущего пользователя"""
    user = MagicMock()
    user.id = 1
    user.username = "test_user"
    user.email = "test@example.com"
    user.full_name = "Тестовый Пользователь"
    user.role = "user"
    user.is_active = True
    return user


@pytest.fixture
def mock_current_admin():
    """Мок текущего администратора"""
    admin = MagicMock()
    admin.id = 1
    admin.username = "test_admin"
    admin.email = "admin@test.com"
    admin.full_name = "Тестовый Администратор"
    admin.role = "admin"
    admin.is_active = True
    return admin


# ============================================================================
# Фикстуры для FastAPI test client
# ============================================================================

@pytest.fixture
def client(monkeypatch):
    """
    Test client для API.
    
    Создаёт мок-версию get_db, чтобы тесты не требовали реальную БД.
    """
    from fastapi.testclient import TestClient
    from src.infrastructure.main import app
    
    # Мокаем get_db чтобы не требовалась реальная БД
    def mock_get_db():
        db = MagicMock()
        db.query.return_value = []
        yield db
    
    monkeypatch.setattr(
        "src.presentation.http.routers.assets.get_db",
        mock_get_db
    )
    monkeypatch.setattr(
        "src.infrastructure.db.init_db.get_db",
        mock_get_db
    )
    
    # Мокаем аутентификацию для тестов которые не проверяют авторизацию
    def mock_get_current_user():
        return MagicMock(
            id=1,
            username="test_user",
            email="test@example.com",
            full_name="Test User",
            role="user",
            is_active=True,
        )
    
    def mock_get_current_admin():
        return MagicMock(
            id=1,
            username="test_admin",
            email="admin@test.com",
            full_name="Test Admin",
            role="admin",
            is_active=True,
        )
    
    # Применяем моки ко всем роутерам
    monkeypatch.setattr(
        "src.presentation.http.dependencies.auth.get_current_user",
        mock_get_current_user
    )
    monkeypatch.setattr(
        "src.presentation.http.dependencies.auth.get_current_admin",
        mock_get_current_admin
    )
    
    return TestClient(app)


# ============================================================================
# Фикстуры для value objects
# ============================================================================

@pytest.fixture
def sample_email():
    """Тестовый email"""
    from src.core.value_objects.email import Email
    return Email("test@example.com")


@pytest.fixture
def sample_password_hash():
    """Тестовый хеш пароля"""
    from src.core.value_objects.password_hash import PasswordHash
    return PasswordHash.from_plain_password("test_password_123")


@pytest.fixture
def sample_inventory_number():
    """Тестовый инвентарный номер"""
    from src.core.value_objects.inventory_number import InventoryNumber
    return InventoryNumber("0232026200020180000000045")


@pytest.fixture
def sample_serial_number():
    """Тестовый серийный номер"""
    from src.core.value_objects.serial_number import SerialNumber
    return SerialNumber(12345, 5)


# ============================================================================
# Автоиспользование фикстуры client
# ============================================================================

pytest_plugins = []
