# backend/src/presentation/http/routers/asset_split.py
"""API для разделения активов с quantity > 1 на отдельные объекты

Позволяет:
- Разделить актив с quantity > 1 на отдельные объекты (6464646-1, 6464646-2, ...)
- Каждый новый объект получает уникальный инвентарный номер
- Можно назначить помещение, сотрудника, RFID метку
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime

from src.infrastructure.db.init_db import get_db
from src.infrastructure.db.models.asset import Asset
from src.infrastructure.db.models.asset_unit import AssetUnit
from src.infrastructure.db.models.employee import Employee
from src.infrastructure.db.models.department import Room
from src.infrastructure.db.models.user import User
from src.presentation.http.dependencies.auth import get_current_user, get_current_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/assets/split", tags=["asset-split"])


@router.get("/")
async def list_split_candidates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Список активов, которые можно разделить (quantity > 1)"""
    assets = db.query(Asset).filter(
        Asset.is_active == True,
        Asset.quantity > 1,
    ).all()
    
    return {
        "total": len(assets),
        "assets": [
            {
                "id": a.id,
                "inventory_number": a.inventory_number or "",
                "name": a.name or "",
                "quantity": a.quantity or 1,
                "asset_type": a.asset_type or "",
                "model": a.model or "",
                "serial_number": a.serial_number or "",
                "can_split": True,  # Можно разделить
            }
            for a in assets
        ],
    }


@router.post("/")
async def split_asset(
    asset_id: int = Query(..., description="ID актива для разделения"),
    room_id: Optional[int] = Query(None, description="ID помещения для хранения"),
    employee_id: Optional[int] = Query(None, description="ID сотрудника"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Разделить актив на отдельные объекты.
    
    Пример:
    - Было: Штампы (инв. 6464646, quantity=3)
    - Станет:
      * Штампы (инв. 6464646-1, room_id=X, employee_id=Y)
      * Штампы (инв. 6464646-2, room_id=X, employee_id=Y)
      * Штампы (инв. 6464646-3, room_id=X, employee_id=Y)
    """
    # Получаем исходный актив
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Актив не найден")
    
    if asset.quantity <= 1:
        raise HTTPException(status_code=400, detail="Актив имеет quantity=1, разделение невозможно")
    
    quantity = asset.quantity or 1
    base_inventory = asset.inventory_number or ""
    
    # Получаем помещение и сотрудника если указаны
    room = None
    employee = None
    if room_id:
        room = db.query(Room).filter(Room.id == room_id).first()
        if not room:
            raise HTTPException(status_code=404, detail="Помещение не найдено")
    
    if employee_id:
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Сотрудник не найден")
    
    # Деактивируем исходный актив
    asset.is_active = False
    asset.quantity = 0
    
    # Создаём отдельные объекты
    new_assets = []
    for i in range(1, quantity + 1):
        new_inventory = f"{base_inventory}-{i}"
        
        # Проверяем уникальность
        existing = db.query(Asset).filter(
            Asset.inventory_number == new_inventory,
            Asset.is_active == True,
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Инвентарный номер {new_inventory} уже существует"
            )
        
        new_asset = Asset(
            inventory_number=new_inventory,
            name=asset.name,
            description=asset.description,
            model=asset.model,
            asset_type=asset.asset_type,
            status=asset.status,
            purchase_price=asset.purchase_price / quantity if asset.purchase_price else None,
            current_value=asset.current_value / quantity if asset.current_value else None,
            quantity=1,
            department_code=asset.department_code,
            employee_id=employee.id if employee else None,
            responsible_person=employee.last_name + " " + employee.first_name if employee else None,
            room_id=room.id if room else None,
            location_address=asset.location_address,
            manufacturer_code=asset.manufacturer_code,
            manufacturer_name=asset.manufacturer_name,
            purchase_date=asset.purchase_date,
            commissioning_date=asset.commissioning_date,
            warranty_expiry=asset.warranty_expiry,
            serial_number=f"{asset.serial_number}-{i}" if asset.serial_number else None,
            capacity=asset.capacity,
            power=asset.power,
            weight=asset.weight,
            consumable_type=asset.consumable_type,
            crypto_wallet_address=asset.crypto_wallet_address,
            crypto_token_symbol=asset.crypto_token_symbol,
            depreciation_years=asset.depreciation_years,
            next_maintenance_date=asset.next_maintenance_date,
            rfid_tag=None,
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        db.add(new_asset)
        new_assets.append(new_asset)
    
    db.commit()
    
    # Создаём AssetUnit для каждого нового актива
    for i, new_asset in enumerate(new_assets, 1):
        unit = AssetUnit(
            asset_id=new_asset.id,
            unit_number=i,
            unique_identifier=new_asset.inventory_number,
            current_employee_id=new_asset.employee_id,
            current_department_code=new_asset.department_code,
            status="active",
            is_active=True,
            created_at=datetime.now(),
        )
        db.add(unit)
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Актив разделён на {quantity} объектов",
        "original_asset_id": asset.id,
        "original_inventory": base_inventory,
        "new_assets": [
            {
                "id": a.id,
                "inventory_number": a.inventory_number,
                "name": a.name,
                "quantity": a.quantity,
                "room_name": room.name if room else None,
                "employee_name": f"{employee.last_name} {employee.first_name}" if employee else None,
            }
            for a in new_assets
        ],
    }


@router.get("/{asset_id}/preview")
async def preview_split(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Предпросмотр разделения актива"""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Актив не найден")
    
    if asset.quantity <= 1:
        raise HTTPException(status_code=400, detail="Актив имеет quantity=1, разделение невозможно")
    
    quantity = asset.quantity or 1
    base_inventory = asset.inventory_number or ""
    
    return {
        "asset_id": asset.id,
        "inventory_number": base_inventory,
        "name": asset.name or "",
        "quantity": quantity,
        "preview": [
            {
                "new_inventory": f"{base_inventory}-{i}",
                "new_serial": f"{asset.serial_number}-{i}" if asset.serial_number else None,
                "purchase_price": f"{(asset.purchase_price / quantity):.2f}" if asset.purchase_price else None,
                "current_value": f"{(asset.current_value / quantity):.2f}" if asset.current_value else None,
            }
            for i in range(1, quantity + 1)
        ],
    }
