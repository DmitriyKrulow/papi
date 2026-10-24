# backend/src/presentation/http/routers/asset_units.py
"""API для управления единицами актива (AssetUnit)

Позволяет:
- Создавать единицы для активов с quantity > 1
- Получать список единиц актива
- Передавать единицу сотруднику
- Получать детальную информацию по единице
"""
import logging
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime

from src.infrastructure.db.init_db import get_db
from src.infrastructure.db.models.asset_unit import AssetUnit
from src.infrastructure.db.models.asset import Asset
from src.infrastructure.db.models.employee import Employee
from src.infrastructure.db.models.user import User
from src.presentation.http.dependencies.auth import get_current_user, get_current_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/asset-units", tags=["asset-units"])


@router.get("/")
async def get_asset_units(
    asset_id: Optional[int] = Query(None, description="ID актива"),
    employee_id: Optional[int] = Query(None, description="ID сотрудника"),
    status: Optional[str] = Query(None, description="Статус: active, in_repair, written_off, lost, damaged"),
    search: Optional[str] = Query(None, description="Поиск по уникальному идентификатору"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить список единиц актива с фильтрацией"""
    query = db.query(AssetUnit).filter(
        AssetUnit.is_active == True,
    )
    
    if asset_id:
        query = query.filter(AssetUnit.asset_id == asset_id)
    
    if employee_id:
        query = query.filter(AssetUnit.current_employee_id == employee_id)
    
    if status:
        query = query.filter(AssetUnit.status == status)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(AssetUnit.unique_identifier.ilike(search_pattern))
    
    units = query.order_by(AssetUnit.asset_id, AssetUnit.unit_number).all()
    
    return {
        "total": len(units),
        "units": [
            {
                "id": u.id,
                "asset_id": u.asset_id,
                "asset_name": u.asset.name if u.asset else "",
                "asset_inventory_number": u.asset.inventory_number if u.asset else "",
                "unit_number": u.unit_number,
                "unique_identifier": u.unique_identifier,
                "current_employee_id": u.current_employee_id,
                "current_employee_name": u.current_employee.last_name + " " + u.current_employee.first_name if u.current_employee else None,
                "current_department_code": u.current_department_code,
                "status": u.status,
                "last_transfer_date": u.last_transfer_date.isoformat() if u.last_transfer_date else None,
                "rfid_tag": u.rfid_tag,
                "notes": u.notes,
            }
            for u in units
        ],
    }


@router.get("/{unit_id}")
async def get_asset_unit_details(
    unit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить детальную информацию по единице актива"""
    unit = db.query(AssetUnit).filter(
        AssetUnit.id == unit_id,
    ).first()
    
    if not unit:
        raise HTTPException(status_code=404, detail="Единица актива не найдена")
    
    return {
        "id": unit.id,
        "asset_id": unit.asset_id,
        "asset_name": unit.asset.name if unit.asset else "",
        "asset_inventory_number": unit.asset.inventory_number if unit.asset else "",
        "asset_type": unit.asset.asset_type if unit.asset else "",
        "unit_number": unit.unit_number,
        "unique_identifier": unit.unique_identifier,
        "current_employee_id": unit.current_employee_id,
        "current_employee_name": f"{unit.current_employee.last_name} {unit.current_employee.first_name}" if unit.current_employee else None,
        "current_department_code": unit.current_department_code,
        "status": unit.status,
        "last_transfer_date": unit.last_transfer_date.isoformat() if unit.last_transfer_date else None,
        "rfid_tag": unit.rfid_tag,
        "notes": unit.notes,
        "created_at": unit.created_at.isoformat() if unit.created_at else None,
        "updated_at": unit.updated_at.isoformat() if unit.updated_at else None,
    }


@router.post("/")
async def create_asset_unit(
    asset_id: int = Query(..., description="ID актива"),
    unit_number: int = Query(..., description="Номер единицы"),
    unique_identifier: str = Query(..., description="Уникальный идентификатор (напр. 6464646-1)"),
    employee_id: Optional[int] = Query(None, description="ID сотрудника, которому передаётся единица"),
    department_code: Optional[str] = Query(None, description="Код подразделения"),
    rfid_tag: Optional[str] = Query(None, description="RFID метка"),
    notes: str = "",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Создать новую единицу актива"""
    # Проверяем существование актива
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Актив не найден")
    
    # Проверяем уникальность идентификатора
    existing = db.query(AssetUnit).filter(
        AssetUnit.unique_identifier == unique_identifier,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Единица с идентификатором '{unique_identifier}' уже существует")
    
    # Создаём единицу
    new_unit = AssetUnit(
        asset_id=asset_id,
        unit_number=unit_number,
        unique_identifier=unique_identifier,
        current_employee_id=employee_id,
        current_department_code=department_code,
        rfid_tag=rfid_tag,
        notes=notes,
    )
    
    # Если передан сотрудник, обновляем его в asset
    if employee_id:
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if employee:
            asset.employee_id = employee_id
            asset.responsible_person = f"{employee.last_name} {employee.first_name}"
            asset.department_code = employee.department_code
    
    db.add(new_unit)
    db.commit()
    db.refresh(new_unit)
    
    return {
        "success": True,
        "id": new_unit.id,
        "unique_identifier": new_unit.unique_identifier,
        "asset_name": asset.name,
        "asset_inventory_number": asset.inventory_number,
    }


@router.put("/{unit_id}")
async def update_asset_unit(
    unit_id: int,
    employee_id: Optional[int] = Query(None),
    department_code: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    rfid_tag: Optional[str] = Query(None),
    notes: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Обновить единицу актива"""
    unit = db.query(AssetUnit).filter(
        AssetUnit.id == unit_id,
    ).first()
    
    if not unit:
        raise HTTPException(status_code=404, detail="Единица актива не найдена")
    
    if employee_id is not None:
        unit.current_employee_id = employee_id
        unit.last_transfer_date = datetime.now()
        
        # Обновляем сотрудника в родительском активе
        if unit.asset:
            employee = db.query(Employee).filter(Employee.id == employee_id).first()
            if employee:
                unit.asset.employee_id = employee_id
                unit.asset.responsible_person = f"{employee.last_name} {employee.first_name}"
                unit.asset.department_code = employee.department_code
                unit.current_department_code = employee.department_code
    
    if department_code is not None:
        unit.current_department_code = department_code
    
    if status is not None:
        unit.status = status
    
    if rfid_tag is not None:
        unit.rfid_tag = rfid_tag
    
    if notes is not None:
        unit.notes = notes
    
    db.commit()
    db.refresh(unit)
    
    return {
        "success": True,
        "id": unit.id,
        "unique_identifier": unit.unique_identifier,
    }


@router.post("/{unit_id}/transfer")
async def transfer_asset_unit(
    unit_id: int,
    to_employee_id: int = Query(..., description="ID сотрудника, которому передаётся"),
    from_employee_id: Optional[int] = Query(None, description="ID текущего сотрудника"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Передать единицу актива сотруднику"""
    unit = db.query(AssetUnit).filter(
        AssetUnit.id == unit_id,
    ).first()
    
    if not unit:
        raise HTTPException(status_code=404, detail="Единица актива не найдена")
    
    to_employee = db.query(Employee).filter(Employee.id == to_employee_id).first()
    if not to_employee:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")
    
    # Сохраняем предыдущего сотрудника
    prev_employee_id = unit.current_employee_id
    prev_employee_name = None
    if prev_employee_id:
        prev_emp = db.query(Employee).filter(Employee.id == prev_employee_id).first()
        if prev_emp:
            prev_employee_name = f"{prev_emp.last_name} {prev_emp.first_name}"
    
    # Обновляем единицу
    unit.current_employee_id = to_employee_id
    unit.current_department_code = to_employee.department_code if to_employee.department_code else None
    unit.last_transfer_date = datetime.now()
    
    # Обновляем родительский актив
    if unit.asset:
        unit.asset.employee_id = to_employee_id
        unit.asset.responsible_person = f"{to_employee.last_name} {to_employee.first_name}"
        if to_employee.department_code:
            unit.asset.department_code = to_employee.department_code
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Единица {unit.unique_identifier} передана {to_employee.last_name} {to_employee.first_name}",
        "unit_id": unit.id,
        "unique_identifier": unit.unique_identifier,
        "to_employee_id": to_employee_id,
        "to_employee_name": f"{to_employee.last_name} {to_employee.first_name}",
        "from_employee_id": prev_employee_id,
        "from_employee_name": prev_employee_name,
        "transfer_date": datetime.now().isoformat(),
    }


@router.get("/by-identifier/{identifier}")
async def get_asset_unit_by_identifier(
    identifier: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить единицу актива по уникальному идентификатору"""
    unit = db.query(AssetUnit).filter(
        AssetUnit.unique_identifier == identifier,
    ).first()
    
    if not unit:
        raise HTTPException(status_code=404, detail=f"Единица с идентификатором '{identifier}' не найдена")
    
    return {
        "id": unit.id,
        "asset_id": unit.asset_id,
        "asset_name": unit.asset.name if unit.asset else "",
        "asset_inventory_number": unit.asset.inventory_number if unit.asset else "",
        "asset_type": unit.asset.asset_type if unit.asset else "",
        "unit_number": unit.unit_number,
        "unique_identifier": unit.unique_identifier,
        "current_employee_id": unit.current_employee_id,
        "current_employee_name": f"{unit.current_employee.last_name} {unit.current_employee.first_name}" if unit.current_employee else None,
        "current_department_code": unit.current_department_code,
        "status": unit.status,
        "last_transfer_date": unit.last_transfer_date.isoformat() if unit.last_transfer_date else None,
        "rfid_tag": unit.rfid_tag,
        "notes": unit.notes,
    }
