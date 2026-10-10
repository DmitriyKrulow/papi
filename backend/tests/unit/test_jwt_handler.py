# backend/tests/unit/test_jwt_handler.py
"""Unit-тесты для JWT handler (без БД)"""
import os
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

# Устанавливаем переменные окружения перед импортом
os.environ["SECRET_KEY"] = "test-secret-key-for-unit-tests-only-12345"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"

from src.core.security.jwt_handler import (
    create_access_token,
    verify_token,
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)


class TestJWTConstants:
    """Тесты констант JWT"""

    def test_secret_key_set(self):
        """SECRET_KEY должен быть установлен"""
        assert SECRET_KEY is not None
        assert len(SECRET_KEY) > 0

    def test_algorithm_is_hs256(self):
        """ALGORITHM должен быть HS256"""
        assert ALGORITHM == "HS256"

    def test_access_token_expire_minutes(self):
        """ACCESS_TOKEN_EXPIRE_MINUTES должен быть числом"""
        assert ACCESS_TOKEN_EXPIRE_MINUTES > 0


class TestCreateAccessToken:
    """Тесты создания токенов"""

    def test_create_token_basic(self):
        """Создание базового токена"""
        data = {"sub": "user123", "role": "admin"}
        token = create_access_token(data)
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_token_has_three_parts(self):
        """Токен должен состоять из трёх частей (header.payload.signature)"""
        data = {"sub": "user123"}
        token = create_access_token(data)
        parts = token.split(".")
        assert len(parts) == 3

    def test_token_contains_sub(self):
        """Токен должен содержать sub"""
        data = {"sub": "test_user_456"}
        token = create_access_token(data)
        payload = verify_token(token)
        assert payload["sub"] == "test_user_456"

    def test_token_contains_exp(self):
        """Токен должен содержать exp"""
        data = {"sub": "user123"}
        token = create_access_token(data)
        payload = verify_token(token)
        assert "exp" in payload

    def test_token_contains_iat(self):
        """Токен должен содержать iat"""
        data = {"sub": "user123"}
        token = create_access_token(data)
        payload = verify_token(token)
        assert "iat" in payload

    def test_token_with_custom_expiry(self):
        """Токен с пользовательским сроком"""
        data = {"sub": "user123"}
        expiry = timedelta(minutes=15)
        token = create_access_token(data, expires_delta=expiry)
        payload = verify_token(token)
        assert "exp" in payload

    def test_token_does_not_modify_original_data(self):
        """Исходные данные не должны модифицироваться"""
        data = {"sub": "user123", "role": "admin"}
        original_data = data.copy()
        create_access_token(data)
        assert data == original_data

    def test_token_with_additional_claims(self):
        """Токен с дополнительными claim'ами"""
        data = {
            "sub": "user123",
            "role": "admin",
            "department_id": 5,
            "permissions": ["read", "write"],
        }
        token = create_access_token(data)
        payload = verify_token(token)
        assert payload["sub"] == "user123"
        assert payload["role"] == "admin"
        assert payload["department_id"] == 5


class TestVerifyToken:
    """Тесты верификации токенов"""

    def test_verify_valid_token(self):
        """Верификация валидного токена"""
        data = {"sub": "user123", "role": "admin"}
        token = create_access_token(data)
        payload = verify_token(token)
        assert payload["sub"] == "user123"
        assert payload["role"] == "admin"

    def test_verify_token_returns_dict(self):
        """verify_token должен возвращать dict"""
        data = {"sub": "user123"}
        token = create_access_token(data)
        payload = verify_token(token)
        assert isinstance(payload, dict)

    def test_verify_token_contains_exp(self):
        """Верифицированный токен должен содержать exp"""
        data = {"sub": "user123"}
        token = create_access_token(data)
        payload = verify_token(token)
        assert "exp" in payload
        assert isinstance(payload["exp"], (int, float))


class TestTokenExpiration:
    """Тесты истечения токенов"""

    def test_token_has_future_expiry(self):
        """Токен должен иметь exp в будущем"""
        data = {"sub": "user123"}
        token = create_access_token(data)
        payload = verify_token(token)
        exp = datetime.utcfromtimestamp(payload["exp"])
        assert exp > datetime.utcnow()

    def test_custom_expiry_shorter(self):
        """Пользовательский expiry короче дефолтного"""
        data = {"sub": "user123"}
        expiry = timedelta(minutes=5)
        token = create_access_token(data, expires_delta=expiry)
        payload = verify_token(token)
        exp = datetime.utcfromtimestamp(payload["exp"])
        assert exp - datetime.utcnow() <= timedelta(minutes=6)

    def test_custom_expiry_longer(self):
        """Пользовательский expiry длиннее дефолтного"""
        data = {"sub": "user123"}
        expiry = timedelta(hours=2)
        token = create_access_token(data, expires_delta=expiry)
        payload = verify_token(token)
        exp = datetime.utcfromtimestamp(payload["exp"])
        assert exp - datetime.utcnow() >= timedelta(hours=1)


class TestTokenEdgeCases:
    """Тесты граничных случаев"""

    def test_empty_data(self):
        """Токен с пустыми данными"""
        token = create_access_token({})
        assert token is not None
        payload = verify_token(token)
        assert "exp" in payload

    def test_token_with_none_value(self):
        """Токен с None значением"""
        data = {"sub": None}
        token = create_access_token(data)
        assert token is not None

    def test_token_with_numeric_sub(self):
        """Токен с numeric sub"""
        data = {"sub": 12345}
        token = create_access_token(data)
        payload = verify_token(token)
        assert payload["sub"] == 12345

    def test_token_with_boolean_value(self):
        """Токен с boolean значением"""
        data = {"is_admin": True}
        token = create_access_token(data)
        payload = verify_token(token)
        assert payload["is_admin"] is True
