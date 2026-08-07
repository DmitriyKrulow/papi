# backend/src/infrastructure/db/models/notification_template.py
"""Модель шаблонов уведомлений"""
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    Text,
)
from . import Base


class NotificationTemplate(Base):
    """Шаблоны уведомлений"""
    __tablename__ = "notification_templates"

    id = Column(Integer, primary_key=True)
    
    # Уникальный ключ шаблона
    key = Column(String(50), nullable=False, unique=True, index=True)
    
    # Название шаблона
    name = Column(String(100), nullable=False)
    
    # Заголовок (может содержать переменные {variable})
    title_template = Column(Text, nullable=False)
    
    # Тело сообщения (может содержать переменные {variable})
    message_template = Column(Text, nullable=False)
    
    # Тип уведомления
    type = Column(String(50), nullable=False, default="general")
    
    # Активен ли шаблон
    is_active = Column(Integer, nullable=False, default=1)
    
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<NotificationTemplate(id={self.id}, key='{self.key}', name='{self.name}')>"
