# src/infrastructure/db/models/audit_log.py
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from . import Base


class AuditLog(Base):
    """Журнал аудита — фиксирует все значимые действия в системе"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)

    # Время события
    created_at = Column(DateTime, nullable=False, default=datetime.now, index=True)

    # Кто выполнил действие
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    user = relationship("User", foreign_keys=[user_id])

    # IP-адрес (сохраняем как строку, т.к. IPv4/IPv6)
    ip_address = Column(String(45), nullable=True)

    # Метаданные запроса
    method = Column(String(10), nullable=True)           # GET, POST, PUT, PATCH, DELETE
    path = Column(String(500), nullable=True)             # /api/assets/123
    user_agent = Column(String(500), nullable=True)       # Браузер/клиент

    # Сущность и действие
    entity_type = Column(String(100), nullable=False, index=True)   # "Asset", "User", "RepairRequest"
    entity_id = Column(Integer, nullable=False, index=True)         # ID записи в соответствующей таблице

    action = Column(String(50), nullable=False, index=True)         # "create", "update", "delete", "login", "logout"

    # Старые и новые значения (JSON)
    old_values = Column(Text, nullable=True)      # JSON: старые значения
    new_values = Column(Text, nullable=True)      # JSON: новые значения
    diff_summary = Column(String(500), nullable=True)  # Краткое описание изменений: "status: draft -> active"

    # Комментарий (для особых действий)
    comment = Column(String(500), nullable=True)

    __table_args__ = (
        Index("idx_audit_logs_entity", "entity_type", "entity_id"),
        Index("idx_audit_logs_action", "action"),
        Index("idx_audit_logs_created_at", "created_at"),
        Index("idx_audit_logs_user", "user_id", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<AuditLog(id={self.id}, user={self.user_id}, "
            f"{self.entity_type}/{self.entity_id} {self.action} "
            f"at {self.created_at})>"
        )
