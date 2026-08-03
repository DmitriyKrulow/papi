from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Column,
    Date,
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


class InventoryCheck(Base):
    """Проверка инвентаризации"""
    __tablename__ = "inventory_checks"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    check_date = Column(Date, nullable=False)

    # Тип проверки: full, by_room, by_employee, by_responsible
    check_type = Column(String(50), nullable=False, default="full")
    scope_id = Column(Integer, nullable=True)  # ID комнаты, сотрудника и т.д.
    scope_name = Column(String(255), nullable=True)  # Название объекта проверки

    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)

    total_checked = Column(Integer, nullable=False, default=0)
    found = Column(Integer, nullable=False, default=0)
    missing = Column(Integer, nullable=False, default=0)
    surplus = Column(Integer, nullable=False, default=0)

    status = Column(String(50), nullable=False, default="draft")  # draft, in_progress, completed, cancelled

    responsible_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    commission_members = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.now)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_inventory_checks_check_date", "check_date"),
        Index("idx_inventory_checks_department_id", "department_id"),
        Index("idx_inventory_checks_status", "status"),
        Index("idx_inventory_checks_created_at", "created_at"),
    )

    department = relationship("Department", back_populates="inventory_checks")
    responsible = relationship("User", foreign_keys=[responsible_id], back_populates="inventory_checks")
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_inventory_checks")
    asset_photos = relationship("AssetPhoto", back_populates="inventory_check")
    items = relationship("InventoryCheckItem", back_populates="inventory_check", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<InventoryCheck(id={self.id}, name='{self.name}', type='{self.check_type}', status='{self.status}')>"


