# backend/src/infrastructure/db/models/notification_settings.py
"""Модель настроек уведомлений"""
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    Text,
)
from . import Base


class NotificationSettings(Base):
    """Настройки уведомлений"""
    __tablename__ = "notification_settings"

    id = Column(Integer, primary_key=True)
    
    # SMTP настройки
    smtp_host = Column(String(255), nullable=True)
    smtp_port = Column(Integer, nullable=True)
    smtp_user = Column(String(255), nullable=True)
    smtp_password = Column(String(255), nullable=True)
    sender_email = Column(String(255), nullable=True)
    
    # MAX chat настройки
    max_api_url = Column(String(500), nullable=True)
    max_api_token = Column(String(255), nullable=True)
    
    # Флаги
    enable_email = Column(Integer, nullable=False, default=1)
    enable_max = Column(Integer, nullable=False, default=0)
    
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<NotificationSettings(id={self.id})>"
