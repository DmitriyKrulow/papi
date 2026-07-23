from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

from backend.src.core.entities.repair_request import RepairPriority, RepairStatus

Base = declarative_base()


class RepairRequest(Base):
    """Модель заявки на ремонт"""
    __tablename__ = "repair_requests"

    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    priority = Column(
        Enum(RepairPriority, name="repair_priority_enum"),
        nullable=False,
        default=RepairPriority.MEDIUM,
    )
    status = Column(
        Enum(RepairStatus, name="repair_status_enum"),
        nullable=False,
        default=RepairStatus.DRAFT,
    )
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_at = Column(DateTime, nullable=True)

    desired_completion_date = Column(Date, nullable=True)
    actual_completion_date = Column(Date, nullable=True)
    deadline = Column(Date, nullable=True)

    estimated_cost = Column(Numeric(15, 2), nullable=True)
    actual_cost = Column(Numeric(15, 2), nullable=True)

    completion_notes = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)

    maintenance_record_id = Column(Integer, nullable=True)

    updated_at = Column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    __table_args__ = (
        Index("idx_repair_requests_asset_id", "asset_id"),
        Index("idx_repair_requests_status", "status"),
        Index("idx_repair_requests_priority", "priority"),
        Index("idx_repair_requests_created_by", "created_by"),
        Index("idx_repair_requests_assigned_to", "assigned_to"),
        Index("idx_repair_requests_created_at", "created_at"),
        Index("idx_repair_requests_deadline", "deadline"),
    )

    # Relationships
    asset = relationship("Asset", back_populates="repair_requests")
    created_by_user = relationship(
        "User", back_populates="repair_requests", foreign_keys=[created_by]
    )
    assigned_to_user = relationship(
        "User", back_populates="assigned_repairs", foreign_keys=[assigned_to]
    )

    def __repr__(self) -> str:
        return f"<RepairRequest(id={self.id}, asset_id={self.asset_id}, title='{self.title}', status={self.status.value})>"
