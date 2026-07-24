# backend/src/presentation/http/routers/assets.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, Any
from datetime import datetime
from decimal import Decimal

from src.infrastructure.db.init_db import get_db
from src.infrastructure.db.models.asset import Asset

router = APIRouter(prefix="/assets", tags=["assets"])


def safe_decimal_to_float(value: Optional[Any], default: float = 0.0) -> float:
    """Безопасно преобразует Decimal в float"""
    if value is None:
        return default
    try:
        if isinstance(value, (int, float, Decimal)):
            return float(value)
        return default
    except (TypeError, ValueError):
        return default


def safe_str(value: Optional[Any], default: str = "") -> str:
    """Безопасно преобразует в строку"""
    if value is None:
        return default
    try:
        return str(value)
    except (TypeError, ValueError):
        return default


def safe_isoformat(value: Optional[Any]) -> Optional[str]:
    """Безопасно преобразует дату в ISO формат"""
    if value is None:
        return None
    try:
        if hasattr(value, 'isoformat') and callable(getattr(value, 'isoformat')):
            return value.isoformat()
        return str(value)
    except (AttributeError, ValueError):
        return None


@router.get("/")
async def list_assets(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Получить список активов с пагинацией и фильтрацией.
    """
    try:
        query = db.query(Asset)
        
        # Фильтр по статусу
        if status:
            query = query.filter(Asset.status == status)
        
        # Поиск по названию или инвентарному номеру
        if search:
            query = query.filter(
                (Asset.name.contains(search)) | 
                (Asset.inventory_number.contains(search))
            )
        
        # Пагинация
        total = query.count()
        assets = query.offset(skip).limit(limit).all()
        
        # Преобразуем в словари
        result = []
        for asset in assets:
            result.append({
                "id": getattr(asset, 'id', None),
                "inventory_number": safe_str(getattr(asset, 'inventory_number', None)),
                "name": safe_str(getattr(asset, 'name', None)),
                "description": safe_str(getattr(asset, 'description', None)),
                "model": safe_str(getattr(asset, 'model', None)),
                "asset_type": safe_str(getattr(asset, 'asset_type', None)),
                "status": safe_str(getattr(asset, 'status', None)),
                "purchase_price": safe_decimal_to_float(getattr(asset, 'purchase_price', None)),
                "current_value": safe_decimal_to_float(getattr(asset, 'current_value', None)),
                "department_code": safe_str(getattr(asset, 'department_code', None)),
                "responsible_person": safe_str(getattr(asset, 'responsible_person', None)),
                "created_at": safe_isoformat(getattr(asset, 'created_at', None)),
                "updated_at": safe_isoformat(getattr(asset, 'updated_at', None)),
            })
        
        return {
            "items": result,
            "total": total,
            "skip": skip,
            "limit": limit,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{asset_id}")
async def get_asset(
    asset_id: int,
    db: Session = Depends(get_db),
):
    """
    Получить актив по ID.
    """
    try:
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        return {
            "id": getattr(asset, 'id', None),
            "inventory_number": safe_str(getattr(asset, 'inventory_number', None)),
            "name": safe_str(getattr(asset, 'name', None)),
            "description": safe_str(getattr(asset, 'description', None)),
            "model": safe_str(getattr(asset, 'model', None)),
            "asset_type": safe_str(getattr(asset, 'asset_type', None)),
            "status": safe_str(getattr(asset, 'status', None)),
            "purchase_price": safe_decimal_to_float(getattr(asset, 'purchase_price', None)),
            "current_value": safe_decimal_to_float(getattr(asset, 'current_value', None)),
            "department_code": safe_str(getattr(asset, 'department_code', None)),
            "responsible_person": safe_str(getattr(asset, 'responsible_person', None)),
            "created_at": safe_isoformat(getattr(asset, 'created_at', None)),
            "updated_at": safe_isoformat(getattr(asset, 'updated_at', None)),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def create_asset(
    asset_data: dict,
    db: Session = Depends(get_db),
):
    """
    Создать новый актив.
    """
    try:
        # Проверяем, что инвентарный номер уникален
        existing = db.query(Asset).filter(
            Asset.inventory_number == asset_data.get("inventory_number")
        ).first()
        if existing:
            raise HTTPException(
                status_code=400, 
                detail=f"Asset with inventory number '{asset_data.get('inventory_number')}' already exists"
            )
        
        # Создаем актив
        asset = Asset(
            inventory_number=asset_data.get("inventory_number"),
            name=asset_data.get("name"),
            description=asset_data.get("description"),
            model=asset_data.get("model"),
            asset_type=asset_data.get("asset_type"),
            status=asset_data.get("status", "active"),
            purchase_price=Decimal(str(asset_data.get("purchase_price", 0))),
            current_value=Decimal(str(asset_data.get("current_value", 0))),
            department_code=asset_data.get("department_code"),
            responsible_person=asset_data.get("responsible_person"),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        db.add(asset)
        db.commit()
        db.refresh(asset)
        
        return {
            "id": getattr(asset, 'id', None),
            "inventory_number": safe_str(getattr(asset, 'inventory_number', None)),
            "name": safe_str(getattr(asset, 'name', None)),
            "description": safe_str(getattr(asset, 'description', None)),
            "model": safe_str(getattr(asset, 'model', None)),
            "asset_type": safe_str(getattr(asset, 'asset_type', None)),
            "status": safe_str(getattr(asset, 'status', None)),
            "purchase_price": safe_decimal_to_float(getattr(asset, 'purchase_price', None)),
            "current_value": safe_decimal_to_float(getattr(asset, 'current_value', None)),
            "department_code": safe_str(getattr(asset, 'department_code', None)),
            "responsible_person": safe_str(getattr(asset, 'responsible_person', None)),
            "created_at": safe_isoformat(getattr(asset, 'created_at', None)),
            "updated_at": safe_isoformat(getattr(asset, 'updated_at', None)),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{asset_id}")
async def update_asset(
    asset_id: int,
    asset_data: dict,
    db: Session = Depends(get_db),
):
    """
    Обновить актив.
    """
    try:
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        # Обновляем только переданные поля
        if "name" in asset_data:
            asset.name = asset_data["name"]
        if "description" in asset_data:
            asset.description = asset_data["description"]
        if "model" in asset_data:
            asset.model = asset_data["model"]
        if "asset_type" in asset_data:
            asset.asset_type = asset_data["asset_type"]
        if "status" in asset_data:
            asset.status = asset_data["status"]
        if "purchase_price" in asset_data:
            asset.purchase_price = Decimal(str(asset_data["purchase_price"]))  # type: ignore
        if "current_value" in asset_data:
            asset.current_value = Decimal(str(asset_data["current_value"]))  # type: ignore
        if "department_code" in asset_data:
            asset.department_code = asset_data["department_code"]
        if "responsible_person" in asset_data:
            asset.responsible_person = asset_data["responsible_person"]
        
        asset.updated_at = datetime.now()  # type: ignore
        
        db.commit()
        db.refresh(asset)
        
        return {
            "id": getattr(asset, 'id', None),
            "inventory_number": safe_str(getattr(asset, 'inventory_number', None)),
            "name": safe_str(getattr(asset, 'name', None)),
            "description": safe_str(getattr(asset, 'description', None)),
            "model": safe_str(getattr(asset, 'model', None)),
            "asset_type": safe_str(getattr(asset, 'asset_type', None)),
            "status": safe_str(getattr(asset, 'status', None)),
            "purchase_price": safe_decimal_to_float(getattr(asset, 'purchase_price', None)),
            "current_value": safe_decimal_to_float(getattr(asset, 'current_value', None)),
            "department_code": safe_str(getattr(asset, 'department_code', None)),
            "responsible_person": safe_str(getattr(asset, 'responsible_person', None)),
            "created_at": safe_isoformat(getattr(asset, 'created_at', None)),
            "updated_at": safe_isoformat(getattr(asset, 'updated_at', None)),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{asset_id}")
async def delete_asset(
    asset_id: int,
    db: Session = Depends(get_db),
):
    """
    Удалить актив.
    """
    try:
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        db.delete(asset)
        db.commit()
        
        return {"message": "Asset deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))