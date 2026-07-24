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
    Numeric,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class AssetCategory(Base):
    """?????? ????????? ???????"""
    __tablename__ = "asset_categories"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False, unique=True, index=True)

    parent_id = Column(Integer, ForeignKey("asset_categories.id"), nullable=True)
    description = Column(Text, nullable=True)

    default_depreciation_rate = Column(Numeric(5, 2), nullable=True)
    useful_life_years = Column(Integer, nullable=True)

    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )

    __table_args__ = (
        Index("idx_asset_categories_code", "code"),
        Index("idx_asset_categories_parent_id", "parent_id"),
        Index("idx_asset_categories_created_at", "created_at"),
    )

    # Self-referential relationship for hierarchy
    parent = relationship(
        "AssetCategory", remote_side=[id], backref="subcategories"
    )

    # Relationships
    asset_types = relationship(
        "AssetType", back_populates="category", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<AssetCategory(id={self.id}, name='{self.name}', code='{self.code}')>"


