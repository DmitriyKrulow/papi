# src/infrastructure/db/models/brute_force_log.py
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import declarative_base

from . import Base


class BruteForceLog(Base):
    """
    Лог попыток входа для защиты от брутфорса.
    Хранит все неудачные и успешные попытки авторизации.
    """
    __tablename__ = "brute_force_logs"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False, index=True, comment="Имя пользователя")
    ip_address = Column(String(45), nullable=False, comment="IP адрес (IPv4/IPv6)")
    is_success = Column(Integer, nullable=False, default=0, comment="0 = неудача, 1 = успех")
    created_at = Column(DateTime, nullable=False, default=datetime.now, index=True)

    __table_args__ = (
        # Индекс для группировки по пользователю и времени
        # (Commented out if not supported by current DB dialect)
        # Index("idx_bfl_username_time", "username", "created_at"),
    )

    def __repr__(self) -> str:
        status = "SUCCESS" if self.is_success else "FAILURE"
        return f"<BruteForceLog(username='{self.username}', ip='{self.ip_address}', status={status})>"
