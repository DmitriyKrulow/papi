# src/shared/cache.py
"""
Redis кэш для FastAPI.

Предоставляет простой интерфейс для кэширования данных.
"""

import json
import logging
from typing import Any, Optional
from datetime import timedelta

import redis

logger = logging.getLogger(__name__)

# Глобальный Redis клиент (инициализируется при первом использовании)
_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    """Получает Redis клиент (создаёт при необходимости)."""
    global _redis_client
    if _redis_client is None:
        from dotenv import load_dotenv
        import os
        load_dotenv()
        
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        try:
            _redis_client = redis.from_url(redis_url, decode_responses=True)
            _redis_client.ping()
            logger.info("Redis connected successfully")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Cache disabled.")
            _redis_client = None
    return _redis_client


def cache_get(key: str) -> Optional[Any]:
    """Получает значение из кэша."""
    client = get_redis_client()
    if client is None:
        return None
    
    try:
        value = client.get(key)
        if value:
            return json.loads(value)
    except Exception as e:
        logger.warning(f"Cache GET error: {e}")
    return None


def cache_set(key: str, value: Any, expire_seconds: int = 300) -> bool:
    """Сохраняет значение в кэш."""
    client = get_redis_client()
    if client is None:
        return False
    
    try:
        client.setex(key, expire_seconds, json.dumps(value, ensure_ascii=False))
        return True
    except Exception as e:
        logger.warning(f"Cache SET error: {e}")
        return False


def cache_delete(key: str) -> bool:
    """Удаляет значение из кэша."""
    client = get_redis_client()
    if client is None:
        return False
    
    try:
        client.delete(key)
        return True
    except Exception as e:
        logger.warning(f"Cache DELETE error: {e}")
        return False


def cache_invalidate_pattern(pattern: str) -> int:
    """Инвалидирует все ключи по паттерну."""
    client = get_redis_client()
    if client is None:
        return 0
    
    try:
        keys = client.keys(pattern)
        if keys:
            return client.delete(*keys)
    except Exception as e:
        logger.warning(f"Cache invalidate error: {e}")
    return 0
