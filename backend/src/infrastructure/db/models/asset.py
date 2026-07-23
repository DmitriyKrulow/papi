from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
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

from backend.src.core.value_objects import AssetStatus

Base = declarative_base()


class Asset(Base):
    """Модель актива/основного средства"""
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True)
    inventory_number = Column(String(50), nullable=False, unique=True, index=True)
    batch_id = Column(String(50), nullable=True)
    serial_number = Column(String(50), nullable=True)
    year_period = Column(String(10), nullable=True)
    asset_type = Column(String(50), nullable=True)

    name = Column(String(255), nullable=False, default="")
    description = Column(Text, nullable=True)
    model = Column(String(255), nullable=True)

    manufacturer_code = Column(String(100), nullable=True)
    manufacturer_name = Column(String(255), nullable=True)
    country_of_origin = Column(String(100), nullable=True)

    accounting_code = Column(String(100), nullable=True)
    department_code = Column(String(100), nullable=True)
    responsible_person = Column(String(255), nullable=True)

    purchase_price = Column(Numeric(15, 2), nullable=True)
    current_value = Column(Numeric(15, 2), nullable=True)
    residual_value = Column(Numeric(15, 2), nullable=True)
    depreciation_rate = Column(Numeric(5, 2), nullable=True)

    status = Column(
        Enum(AssetStatus, name="asset_status_enum"),
        nullable=False,
        default=AssetStatus.ACTIVE,
    )

    location = Column(String(255), nullable=True)
    location_address = Column(String(500), nullable=True)
    responsible_phone = Column(String(50), nullable=True)

    purchase_date = Column(Date, nullable=True)
    commissioning_date = Column(Date, nullable=True)
    warranty_expiry = Column(Date, nullable=True)
    last_maintenance_date = Column(Date, nullable=True)
    next_maintenance_date = Column(Date, nullable=True)
    decommissioning_date = Column(Date, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)

    tags = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    __table_args__ = (
        Index("idx_assets_inventory_number", "inventory_number"),
        Index("idx_assets_status", "status"),
        Index("idx_assets_department_code", "department_code"),
        Index("idx_assets_created_at", "created_at"),
        CheckConstraint("purchase_price >= 0", name="chk_assets_purchase_price_non_negative"),
        CheckConstraint("current_value >= 0", name="chk_assets_current_value_non_negative"),
    )

    # Relationships
    repair_requests = relationship(
        "RepairRequest", back_populates="asset", cascade="all, delete-orphan"
    )
    documents = relationship(
        "Document", back_populates="asset", foreign_keys="[Document.asset_id]", cascade="all, delete-orphan"
    )
    movement_records = relationship(
        "MovementRecord", back_populates="asset", cascade="all, delete-orphan"
    )
    maintenance_records = relationship(
        "MaintenanceRecord", back_populates="asset", cascade="all, delete-orphan"
    )
    depreciation_records = relationship(
        "DepreciationRecord", back_populates="asset", cascade="all, delete-orphan"
    )
    asset_photos = relationship(
        "AssetPhoto", back_populates="asset", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Asset(id={self.id}, inventory_number='{self.inventory_number}', name='{self.name}')>"
