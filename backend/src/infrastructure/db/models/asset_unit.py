# backend/src/infrastructure/db/models/asset_unit.py
"""Модель отдельных физических единиц актива (AssetUnit)

Для активов с quantity > 1 создаются отдельные единицы:
- Инвентарный номер: 6464646
- Единицы: 6464646-1, 6464646-2, 6464646-3

Каждая единица может быть выдана отдельному сотруднику.
"""
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


class AssetUnit(Base):
    """
    Физическая единица актива.
    
    Используется для активов с quantity > 1, где каждая единица
    может быть выдана отдельному сотруднику.
    
    Пример:
    - Asset: Штампы (inventory_number=6464646, quantity=3)
    - AssetUnit: 6464646-1 (выдан Иванову)
    - AssetUnit: 6464646-2 (выдан Петрову)
    - AssetUnit: 6464646-3 (на складе)
    """
    __tablename__ = "asset_units"

    id = Column(Integer, primary_key=True)
    
    # Привязка к родительскому активу
    asset_id = Column(
        Integer, ForeignKey("assets.id"), nullable=False, index=True
    )
    
    # Номер единицы (1, 2, 3...)
    unit_number = Column(Integer, nullable=False)
    
    # Уникальный идентификатор единицы (напр. "6464646-1")
    unique_identifier = Column(
        String(100), nullable=False, unique=True, index=True
    )
    
    # Текущий сотрудник, у которого находится единица
    current_employee_id = Column(
        Integer, ForeignKey("employees.id"), nullable=True, index=True
    )
    
    # Текущее подразделение
    current_department_code = Column(String(50), nullable=True, index=True)
    
    # Статус единицы
    status = Column(String(50), nullable=False, default="active")
    # active, in_repair, written_off, lost, damaged
    
    # Дата последней передачи
    last_transfer_date = Column(DateTime, nullable=True)
    
    # Примечания
    notes = Column(Text, nullable=True)
    
    # RFID метка для этой единицы (если есть)
    rfid_tag = Column(String(100), nullable=True, unique=True, index=True)
    
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )

    __table_args__ = (
        Index("idx_asset_units_asset_id", "asset_id"),
        Index("idx_asset_units_status", "status"),
        Index("idx_asset_units_is_active", "is_active"),
    )

    # Relationships
    asset = relationship("Asset", foreign_keys=[asset_id])
    current_employee = relationship("Employee", foreign_keys=[current_employee_id])
    
    # История передач этой единицы
    transfer_history = relationship(
        "AssetTransferHistory",
        back_populates="asset_unit",
        foreign_keys="AssetTransferHistory.asset_unit_id",
        cascade="all, delete-orphan",
    )

    def get_full_identifier(self) -> str:
        """Получить полный идентификатор единицы"""
        return f"{self.unique_identifier}"

    def __repr__(self) -> str:
        return f"<AssetUnit(id={self.id}, asset_id={self.asset_id}, unit={self.unit_number}, identifier='{self.unique_identifier}')>"
