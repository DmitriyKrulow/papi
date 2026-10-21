# backend/src/infrastructure/db/models/room_inventory_print.py
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


class RoomInventoryPrint(Base):
    """Распечатанная опись помещения"""
    __tablename__ = "room_inventory_prints"

    id = Column(Integer, primary_key=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    room_name = Column(String(100), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    department_name = Column(String(255), nullable=True)

    # Сотрудник-подписант
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    employee_name = Column(String(255), nullable=True)
    employee_position = Column(String(255), nullable=True)

    # Количество активов в описи
    asset_count = Column(Integer, nullable=False, default=0)

    # Файл описи
    file_path = Column(String(500), nullable=True)

    # Статус подписания
    signed = Column(Boolean, nullable=False, default=False)
    signed_at = Column(DateTime, nullable=True)
    signed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Статус архивации (показывает, что опись не будет подписана)
    is_archived = Column(Boolean, nullable=False, default=False, server_default="false")
    archived_at = Column(DateTime, nullable=True)

    # Кто распечатал
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime, nullable=False, default=datetime.now)

    __table_args__ = (
        Index("idx_room_inv_print_room_id", "room_id"),
        Index("idx_room_inv_print_employee_id", "employee_id"),
        Index("idx_room_inv_print_signed", "signed"),
        Index("idx_room_inv_print_created_at", "created_at"),
        Index("idx_room_inv_print_is_archived", "is_archived"),
    )

    # Relationships
    room = relationship("Room", back_populates="inventory_prints")
    department = relationship("Department", back_populates="room_inventory_prints")
    employee = relationship("Employee", back_populates="room_inventory_prints")
    created_by_user = relationship("User", foreign_keys=[created_by_user_id])
    signed_by_user = relationship("User", foreign_keys=[signed_by_user_id])

    def __repr__(self) -> str:
        return f"<RoomInventoryPrint(id={self.id}, room='{self.room_name}', signed={self.signed})>"
