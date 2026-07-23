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
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class DepreciationRecord(Base):
    """Модель записи об амортизации"""
    __tablename__ = "depreciation_records"

    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    depreciation_amount = Column(Numeric(15, 2), nullable=False)
    accumulated_depreciation = Column(Numeric(15, 2), nullable=False)
    book_value_before = Column(Numeric(15, 2), nullable=False)
    book_value_after = Column(Numeric(15, 2), nullable=False)
    rate = Column(Numeric(5, 2), nullable=False)
    method = Column(String(50), nullable=False)

    created_at = Column(DateTime, nullable=False, default=datetime.now)
    posted_at = Column(DateTime, nullable=True)
    posted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)
    document_number = Column(String(100), nullable=True)

    __table_args__ = (
        Index("idx_depreciation_records_asset_id", "asset_id"),
        Index("idx_depreciation_records_period", "period_start", "period_end"),
        Index("idx_depreciation_records_created_at", "created_at"),
        Index("idx_depreciation_records_method", "method"),
    )

    asset = relationship("Asset", back_populates="depreciation_records")

    def __repr__(self) -> str:
        return f"<DepreciationRecord(id={self.id}, asset_id={self.asset_id}, period={self.period_start}→{self.period_end}, amount={self.depreciation_amount})>"
