# backend/src/infrastructure/db/models/warehouse_location.py
"""Модель складских локаций — зоны/участки склада"""
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


class WarehouseLocation(Base):
    """
    Складская локация — зона/участок внутри складского помещения.
    
    Иерархия склада:
    Room (warehouse) → WarehouseLocation (зона/участок) → StorageAddress (стеллаж/полка/ячейка)
    
    Пример:
    Склад №3 (room) → Зона приёмки (location) → Стеллаж A-01 (rack) → Полка 2 (shelf) → Ячейка 5 (cell)
    
    WarehouseLocation служит родительской сущностью для storage_addresses
    внутри складских помещений.
    """
    __tablename__ = "warehouse_locations"

    id = Column(Integer, primary_key=True)
    
    # Привязка к складскому помещению
    room_id = Column(
        Integer, ForeignKey("rooms.id"), nullable=False, index=True
    )
    
    # Код локации (напр. "REC-01" для зоны приёмки, "STO-02" для зоны хранения)
    code = Column(String(50), nullable=True, index=True)
    
    # Название локации
    name = Column(String(200), nullable=False)
    
    # Описание
    description = Column(Text, nullable=True)
    
    # Тип локации: receiving (приёмка), storage (хранение), shipping (отгрузка), 
    # returns (возвраты), quarantine (карантин)
    location_type = Column(String(50), nullable=False, default="storage", index=True)
    
    # Вместимость (максимальное количество storage_addresses в этой локации)
    capacity = Column(Integer, nullable=True)
    
    # Текущее количество объектов хранения
    current_count = Column(Integer, nullable=False, default=0)
    
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )

    __table_args__ = (
        Index("idx_warehouse_locations_room_id", "room_id"),
        Index("idx_warehouse_locations_code", "code"),
        Index("idx_warehouse_locations_type", "location_type"),
        Index("idx_warehouse_locations_is_active", "is_active"),
    )

    # Relationships
    room = relationship("Room", foreign_keys=[room_id], back_populates="warehouse_locations")
    
    # Storage addresses (стеллажи, полки, ячейки) в этой локации
    storage_addresses = relationship(
        "StorageAddress",
        back_populates="warehouse_location",
        foreign_keys="StorageAddress.warehouse_location_id",
        cascade="all, delete-orphan",
    )
    
    # Активы, привязанные напрямую к локации (без конкретного storage_address)
    assets = relationship(
        "Asset",
        back_populates="warehouse_location",
        foreign_keys="Asset.warehouse_location_id",
    )

    def get_full_name(self) -> str:
        """Получить полное имя локации с названием комнаты"""
        room_name = self.room.name if self.room else ""
        return f"{room_name} → {self.name}"

    def __repr__(self) -> str:
        return f"<WarehouseLocation(id={self.id}, name='{self.name}', code='{self.code or ''}', room_id={self.room_id})>"
