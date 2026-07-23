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


class AssetPhoto(Base):
    """Модель фотографии актива"""
    __tablename__ = "asset_photos"

    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    stage = Column(String(50), nullable=False, default="other")

    description = Column(Text, nullable=True)
    taken_at = Column(DateTime, nullable=True)
    taken_by = Column(Integer, nullable=True)
    uploaded_at = Column(DateTime, nullable=False, default=datetime.now)

    inventory_check_id = Column(Integer, ForeignKey("inventory_checks.id"), nullable=True)
    repair_request_id = Column(Integer, ForeignKey("repair_requests.id"), nullable=True)

    is_before = Column(Boolean, nullable=False, default=False)
    is_after = Column(Boolean, nullable=False, default=False)
    sort_order = Column(Integer, nullable=False, default=0)

    __table_args__ = (
        Index("idx_asset_photos_asset_id", "asset_id"),
        Index("idx_asset_photos_document_id", "document_id"),
        Index("idx_asset_photos_uploaded_by", "uploaded_by"),
        Index("idx_asset_photos_uploaded_at", "uploaded_at"),
    )

    # Relationships
    asset = relationship("Asset", back_populates="asset_photos")
    document = relationship("Document", backref="asset_photos")
    uploaded_by_user = relationship("User", backref="asset_photos")
    inventory_check = relationship("InventoryCheck", backref="asset_photos")
    repair_request = relationship("RepairRequest", backref="asset_photos")

    def __repr__(self) -> str:
        return f"<AssetPhoto(id={self.id}, asset_id={self.asset_id}, stage='{self.stage}')>"
