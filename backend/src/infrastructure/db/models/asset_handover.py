# backend/src/infrastructure/db/models/asset_handover.py
"""Модель передачи/возврата имущества — фиксация действий с МОЛ"""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
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


class AssetHandover(Base):
    """
    Передача/возврат имущества.
    
    Фиксирует:
    - КТО передал (handover_by)
    - КТО получил (received_by)
    - КАКОЙ актив (asset_id)
    - КОГДА (date)
    - ЗАЧЕМ (reason)
    - СРОК ВОЗВРАТА (return_deadline)
    - Статус (active / returned / overdue)
    """
    __tablename__ = "asset_handovers"

    id = Column(Integer, primary_key=True)
    
    # Актив
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    
    # Передал
    handover_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Получил
    received_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Тип действия: handover / return
    action_type = Column(String(20), nullable=False, default="handover", index=True)
    
    # Причина передачи
    reason = Column(Text, nullable=True)
    
    # Срок возврата (для временной передачи)
    return_deadline = Column(DateTime, nullable=True)
    
    # Фактическая дата возврата
    actual_return_date = Column(DateTime, nullable=True)
    
    # Закрыта ли передача
    is_closed = Column(Boolean, nullable=False, default=False)
    
    # Комментарий
    comment = Column(Text, nullable=True)
    
    # RFID-метка (для автоматической фиксации)
    rfid_tag = Column(String(100), nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    
    __table_args__ = (
        Index("idx_asset_handovers_asset_id", "asset_id"),
        Index("idx_asset_handovers_handover_by", "handover_by"),
        Index("idx_asset_handovers_received_by", "received_by"),
        Index("idx_asset_handovers_action_type", "action_type"),
        Index("idx_asset_handovers_is_closed", "is_closed"),
        Index("idx_asset_handovers_return_deadline", "return_deadline"),
    )
    
    asset = relationship("Asset", foreign_keys=[asset_id])
    handover_by_user = relationship("User", foreign_keys=[handover_by])
    received_by_user = relationship("User", foreign_keys=[received_by])
    
    def __repr__(self) -> str:
        return (
            f"<AssetHandover(id={self.id}, asset={self.asset_id}, "
            f"action={self.action_type}, closed={self.is_closed})>"
        )
