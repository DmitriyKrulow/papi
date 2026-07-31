# src/infrastructure/db/models/asset.py
from datetime import datetime, date
from typing import Optional

from sqlalchemy import (
    Boolean,
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

# Импортируем Base из __init__.py
from . import Base


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True)
    inventory_number = Column(String(50), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    model = Column(String(100), nullable=True)
    
    asset_type = Column(String(50), nullable=True)
    asset_type_config_id = Column(
        Integer, ForeignKey("asset_type_configs.id"), nullable=True
    )
    status = Column(String(50), nullable=False, default="active")
    
    purchase_price = Column(Numeric(15, 2), nullable=True)
    current_value = Column(Numeric(15, 2), nullable=True)
    quantity = Column(Integer, nullable=False, default=1)
    
    department_code = Column(String(50), nullable=True)
    responsible_person = Column(String(100), nullable=True)
    location_address = Column(String(255), nullable=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    manufacturer_code = Column(String(100), nullable=True)
    manufacturer_name = Column(String(255), nullable=True)
    
    purchase_date = Column(Date, nullable=True)
    commissioning_date = Column(Date, nullable=True)
    warranty_expiry = Column(Date, nullable=True)
    
    serial_number = Column(String(100), nullable=True)
    capacity = Column(Numeric(10, 2), nullable=True)
    power = Column(String(50), nullable=True)
    weight = Column(String(50), nullable=True)
    consumable_type = Column(String(100), nullable=True)
    crypto_wallet_address = Column(String(100), nullable=True)
    crypto_token_symbol = Column(String(20), nullable=True)
    depreciation_years = Column(Integer, nullable=True)
    next_maintenance_date = Column(Date, nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    is_active = Column(Boolean, nullable=False, default=True)
    
    __table_args__ = (
        Index("idx_assets_inventory_number", "inventory_number"),
        Index("idx_assets_status", "status"),
        Index("idx_assets_created_at", "created_at"),
        Index("idx_assets_asset_type", "asset_type"),
        Index("idx_assets_is_active", "is_active"),
    )

    repair_requests = relationship("RepairRequest", back_populates="asset")
    maintenance_records = relationship("MaintenanceRecord", back_populates="asset")
    maintenance_events = relationship("MaintenanceEvent", back_populates="asset")
    movement_records = relationship("MovementRecord", back_populates="asset")
    asset_photos = relationship("AssetPhoto", back_populates="asset")
    asset_type_config = relationship("AssetTypeConfig", back_populates="assets")
    assigned_employee = relationship("Employee")

    def __repr__(self) -> str:
        return f"<Asset(id={self.id}, name='{self.name}', status='{self.status}')>"