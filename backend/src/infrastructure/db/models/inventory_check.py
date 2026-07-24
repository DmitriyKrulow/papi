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
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class InventoryCheck(Base):
    """?????? ??????????????"""
    __tablename__ = "inventory_checks"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    check_date = Column(Date, nullable=False)

    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)

    total_checked = Column(Integer, nullable=False, default=0)
    found = Column(Integer, nullable=False, default=0)
    missing = Column(Integer, nullable=False, default=0)
    surplus = Column(Integer, nullable=False, default=0)

    status = Column(String(50), nullable=False, default="created")

    responsible_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    commission_members = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.now)
    completed_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_inventory_checks_check_date", "check_date"),
        Index("idx_inventory_checks_department_id", "department_id"),
        Index("idx_inventory_checks_status", "status"),
        Index("idx_inventory_checks_created_at", "created_at"),
    )

    # Relationships
    department = relationship("Department", backref="inventory_checks")
    responsible = relationship("User", backref="inventory_checks")

    def __repr__(self) -> str:
        return f"<InventoryCheck(id={self.id}, name='{self.name}', date={self.check_date}, status='{self.status}')>"


