# backend/tests/unit/test_utils.py
"""Unit-тесты для общих утилит (без БД)"""
import os
import pytest
from unittest.mock import MagicMock, patch


class TestGetFrontendUrl:
    """Тесты функции get_frontend_url"""

    def test_env_variable_takes_precedence(self):
        """Переменная окружения должна возвращаться"""
        with patch.dict(os.environ, {"FRONTEND_URL": "https://example.com"}):
            from src.shared.utils import get_frontend_url
            # Без db_session — только env
            url = get_frontend_url(db_session=None)
            assert url == "https://example.com"

    def test_env_variable_strips_trailing_slash(self):
        """Trailing slash должен удаляться"""
        with patch.dict(os.environ, {"FRONTEND_URL": "https://example.com/"}):
            # Перезагружаем модуль для применения новых env
            import importlib
            import src.shared.utils as utils
            importlib.reload(utils)
            url = utils.get_frontend_url(db_session=None)
            assert url == "https://example.com"

    def test_env_variable_strips_multiple_trailing_slashes(self):
        """Несколько trailing slash должны удаляться"""
        with patch.dict(os.environ, {"FRONTEND_URL": "https://example.com///"}):
            import importlib
            import src.shared.utils as utils
            importlib.reload(utils)
            url = utils.get_frontend_url(db_session=None)
            assert url == "https://example.com"

    def test_empty_env_returns_empty_string(self):
        """Пустой env должен возвращать пустую строку"""
        with patch.dict(os.environ, {"FRONTEND_URL": ""}):
            import importlib
            import src.shared.utils as utils
            importlib.reload(utils)
            url = utils.get_frontend_url(db_session=None)
            assert url == ""

    def test_env_variable_with_whitespace_stripped(self):
        """Пробелы в env должны удаляться"""
        with patch.dict(os.environ, {"FRONTEND_URL": "  https://example.com  "}):
            import importlib
            import src.shared.utils as utils
            importlib.reload(utils)
            url = utils.get_frontend_url(db_session=None)
            assert url == "https://example.com"

    def test_unset_env_returns_empty_string(self):
        """Неустановленный env должен возвращать пустую строку"""
        env = os.environ.copy()
        env.pop("FRONTEND_URL", None)
        with patch.dict(os.environ, env, clear=True):
            import importlib
            import src.shared.utils as utils
            importlib.reload(utils)
            url = utils.get_frontend_url(db_session=None)
            assert url == ""

    def test_db_session_none_returns_env_only(self):
        """db_session=None не должен обращаться к БД"""
        with patch.dict(os.environ, {"FRONTEND_URL": "https://test.local"}):
            from src.shared.utils import get_frontend_url
            url = get_frontend_url(db_session=None)
            assert url == "https://test.local"


class TestGetFrontendUrlWithDb:
    """Тесты get_frontend_url с БД"""

    def test_db_setting_takes_precedence_over_env(self):
        """Настройка из БД должна иметь приоритет над env"""
        mock_db = MagicMock()
        mock_settings = MagicMock()
        mock_settings.frontend_url = "https://db-setting.com"
        mock_db.query.return_value.first.return_value = mock_settings

        with patch.dict(os.environ, {"FRONTEND_URL": "https://env-setting.com"}):
            import importlib
            import src.shared.utils as utils
            importlib.reload(utils)
            url = utils.get_frontend_url(db_session=mock_db)
            assert url == "https://db-setting.com"

    def test_db_exception_falls_back_to_env(self):
        """Ошибка БД должна приводить к fallback на env"""
        mock_db = MagicMock()
        mock_db.query.side_effect = Exception("DB connection failed")

        with patch.dict(os.environ, {"FRONTEND_URL": "https://fallback.com"}):
            import importlib
            import src.shared.utils as utils
            importlib.reload(utils)
            url = utils.get_frontend_url(db_session=mock_db)
            assert url == "https://fallback.com"

    def test_db_none_frontend_url_falls_back_to_env(self):
        """None в БД должен приводить к fallback на env"""
        mock_db = MagicMock()
        mock_settings = MagicMock()
        mock_settings.frontend_url = None
        mock_db.query.return_value.first.return_value = mock_settings

        with patch.dict(os.environ, {"FRONTEND_URL": "https://fallback.com"}):
            import importlib
            import src.shared.utils as utils
            importlib.reload(utils)
            url = utils.get_frontend_url(db_session=mock_db)
            assert url == "https://fallback.com"


class TestGetFrontendUrlNoDbNoEnv:
    """Тесты get_frontend_url без БД и env"""

    def test_no_db_no_env_returns_empty(self):
        """Без БД и env должна возвращаться пустая строка"""
        env = os.environ.copy()
        env.pop("FRONTEND_URL", None)
        with patch.dict(os.environ, env, clear=True):
            import importlib
            import src.shared.utils as utils
            importlib.reload(utils)
            url = utils.get_frontend_url(db_session=None)
            assert url == ""
