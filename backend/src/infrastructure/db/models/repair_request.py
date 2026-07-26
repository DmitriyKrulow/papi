# backend/src/infrastructure/db/models/repair_request.py
from datetime import datetime, date
from typing import Optional

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Numeric,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
import enum
from . import Base


class RepairPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class RepairStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class RepairRequest(Base):
    __tablename__ = "repair_requests"

    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)

    priority = Column(SQLEnum(RepairPriority), nullable=False, default=RepairPriority.MEDIUM)
    status = Column(SQLEnum(RepairStatus), nullable=False, default=RepairStatus.DRAFT)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
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

    maintenance_record_id = Column(Integer, ForeignKey("maintenance_records.id"), nullable=True)

    template_data = Column(Text, nullable=True)

    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    asset = relationship("Asset", back_populates="repair_requests")
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_repairs")
    assignee = relationship("User", foreign_keys=[assigned_to], back_populates="assigned_repairs")
    asset_photos = relationship("AssetPhoto", back_populates="repair_request")

    __table_args__ = (
        Index("idx_repair_requests_asset_id", "asset_id"),
        Index("idx_repair_requests_status", "status"),
        Index("idx_repair_requests_priority", "priority"),
        Index("idx_repair_requests_created_at", "created_at"),
        Index("idx_repair_requests_assigned_to", "assigned_to"),
    )

    def __repr__(self) -> str:
        return f"<RepairRequest(id={self.id}, title='{self.title}', status='{self.status}')>"