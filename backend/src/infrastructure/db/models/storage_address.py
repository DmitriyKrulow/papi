# backend/src/infrastructure/db/models/storage_address.py
"""Модель адресного хранения — стеллажи, полки, ячейки"""
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


class StorageAddress(Base):
    """
    Адрес хранения имущества (стеллаж, полка, ячейка).
    
    Для складских помещений иерархия:
    Room (warehouse) → WarehouseLocation (зона/участок) → StorageAddress (стеллаж/rack)
        → StorageAddress (полка/shelf) → StorageAddress (ячейка/cell)
    
    Для не-складских помещений иерархия:
    Building (Корпус) → Floor (Этаж) → Zone (Зона) → Aisle (Ряд) → Shelf (Стеллаж) → Cell (Ячейка)
    
    Пример полного адреса склада:
    "Склад №3 → Зона приёмки → Стеллаж A-01 → Полка 2 → Ячейка 5"
    """
    __tablename__ = "storage_addresses"

    id = Column(Integer, primary_key=True)
    
    # Иерархия
    parent_id = Column(Integer, ForeignKey("storage_addresses.id"), nullable=True, index=True)
    
    # Тип уровня
    level = Column(String(20), nullable=False, default="cell", index=True)
    # building, floor, zone, aisle, rack, shelf, cell
    # rack — стеллаж/секция, shelf — полка стеллажа, cell — ячейка хранения
    
    # Название/номер
    name = Column(String(100), nullable=False)
    code = Column(String(50), nullable=True, index=True)  # Код адреса (напр. "A-01-2-5")
    
    # Привязка к складской локации (зоне/участку склада)
    warehouse_location_id = Column(
        Integer, ForeignKey("warehouse_locations.id"), nullable=True, index=True
    )
    
    # Привязка к комнате
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=True, index=True)
    
    # Описание
    description = Column(Text, nullable=True)
    
    # Вместимость (количество ячеек на уровне, для валидации)
    capacity = Column(Integer, nullable=True)
    
    # Текущее количество объектов
    current_count = Column(Integer, nullable=False, default=0)
    
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    
    __table_args__ = (
        Index("idx_storage_addresses_parent_id", "parent_id"),
        Index("idx_storage_addresses_level", "level"),
        Index("idx_storage_addresses_room_id", "room_id"),
        Index("idx_storage_addresses_warehouse_location_id", "warehouse_location_id"),
        Index("idx_storage_addresses_code", "code"),
        Index("idx_storage_addresses_is_active", "is_active"),
    )
    
    # Self-referential relationships
    parent = relationship("StorageAddress", remote_side=[id], backref="children")
    
    # Assets at this address
    assets = relationship("Asset", back_populates="storage_address")
    
    # Room relationship
    room = relationship("Room", foreign_keys=[room_id], back_populates="storage_addresses")
    
    # Warehouse location relationship
    warehouse_location = relationship(
        "WarehouseLocation",
        foreign_keys=[warehouse_location_id],
        back_populates="storage_addresses",
    )
    
    def get_full_address(self) -> str:
        """Получить полный адрес от корня до текущей ячейки"""
        path = []
        node = self
        while node:
            path.insert(0, node.name)
            node = node.parent
        return " → ".join(path)
    
    def get_address_path(self) -> list:
        """Получить список всех уровней адреса"""
        path = []
        node = self
        while node:
            path.insert(0, node)
            node = node.parent
        return path
    
    def __repr__(self) -> str:
        return f"<StorageAddress(id={self.id}, name='{self.name}', level='{self.level}')>"
