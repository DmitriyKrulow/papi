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
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class AssetType(Base):
    """?????? ???? ??????"""
    __tablename__ = "asset_types"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=True)

    category_id = Column(Integer, ForeignKey("asset_categories.id"), nullable=False)

    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )

    __table_args__ = (
        Index("idx_asset_types_category_id", "category_id"),
        Index("idx_asset_types_code", "code"),
        Index("idx_asset_types_created_at", "created_at"),
    )

    # Relationships
    category = relationship("AssetCategory", back_populates="asset_types")
    assets = relationship(
        "Asset", back_populates="asset_type_rel", foreign_keys="[Asset.asset_type]"
    )

    def __repr__(self) -> str:
        return f"<AssetType(id={self.id}, name='{self.name}', code='{self.code}')>"


