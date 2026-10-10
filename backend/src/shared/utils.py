"""Общие утилиты"""
import os
from typing import Optional


def get_frontend_url(db_session: Optional[object] = None) -> str:
    """
    Возвращает базовый URL фронтенда для генерации ссылок в QR-кодах.
    
    Приоритет источника:
    1. Настройка `frontend_url` из таблицы `system_settings` в БД
    2. Переменная окружения `FRONTEND_URL`
    3. Дефолтное значение (пустая строка — caller должен подставить свой default)
    
    Args:
        db_session: SQLAlchemy session для чтения из БД. Если None — только env.
    
    Returns:
        Базовый URL фронтенда (без trailing slash).
    """
    # 1. Пытаемся прочитать из БД
    if db_session is not None:
        try:
            from src.infrastructure.db.models.system_settings import SystemSettings
            settings = db_session.query(SystemSettings).first()
            if settings and settings.frontend_url:
                url = settings.frontend_url.rstrip("/")
                return url
        except Exception:
            pass  # игнорируем ошибки БД, переходим к env
    
    # 2. Переменная окружения
    env_url = os.getenv("FRONTEND_URL", "").strip()
    if env_url:
        return env_url.rstrip("/")
    
    # 3. Дефолт — caller должен подставить свой fallback
    return ""
