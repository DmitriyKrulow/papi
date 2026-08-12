# backend/src/core/services/notification_scheduler.py
"""Простой планировщик уведомлений.

Запускается при старте приложения и периодически проверяет условия
для генерации уведомлений.
"""
import logging
import threading
import time
from typing import Optional

from src.infrastructure.db.init_db import SessionLocal
from src.core.services.notification_generator import NotificationGenerator

logger = logging.getLogger(__name__)


class NotificationScheduler:
    """Планировщик автоматической генерации уведомлений."""

    def __init__(self, interval_seconds: int = 3600):  # 1 час по умолчанию
        self.interval = interval_seconds
        self._thread: Optional[threading.Thread] = None
        self._running = False

    def start(self):
        """Запускает планировщик в фоновом потоке."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info(f"NotificationScheduler started (interval: {self.interval}s)")

    def stop(self):
        """Останавливает планировщик."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("NotificationScheduler stopped")

    def _run(self):
        """Основной цикл планировщика."""
        while self._running:
            try:
                self._check_and_generate()
            except Exception as e:
                logger.error(f"NotificationScheduler error: {e}")
            time.sleep(self.interval)

    def _check_and_generate(self):
        """Проверяет и генерирует уведомления."""
        db = SessionLocal()
        try:
            generator = NotificationGenerator(db)
            results = generator.generate_all()
            total = sum(results.values())
            if total > 0:
                logger.info(f"NotificationScheduler: generated {total} notifications")
        except Exception as e:
            logger.error(f"Failed to generate notifications: {e}")
        finally:
            db.close()

    def run_once(self):
        """Запускает проверку один раз (для ручного вызова)."""
        db = SessionLocal()
        try:
            generator = NotificationGenerator(db)
            results = generator.generate_all()
            total = sum(results.values())
            logger.info(f"NotificationScheduler (manual): generated {total} notifications: {results}")
            return results
        except Exception as e:
            logger.error(f"Failed to generate notifications: {e}")
            return {}
        finally:
            db.close()
