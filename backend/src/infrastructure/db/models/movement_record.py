from datetime import date, datetime
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
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class MovementRecord(Base):
    """Модель записи о перемещении актива"""
    __tablename__ = "movement_records"

    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    movement_date = Column(Date, nullable=False)

    from_department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    from_department_name = Column(String(255), nullable=True)
    from_location = Column(String(255), nullable=True)

    to_department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    to_department_name = Column(String(255), nullable=True)
    to_location = Column(String(255), nullable=True)

    from_responsible_id = Column(Integer, nullable=True)
    to_responsible_id = Column(Integer, nullable=True)

    reason = Column(Text, nullable=True)
    document_number = Column(String(100), nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.now)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    __table_args__ = (
        Index("idx_movement_records_asset_id", "asset_id"),
        Index("idx_movement_records_movement_date", "movement_date"),
        Index("idx_movement_records_from_department_id", "from_department_id"),
        Index("idx_movement_records_to_department_id", "to_department_id"),
        Index("idx_movement_records_created_at", "created_at"),
    )

    # Relationships
    asset = relationship("Asset", back_populates="movement_records")
    from_department = relationship(
        "Department", foreign_keys=[from_department_id], backref="outgoing_movements"
    )
    to_department = relationship(
        "Department", foreign_keys=[to_department_id], backref="incoming_movements"
    )

    def __repr__(self) -> str:
        return f"<MovementRecord(id={self.id}, asset_id={self.asset_id}, date={self.movement_date})>"
