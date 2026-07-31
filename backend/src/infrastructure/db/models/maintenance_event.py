from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from . import Base


class MaintenanceEvent(Base):
    """Типовые события обслуживания для активов"""
    __tablename__ = "maintenance_events"

    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    event_type = Column(String(100), nullable=False)
    event_date = Column(Date, nullable=False)
    description = Column(Text, nullable=True)
    cost = Column(Numeric(15, 2), nullable=True)
    performed_by = Column(String(255), nullable=True)
    next_event_date = Column(Date, nullable=True)
    result = Column(String(100), nullable=True)
    document_number = Column(String(100), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    __table_args__ = (
        Index("idx_maintenance_events_asset_id", "asset_id"),
        Index("idx_maintenance_events_event_type", "event_type"),
        Index("idx_maintenance_events_event_date", "event_date"),
    )

    asset = relationship("Asset", back_populates="maintenance_events")

    def __repr__(self) -> str:
        return f"<MaintenanceEvent(id={self.id}, asset_id={self.asset_id}, type='{self.event_type}', date={self.event_date})>"
