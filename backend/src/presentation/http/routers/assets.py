# backend/src/presentation/http/routers/assets.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text
from typing import Optional, Any
from datetime import datetime, date
from decimal import Decimal

from src.infrastructure.db.init_db import get_db
from src.infrastructure.db.models.asset import Asset
from src.infrastructure.db.models.asset_type_config import AssetTypeConfig
from src.infrastructure.db.models.department import Department
from src.infrastructure.db.models.employee import Employee

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


def asset_to_dict(asset, db: Optional[Session] = None):
    """Преобразует объект Asset в словарь"""
    asset_type_value = getattr(asset, 'asset_type', None)
    if not asset_type_value and hasattr(asset, 'asset_type_config') and asset.asset_type_config:
        asset_type_value = asset.asset_type_config.code
    
    department_name = None
    employee_name = None
    if db and getattr(asset, 'department_code', None):
        dept = db.query(Department).filter(
            (Department.code == asset.department_code) | (Department.name == asset.department_code),
            Department.is_active == True
        ).first()
        if dept:
            department_name = f"{dept.name} ({dept.code})"
            employees = db.query(Employee).filter(
                Employee.department_id == dept.id,
                Employee.is_active == True
            ).order_by(Employee.last_name, Employee.first_name).all()
            if employees:
                emp_names = [f"{e.last_name} {e.first_name}" for e in employees]
                employee_name = ", ".join(emp_names[:5])
                if len(employees) > 5:
                    employee_name += f" (+{len(employees) - 5})"
    
    return {
        "id": getattr(asset, 'id', None),
        "inventory_number": safe_str(getattr(asset, 'inventory_number', None)),
        "name": safe_str(getattr(asset, 'name', None)),
        "description": safe_str(getattr(asset, 'description', None)),
        "model": safe_str(getattr(asset, 'model', None)),
        "asset_type": safe_str(asset_type_value),
        "status": safe_str(getattr(asset, 'status', None)),
        "purchase_price": safe_decimal_to_float(getattr(asset, 'purchase_price', None)),
        "current_value": safe_decimal_to_float(getattr(asset, 'current_value', None)),
        "department_code": safe_str(getattr(asset, 'department_code', None)),
        "department_name": safe_str(department_name),
        "responsible_person": safe_str(getattr(asset, 'responsible_person', None)),
        "employee_name": safe_str(employee_name),
        "location_address": safe_str(getattr(asset, 'location_address', None)),
        "manufacturer_code": safe_str(getattr(asset, 'manufacturer_code', None)),
        "manufacturer_name": safe_str(getattr(asset, 'manufacturer_name', None)),
        "purchase_date": safe_isoformat(getattr(asset, 'purchase_date', None)),
        "commissioning_date": safe_isoformat(getattr(asset, 'commissioning_date', None)),
        "warranty_expiry": safe_isoformat(getattr(asset, 'warranty_expiry', None)),
        "serial_number": safe_str(getattr(asset, 'serial_number', None)),
        "capacity": safe_decimal_to_float(getattr(asset, 'capacity', None)),
        "power": safe_str(getattr(asset, 'power', None)),
        "weight": safe_str(getattr(asset, 'weight', None)),
        "consumable_type": safe_str(getattr(asset, 'consumable_type', None)),
        "crypto_wallet_address": safe_str(getattr(asset, 'crypto_wallet_address', None)),
        "crypto_token_symbol": safe_str(getattr(asset, 'crypto_token_symbol', None)),
        "depreciation_years": getattr(asset, 'depreciation_years', None),
        "next_maintenance_date": safe_isoformat(getattr(asset, 'next_maintenance_date', None)),
        "created_at": safe_isoformat(getattr(asset, 'created_at', None)),
        "updated_at": safe_isoformat(getattr(asset, 'updated_at', None)),
    }


