# backend/src/infrastructure/db/models/notification.py
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from . import Base


class Notification(Base):
    """Модель уведомлений"""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Тип уведомления: inventory, repair, warranty, maintenance
    type = Column(String(50), nullable=False, default="general")
    
    # Заголовок и тело сообщения
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    
    # Ссылка на связанный объект
    reference_type = Column(String(50), nullable=True)  # inventory_check, repair_request, asset
    reference_id = Column(Integer, nullable=True)
    
    # Уникальный ключ события внутри типа (например "warn_30", "overdue_7") — для дедупликации
    reference_key = Column(String(50), nullable=True)
    
    # Статус отправки
    email_sent = Column(Boolean, nullable=False, default=False)
    email_sent_at = Column(DateTime, nullable=True)
    max_sent = Column(Boolean, nullable=False, default=False)
    max_sent_at = Column(DateTime, nullable=True)
    
    # Статус прочтения
    is_read = Column(Boolean, nullable=False, default=False)
    read_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    __table_args__ = (
        Index("idx_notifications_user_id", "user_id"),
        Index("idx_notifications_type", "type"),
        Index("idx_notifications_created_at", "created_at"),
        Index("idx_notifications_is_read", "is_read"),
    )

    user = relationship("User", foreign_keys=[user_id], back_populates="notifications")

    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, type='{self.type}', user_id={self.user_id})>"
