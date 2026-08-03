# backend/src/infrastructure/db/models/inventory_check_item.py
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


class InventoryCheckItem(Base):
    """Элемент инвентаризации — связь проверки с активом"""
    __tablename__ = "inventory_check_items"

    id = Column(Integer, primary_key=True)
    inventory_check_id = Column(
        Integer, ForeignKey("inventory_checks.id"), nullable=False, index=True
    )
    asset_id = Column(
        Integer, ForeignKey("assets.id"), nullable=False, index=True
    )

    # Результат проверки: found / missing / surplus
    result = Column(String(20), nullable=False, default="pending")
    comment = Column(Text, nullable=True)
    confirmed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    confirmed_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.now)

    __table_args__ = (
        Index("idx_inv_check_item_check_id", "inventory_check_id"),
        Index("idx_inv_check_item_asset_id", "asset_id"),
        Index("idx_inv_check_item_result", "result"),
        # Уникальность: один актив может быть только один раз в одной проверке
        Index("uq_inv_check_item_check_asset", "inventory_check_id", "asset_id", unique=True),
    )

    inventory_check = relationship("InventoryCheck", back_populates="items")
    asset = relationship("Asset", back_populates="inventory_check_items")
    confirmed_by_user = relationship("User", foreign_keys=[confirmed_by])

    def __repr__(self) -> str:
        return f"<InventoryCheckItem(check_id={self.inventory_check_id}, asset_id={self.asset_id}, result='{self.result}')>"