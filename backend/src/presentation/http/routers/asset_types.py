from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal

from src.infrastructure.db.init_db import get_db
from src.infrastructure.db.models.asset_type_config import (
    AssetTypeConfig, 
    seed_asset_types,
    DEFAULT_PHOTO_CATEGORIES,
)
from src.infrastructure.db.models.maintenance_event import MaintenanceEvent

router = APIRouter(prefix="/asset-types", tags=["asset-types"])


# Описания категорий фотографий
PHOTO_CATEGORY_LABELS = {
    "general_view": "Общий вид",
    "placement": "Место размещения",
    "inventory_number": "Инвентарный номер",
    "current_location": "Текущее место расположения",
    "condition": "Состояние",
    "malfunction": "Неисправность",
    "general_condition": "Общее состояние",
}


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
            "photo_categories": t.get_photo_categories(),
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
        "photo_categories": asset_type.get_photo_categories(),
    }


@router.get("/{type_code}/photo-categories")
def get_asset_type_photo_categories(type_code: str, db: Session = Depends(get_db)):
    """
    Получает доступные категории фотографий для типа актива.
    Возвращает:
    - configured: список настроенных категорий для этого типа
    - available: все доступные категории с описаниями
    """
    asset_type = db.query(AssetTypeConfig).filter(AssetTypeConfig.code == type_code).first()
    if not asset_type:
        raise HTTPException(status_code=404, detail="Asset type not found")
    
    configured = asset_type.get_photo_categories()
    available = [
        {"key": cat, "label": PHOTO_CATEGORY_LABELS.get(cat, cat)}
        for cat in DEFAULT_PHOTO_CATEGORIES
    ]
    
    return {
        "type_code": type_code,
        "type_name": asset_type.name,
        "configured": configured,
        "available": available,
    }


@router.put("/{type_code}/photo-categories")
def update_asset_type_photo_categories(
    type_code: str,
    categories: List[str],
    db: Session = Depends(get_db),
):
    """
    Обновляет список разрешённых категорий фотографий для типа актива.
    
    body: {"categories": ["general_view", "inventory_number", ...]}
    """
    asset_type = db.query(AssetTypeConfig).filter(AssetTypeConfig.code == type_code).first()
    if not asset_type:
        raise HTTPException(status_code=404, detail="Asset type not found")
    
    # Валидируем категории
    valid_categories = set(DEFAULT_PHOTO_CATEGORIES)
    invalid = [c for c in categories if c not in valid_categories]
    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"Недопустимые категории: {', '.join(invalid)}. Доступные: {', '.join(DEFAULT_PHOTO_CATEGORIES)}"
        )
    
    asset_type.set_photo_categories(categories)
    db.commit()
    db.refresh(asset_type)
    
    return {
        "message": "Photo categories updated",
        "type_code": type_code,
        "categories": asset_type.get_photo_categories(),
    }


@router.post("/{type_code}/photo-categories/{category}")
def add_asset_type_photo_category(
    type_code: str,
    category: str,
    db: Session = Depends(get_db),
):
    """Добавляет одну категорию фотографий для типа актива."""
    asset_type = db.query(AssetTypeConfig).filter(AssetTypeConfig.code == type_code).first()
    if not asset_type:
        raise HTTPException(status_code=404, detail="Asset type not found")
    
    if category not in DEFAULT_PHOTO_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Недопустимая категория: {category}"
        )
    
    asset_type.add_photo_category(category)
    db.commit()
    db.refresh(asset_type)
    
    return {
        "message": f"Category '{category}' added",
        "categories": asset_type.get_photo_categories(),
    }


@router.delete("/{type_code}/photo-categories/{category}")
def remove_asset_type_photo_category(
    type_code: str,
    category: str,
    db: Session = Depends(get_db),
):
    """Удаляет одну категорию фотографий для типа актива."""
    asset_type = db.query(AssetTypeConfig).filter(AssetTypeConfig.code == type_code).first()
    if not asset_type:
        raise HTTPException(status_code=404, detail="Asset type not found")
    
    asset_type.remove_photo_category(category)
    db.commit()
    db.refresh(asset_type)
    
    return {
        "message": f"Category '{category}' removed",
        "categories": asset_type.get_photo_categories(),
    }


@router.get("/photo-categories/available")
def get_available_photo_categories():
    """Возвращает все доступные категории фотографий с описаниями."""
    return {
        "categories": [
            {"key": cat, "label": PHOTO_CATEGORY_LABELS.get(cat, cat)}
            for cat in DEFAULT_PHOTO_CATEGORIES
        ]
    }