@router.get("/")
async def list_assets(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=10000),
    status: Optional[str] = None,
    search: Optional[str] = None,
    location: Optional[str] = None,
    department: Optional[str] = None,
    responsible: Optional[str] = None,
    employee: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Получить список активов с пагинацией и фильтрацией.
    """
    try:
        query = db.query(Asset).options(joinedload(Asset.asset_type_config))
        
        if status:
            query = query.filter(Asset.status == status)
        
        if search:
            query = query.filter(
                (Asset.name.contains(search)) | 
                (Asset.inventory_number.contains(search)) |
                (Asset.responsible_person.contains(search))
            )
        
        if location:
            query = query.filter(Asset.location_address.contains(location))
        
        if department:
            dept_match = db.query(Department.id).filter(
                (Department.code.contains(department)) | 
                (Department.name.contains(department)),
                Department.is_active == True
            ).first()
            if dept_match:
                query = query.filter(Asset.department_code == Department.code if False else Asset.department_code.contains(department))
            else:
                query = query.filter(Asset.department_code.contains(department))
        
        if responsible:
            query = query.filter(Asset.responsible_person.contains(responsible))
        
        if employee:
            emp_match = db.query(Employee).filter(
                (Employee.first_name.contains(employee)) |
                (Employee.last_name.contains(employee))
            ).first()
            if emp_match:
                query = query.filter(
                    (Asset.responsible_person.contains(emp_match.last_name)) |
                    (Asset.responsible_person.contains(emp_match.first_name))
                )
            else:
                query = query.filter(text("0=1"))
        
        total = query.count()
        assets = query.offset(skip).limit(limit).all()
        
        return {
            "items": [asset_to_dict(asset, db) for asset in assets],
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
        asset = db.query(Asset).options(joinedload(Asset.asset_type_config)).filter(Asset.id == asset_id).first()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        return asset_to_dict(asset, db)
        
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
        
        # Преобразуем даты
        purchase_date = None
        if asset_data.get("purchase_date"):
            try:
                purchase_date = datetime.strptime(asset_data["purchase_date"], "%Y-%m-%d").date()
            except:
                purchase_date = datetime.fromisoformat(asset_data["purchase_date"]).date()
        
        commissioning_date = None
        if asset_data.get("commissioning_date"):
            try:
                commissioning_date = datetime.strptime(asset_data["commissioning_date"], "%Y-%m-%d").date()
            except:
                commissioning_date = datetime.fromisoformat(asset_data["commissioning_date"]).date()
        
        warranty_expiry = None
        if asset_data.get("warranty_expiry"):
            try:
                warranty_expiry = datetime.strptime(asset_data["warranty_expiry"], "%Y-%m-%d").date()
            except:
                warranty_expiry = datetime.fromisoformat(asset_data["warranty_expiry"]).date()
        
        next_maintenance_date = None
        if asset_data.get("next_maintenance_date"):
            try:
                next_maintenance_date = datetime.strptime(asset_data["next_maintenance_date"], "%Y-%m-%d").date()
            except:
                next_maintenance_date = datetime.fromisoformat(asset_data["next_maintenance_date"]).date()

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
            location_address=asset_data.get("location_address"),
            manufacturer_code=asset_data.get("manufacturer_code"),
            manufacturer_name=asset_data.get("manufacturer_name"),
            purchase_date=purchase_date,
            commissioning_date=commissioning_date,
            warranty_expiry=warranty_expiry,
            serial_number=asset_data.get("serial_number"),
            capacity=Decimal(str(asset_data.get("capacity", 0))) if asset_data.get("capacity") else None,
            power=asset_data.get("power"),
            weight=asset_data.get("weight"),
            consumable_type=asset_data.get("consumable_type"),
            crypto_wallet_address=asset_data.get("crypto_wallet_address"),
            crypto_token_symbol=asset_data.get("crypto_token_symbol"),
            depreciation_years=asset_data.get("depreciation_years"),
            next_maintenance_date=next_maintenance_date,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        db.add(asset)
        db.commit()
        db.refresh(asset)
        
        return asset_to_dict(asset)
        
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
        
        # Преобразуем даты
        if "purchase_date" in asset_data and asset_data["purchase_date"]:
            try:
                asset.purchase_date = datetime.strptime(asset_data["purchase_date"], "%Y-%m-%d").date()
            except:
                asset.purchase_date = datetime.fromisoformat(asset_data["purchase_date"]).date()
        elif "purchase_date" in asset_data:
            asset.purchase_date = None
            
        if "commissioning_date" in asset_data and asset_data["commissioning_date"]:
            try:
                asset.commissioning_date = datetime.strptime(asset_data["commissioning_date"], "%Y-%m-%d").date()
            except:
                asset.commissioning_date = datetime.fromisoformat(asset_data["commissioning_date"]).date()
        elif "commissioning_date" in asset_data:
            asset.commissioning_date = None
            
        if "warranty_expiry" in asset_data and asset_data["warranty_expiry"]:
            try:
                asset.warranty_expiry = datetime.strptime(asset_data["warranty_expiry"], "%Y-%m-%d").date()
            except:
                asset.warranty_expiry = datetime.fromisoformat(asset_data["warranty_expiry"]).date()
        elif "warranty_expiry" in asset_data:
            asset.warranty_expiry = None
            
        if "next_maintenance_date" in asset_data and asset_data["next_maintenance_date"]:
            try:
                asset.next_maintenance_date = datetime.strptime(asset_data["next_maintenance_date"], "%Y-%m-%d").date()
            except:
                asset.next_maintenance_date = datetime.fromisoformat(asset_data["next_maintenance_date"]).date()
        elif "next_maintenance_date" in asset_data:
            asset.next_maintenance_date = None

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
            asset.purchase_price = Decimal(str(asset_data["purchase_price"]))
        if "current_value" in asset_data:
            asset.current_value = Decimal(str(asset_data["current_value"]))
        if "department_code" in asset_data:
            asset.department_code = asset_data["department_code"]
        if "responsible_person" in asset_data:
            asset.responsible_person = asset_data["responsible_person"]
        if "location_address" in asset_data:
            asset.location_address = asset_data["location_address"]
        if "manufacturer_code" in asset_data:
            asset.manufacturer_code = asset_data["manufacturer_code"]
        if "manufacturer_name" in asset_data:
            asset.manufacturer_name = asset_data["manufacturer_name"]
        if "serial_number" in asset_data:
            asset.serial_number = asset_data["serial_number"]
        if "capacity" in asset_data and asset_data["capacity"] is not None:
            asset.capacity = Decimal(str(asset_data["capacity"]))
        if "power" in asset_data:
            asset.power = asset_data["power"]
        if "weight" in asset_data:
            asset.weight = asset_data["weight"]
        if "consumable_type" in asset_data:
            asset.consumable_type = asset_data["consumable_type"]
        if "crypto_wallet_address" in asset_data:
            asset.crypto_wallet_address = asset_data["crypto_wallet_address"]
        if "crypto_token_symbol" in asset_data:
            asset.crypto_token_symbol = asset_data["crypto_token_symbol"]
        if "depreciation_years" in asset_data:
            asset.depreciation_years = asset_data["depreciation_years"]
        
        asset.updated_at = datetime.now()
        
        db.commit()
        db.refresh(asset)
        
        return asset_to_dict(asset)
        
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