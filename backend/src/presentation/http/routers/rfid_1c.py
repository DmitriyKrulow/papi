# backend/src/presentation/http/routers/rfid_1c.py
"""Синхронизация с 1С — экспорт/импорт данных об активах"""
import logging
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from src.infrastructure.db.init_db import get_db
from src.infrastructure.db.models.asset import Asset
from src.infrastructure.db.models.user import User
from src.presentation.http.dependencies.auth import get_current_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sync/1c", tags=["1c-sync"])


@router.get("/export")
async def export_to_1c(
    department_code: Optional[str] = Query(None, description="Фильтр по подразделению"),
    asset_type: Optional[str] = Query(None, description="Фильтр по типу актива"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Экспорт данных об активах для импорта в 1С.
    
    Возвращает список активов в формате, совместимом с 1С:
    - Инвентарный номер
    - Наименование
    - Модель
    - Подразделение
    - Ответственное лицо
    - Помещение
    - Дата покупки
    - Первоначальная стоимость
    - Остаточная стоимость
    - RFID-метка (если есть)
    """
    query = db.query(Asset).filter(Asset.is_active == True)
    
    if department_code:
        query = query.filter(Asset.department_code == department_code)
    if asset_type:
        query = query.filter(Asset.asset_type == asset_type)
    
    assets = query.all()
    
    export_data = []
    for asset in assets:
        export_data.append({
            "InventoryNumber": asset.inventory_number or "",
            "Name": asset.name or "",
            "Description": asset.description or "",
            "Model": asset.model or "",
            "AssetType": asset.asset_type or "",
            "DepartmentCode": asset.department_code or "",
            "DepartmentName": asset.department_code or "",
            "ResponsiblePerson": asset.responsible_person or "",
            "Location": asset.location_address or "",
            "Room": "",  # Можно добавить через relationship
            "PurchaseDate": asset.purchase_date.isoformat() if asset.purchase_date else "",
            "PurchasePrice": float(asset.purchase_price or 0),
            "CurrentValue": float(asset.current_value or 0),
            "SerialNumber": asset.serial_number or "",
            "RfidTag": asset.rfid_tag or "",
            "Status": asset.status or "",
            "CommissioningDate": asset.commissioning_date.isoformat() if asset.commissioning_date else "",
            "WarrantyExpiry": asset.warranty_expiry.isoformat() if asset.warranty_expiry else "",
            "Capacity": float(asset.capacity or 0) if asset.capacity else None,
            "Power": asset.power or "",
            "Weight": asset.weight or "",
            "LastInventoryDate": asset.last_inventory_date.isoformat() if asset.last_inventory_date else "",
            "LastInventoryConfirmed": bool(asset.last_inventory_confirmed),
        })
    
    return {
        "export_date": datetime.now().isoformat(),
        "total_assets": len(export_data),
        "assets": export_data
    }


@router.post("/import")
async def import_from_1c(
    assets: List[dict],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Импорт данных об активах из 1С.
    
    Принимает массив активов в формате 1С и обновляет/создаёт записи в БД.
    Используется для первичной загрузки данных или периодической синхронизации.
    
    Формат входящих данных:
    [
      {
        "InventoryNumber": "ИНВ000001",
        "Name": "Ноутбук Dell",
        "Model": "Latitude 5520",
        "DepartmentCode": "IT",
        "ResponsiblePerson": "Иванов И.И.",
        "PurchasePrice": 75000.00,
        ...
      }
    ]
    """
    results = {
        "created": [],
        "updated": [],
        "errors": []
    }
    
    for i, data in enumerate(assets):
        inventory_number = data.get("InventoryNumber", "")
        
        if not inventory_number:
            results["errors"].append({
                "index": i,
                "error": "Отсутствует инвентарный номер"
            })
            continue
        
        # Ищем существующий актив
        existing = db.query(Asset).filter(
            Asset.inventory_number == inventory_number
        ).first()
        
        try:
            if existing:
                # Обновляем существующий
                existing.name = data.get("Name", existing.name)
                existing.description = data.get("Description", existing.description)
                existing.model = data.get("Model", existing.model)
                existing.asset_type = data.get("AssetType", existing.asset_type)
                existing.department_code = data.get("DepartmentCode", existing.department_code)
                existing.responsible_person = data.get("ResponsiblePerson", existing.responsible_person)
                existing.location_address = data.get("Location", existing.location_address)
                existing.purchase_price = data.get("PurchasePrice")
                existing.current_value = data.get("CurrentValue")
                existing.serial_number = data.get("SerialNumber", existing.serial_number)
                existing.rfid_tag = data.get("RfidTag", existing.rfid_tag)
                existing.status = data.get("Status", existing.status)
                existing.purchase_date = datetime.fromisoformat(data["PurchaseDate"]).date() if data.get("PurchaseDate") else existing.purchase_date
                existing.commissioning_date = datetime.fromisoformat(data["CommissioningDate"]).date() if data.get("CommissioningDate") else existing.commissioning_date
                existing.warranty_expiry = datetime.fromisoformat(data["WarrantyExpiry"]).date() if data.get("WarrantyExpiry") else existing.warranty_expiry
                
                results["updated"].append({
                    "inventory_number": inventory_number,
                    "name": existing.name
                })
            else:
                # Создаём новый
                new_asset = Asset(
                    inventory_number=inventory_number,
                    name=data.get("Name", ""),
                    description=data.get("Description", ""),
                    model=data.get("Model", ""),
                    asset_type=data.get("AssetType", ""),
                    department_code=data.get("DepartmentCode", ""),
                    responsible_person=data.get("ResponsiblePerson", ""),
                    location_address=data.get("Location", ""),
                    purchase_price=data.get("PurchasePrice"),
                    current_value=data.get("CurrentValue"),
                    serial_number=data.get("SerialNumber", ""),
                    rfid_tag=data.get("RfidTag", ""),
                    status=data.get("Status", "active"),
                    purchase_date=datetime.fromisoformat(data["PurchaseDate"]).date() if data.get("PurchaseDate") else None,
                    commissioning_date=datetime.fromisoformat(data["CommissioningDate"]).date() if data.get("CommissioningDate") else None,
                    warranty_expiry=datetime.fromisoformat(data["WarrantyExpiry"]).date() if data.get("WarrantyExpiry") else None,
                    capacity=data.get("Capacity"),
                    power=data.get("Power", ""),
                    weight=data.get("Weight", ""),
                )
                db.add(new_asset)
                results["created"].append({
                    "inventory_number": inventory_number,
                    "name": data.get("Name", "")
                })
        except Exception as e:
            results["errors"].append({
                "index": i,
                "inventory_number": inventory_number,
                "error": str(e)
            })
    
    db.commit()
    
    return {
        "success": True,
        "import_date": datetime.now().isoformat(),
        "total_processed": len(assets),
        "created": len(results["created"]),
        "updated": len(results["updated"]),
        "errors": len(results["errors"]),
        "details": results
    }


@router.get("/status")
async def get_sync_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Статус синхронизации с 1С"""
    total_assets = db.query(func.count(Asset.id)).filter(Asset.is_active == True).scalar()
    with_rfid = db.query(func.count(Asset.id)).filter(
        Asset.is_active == True,
        Asset.rfid_tag.isnot(None),
        Asset.rfid_tag != ""
    ).scalar()
    
    last_inventory = db.query(func.max(Asset.last_inventory_date)).scalar()
    
    return {
        "total_active_assets": total_assets,
        "assets_with_rfid": with_rfid,
        "rfid_coverage_percent": round(with_rfid / total_assets * 100, 1) if total_assets > 0 else 0,
        "last_inventory_date": last_inventory.isoformat() if last_inventory else None,
        "sync_ready": with_rfid > 0  # Готово к синхронизации если есть хотя бы 1 актив с RFID
    }
