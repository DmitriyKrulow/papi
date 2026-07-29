from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, date
from decimal import Decimal

from src.infrastructure.db.init_db import get_db
from src.infrastructure.db.models.asset_type_config import AssetTypeConfig, seed_asset_types
from src.infrastructure.db.models.maintenance_event import MaintenanceEvent

router = APIRouter(prefix="/asset-types", tags=["asset-types"])


@router.get("")
@router.get("/")
def list_asset_types(db: Session = Depends(get_db)):
    """Получить все типы активов"""
    types = db.query(AssetTypeConfig).filter(AssetTypeConfig.is_active == True).all()
    return [
        {
            "id": t.id,
            "code": t.code,
            "name": t.name,
            "icon": t.icon,
            "category": t.category,
            "description": t.description,
            "default_depreciation_years": t.default_depreciation_years,
            "default_maintenance_type": t.default_maintenance_type,
            "maintenance_interval_months": t.maintenance_interval_months,
            "is_active": t.is_active,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "updated_at": t.updated_at.isoformat() if t.updated_at else None,
        }
        for t in types
    ]


@router.post("/seed")
def seed_types(db: Session = Depends(get_db)):
    """Создать предустановленные типы активов"""
    seed_asset_types(db)
    return {"message": "Asset types seeded successfully"}


@router.get("/{type_code}")
def get_asset_type(type_code: str, db: Session = Depends(get_db)):
    """Получить конфигурацию типа актива"""
    asset_type = db.query(AssetTypeConfig).filter(AssetTypeConfig.code == type_code).first()
    if not asset_type:
        raise HTTPException(status_code=404, detail="Asset type not found")
    return {
        "id": asset_type.id,
        "code": asset_type.code,
        "name": asset_type.name,
        "icon": asset_type.icon,
        "category": asset_type.category,
        "description": asset_type.description,
        "default_depreciation_years": asset_type.default_depreciation_years,
        "default_maintenance_type": asset_type.default_maintenance_type,
        "maintenance_interval_months": asset_type.maintenance_interval_months,
        "is_active": asset_type.is_active,
        "created_at": asset_type.created_at.isoformat() if asset_type.created_at else None,
        "updated_at": asset_type.updated_at.isoformat() if asset_type.updated_at else None,
    }
