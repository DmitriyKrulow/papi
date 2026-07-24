# src/infrastructure/db/models/asset.py
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    Numeric,
)
from sqlalchemy.orm import declarative_base

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
    status = Column(String(50), nullable=False, default="active")
    
    purchase_price = Column(Numeric(15, 2), nullable=True)
    current_value = Column(Numeric(15, 2), nullable=True)
    
    department_code = Column(String(50), nullable=True)
    responsible_person = Column(String(100), nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    
    __table_args__ = (
        Index("idx_assets_inventory_number", "inventory_number"),
        Index("idx_assets_status", "status"),
        Index("idx_assets_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Asset(id={self.id}, name='{self.name}', status='{self.status}')>"