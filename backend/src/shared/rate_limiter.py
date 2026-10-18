# src/shared/rate_limiter.py
"""
Rate limiting middleware для FastAPI с использованием Redis.

Использует slowapi для интеграции с FastAPI.
"""

import logging
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

logger = logging.getLogger(__name__)

# Инициализация лимитера
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])


def handle_rate_limited(request, exc):
    """Обработчик превышения лимита."""
    logger.warning(f"Rate limit exceeded for {request.client.host}")
    from fastapi import Response
    return Response(
        status_code=429,
        content={"detail": "Слишком много запросов. Попробуйте позже."},
        headers={"Retry-After": "60"},
    )


def setup_rate_limiting(app):
    """Настраивает rate limiting для приложения."""
    from fastapi import Request
    
    # Добавляем обработчик
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, handle_rate_limited)
    
    logger.info("Rate limiting enabled: 50 requests/hour, 200 requests/day")
