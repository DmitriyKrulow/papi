# backend/src/infrastructure/db/models/system_settings.py
"""Модель глобальных настроек системы (включая HTTPS)"""
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    Text,
)
from . import Base


class SystemSettings(Base):
    """Глобальные настройки системы"""
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True)
    
    # HTTPS настройки
    https_enabled = Column(Integer, nullable=False, default=1)  # 1 = true, 0 = false
    https_domain = Column(String(255), nullable=True)  # Доменное имя (punycode)
    https_email = Column(String(255), nullable=True)  # Email для Let's Encrypt
    https_port = Column(Integer, nullable=False, default=443)
    
    # Основные настройки
    system_name = Column(String(255), nullable=True, default="PAPI Система")
    frontend_url = Column(String(500), nullable=True)
    
    # Флаг для отображения предупреждения о HTTP
    http_warning_enabled = Column(Integer, nullable=False, default=1)
    
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<SystemSettings(id={self.id})>"
