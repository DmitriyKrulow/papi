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
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class MaintenanceRecord(Base):
    """Модель записи о техническом обслуживании"""
    __tablename__ = "maintenance_records"

    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    maintenance_date = Column(Date, nullable=False)
    maintenance_type = Column(String(100), nullable=False)

    description = Column(Text, nullable=True)
    cost = Column(Numeric(15, 2), nullable=True)

    performed_by = Column(String(255), nullable=True)
    contractor = Column(String(255), nullable=True)

    result = Column(String(100), nullable=True)
    next_maintenance_date = Column(Date, nullable=True)

    document_number = Column(String(100), nullable=True)
    document_date = Column(Date, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.now)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    __table_args__ = (
        Index("idx_maintenance_records_asset_id", "asset_id"),
        Index("idx_maintenance_records_maintenance_date", "maintenance_date"),
        Index("idx_maintenance_records_created_at", "created_at"),
    )

    # Relationships
    asset = relationship("Asset", back_populates="maintenance_records")

    def __repr__(self) -> str:
        return f"<MaintenanceRecord(id={self.id}, asset_id={self.asset_id}, date={self.maintenance_date}, type='{self.maintenance_type}')>"
