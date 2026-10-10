# backend/src/infrastructure/db/models/rfid_api_key.py
"""Модель API-ключа для RFID-сканера"""
from datetime import datetime
import secrets

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Index,
    Integer,
    String,
    Text,
)
from . import Base


class RfidApiKey(Base):
    """API-ключ для аутентификации RFID-сканера"""
    __tablename__ = "rfid_api_keys"

    id = Column(Integer, primary_key=True)
    
    # Название ключа (для идентификации: "Сканер цех 1", "Десктоп Windows")
    name = Column(String(100), nullable=False)
    
    # Хеш API-ключа (хранится хеш, не сам ключ)
    key_hash = Column(String(64), nullable=False, unique=True, index=True)
    
    # Префикс ключа (первые 8 символов, чтобы показать админу)
    key_prefix = Column(String(8), nullable=False)
    
    # Активен ли ключ
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Кто создал
    created_by = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    last_used_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index("idx_rfid_api_keys_created_at", "created_at"),
        Index("idx_rfid_api_keys_is_active", "is_active"),
    )

    @staticmethod
    def generate_key() -> str:
        """Генерирует новый случайный API-ключ"""
        return f"rfid_{secrets.token_urlsafe(48)}"

    def __repr__(self) -> str:
        return f"<RfidApiKey(id={self.id}, name='{self.name}', prefix='{self.key_prefix}')>"
