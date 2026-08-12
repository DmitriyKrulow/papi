# backend/src/presentation/http/routers/data_export.py
"""Экспорт всех данных системы в JSON-формат для полного восстановления."""
import json
import logging
from datetime import datetime
from io import BytesIO
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text

from src.infrastructure.db.init_db import get_db
from src.infrastructure.db.models.department import Department, Room
from src.infrastructure.db.models.employee import Employee
from src.infrastructure.db.models.asset import Asset
from src.infrastructure.db.models.user import User
from src.presentation.http.dependencies.auth import get_current_admin

router = APIRouter(prefix="/api/admin/data", tags=["data-export"])

logger = logging.getLogger(__name__)


def _safe_isoformat(value: Optional[Any]) -> Optional[str]:
    """Безопасно преобразует дату в ISO-строку."""
    if value is None:
        return None
    try:
        if hasattr(value, 'isoformat') and callable(getattr(value, 'isoformat')):
            return value.isoformat()
        return str(value)
    except (AttributeError, ValueError):
        return None


def _safe_str(value: Optional[Any], default: str = "") -> str:
    """Безопасно преобразует значение в строку."""
    if value is None:
        return default
    try:
        return str(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Optional[Any], default: Optional[int] = None) -> Optional[int]:
    """Безопасно преобразует значение в int."""
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_float(value: Optional[Any], default: Optional[float] = None) -> Optional[float]:
    """Безопасно преобразует значение в float."""
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# ============================================================================
# Экспорт данных
# ============================================================================

def export_departments(db: Session) -> List[Dict[str, Any]]:
    """Экспортирует все подразделения."""
    departments = db.query(Department).filter(Department.is_active == True).all()
    result = []
    for dept in departments:
        result.append({
            "id": getattr(dept, 'id', None),
            "organization_id": getattr(dept, 'organization_id', 1),
            "name": _safe_str(getattr(dept, 'name', None)),
            "code": _safe_str(getattr(dept, 'code', None)),
            "parent_id": _safe_int(getattr(dept, 'parent_id', None)),
            "head": _safe_str(getattr(dept, 'head', None)),
            "phone": _safe_str(getattr(dept, 'phone', None)),
            "email": _safe_str(getattr(dept, 'email', None)),
            "location": _safe_str(getattr(dept, 'location', None)),
            "is_active": getattr(dept, 'is_active', True),
            "created_at": _safe_isoformat(getattr(dept, 'created_at', None)),
            "updated_at": _safe_isoformat(getattr(dept, 'updated_at', None)),
        })
    return result


def export_rooms(db: Session) -> List[Dict[str, Any]]:
    """Экспортирует все помещения."""
    rooms = db.query(Room).filter(Room.is_active == True).all()
    result = []
    for room in rooms:
        result.append({
            "id": getattr(room, 'id', None),
            "department_id": _safe_int(getattr(room, 'department_id', None)),
            "name": _safe_str(getattr(room, 'name', None)),
            "floor": _safe_str(getattr(room, 'floor', None)),
            "building": _safe_str(getattr(room, 'building', None)),
            "is_active": getattr(room, 'is_active', True),
            "created_at": _safe_isoformat(getattr(room, 'created_at', None)),
            "updated_at": _safe_isoformat(getattr(room, 'updated_at', None)),
        })
    return result


def export_employees(db: Session) -> List[Dict[str, Any]]:
    """Экспортирует всех сотрудников."""
    employees = db.query(Employee).filter(Employee.is_active == True).all()
    result = []
    for emp in employees:
        result.append({
            "id": getattr(emp, 'id', None),
            "department_id": _safe_int(getattr(emp, 'department_id', None)),
            "user_id": _safe_int(getattr(emp, 'user_id', None)),
            "first_name": _safe_str(getattr(emp, 'first_name', None)),
            "last_name": _safe_str(getattr(emp, 'last_name', None)),
            "middle_name": _safe_str(getattr(emp, 'middle_name', None)),
            "phone": _safe_str(getattr(emp, 'phone', None)),
            "email": _safe_str(getattr(emp, 'email', None)),
            "position": _safe_str(getattr(emp, 'position', None)),
            "position_code": _safe_str(getattr(emp, 'position_code', None)),
            "employee_number": _safe_str(getattr(emp, 'employee_number', None)),
            "hire_date": _safe_isoformat(getattr(emp, 'hire_date', None)),
            "termination_date": _safe_isoformat(getattr(emp, 'termination_date', None)),
            "is_active": getattr(emp, 'is_active', True),
            "created_at": _safe_isoformat(getattr(emp, 'created_at', None)),
            "updated_at": _safe_isoformat(getattr(emp, 'updated_at', None)),
        })
    return result


def export_assets(db: Session) -> List[Dict[str, Any]]:
    """Экспортирует все активы."""
    assets = db.query(Asset).options(joinedload(Asset.asset_type_config)).all()
    result = []
    for asset in assets:
        result.append({
            "id": getattr(asset, 'id', None),
            "inventory_number": _safe_str(getattr(asset, 'inventory_number', None)),
            "name": _safe_str(getattr(asset, 'name', None)),
            "description": _safe_str(getattr(asset, 'description', None)),
            "model": _safe_str(getattr(asset, 'model', None)),
            "asset_type": _safe_str(getattr(asset, 'asset_type', None)),
            "status": _safe_str(getattr(asset, 'status', None)),
            "purchase_price": _safe_float(getattr(asset, 'purchase_price', None)),
            "current_value": _safe_float(getattr(asset, 'current_value', None)),
            "quantity": _safe_int(getattr(asset, 'quantity', None), 1),
            "department_code": _safe_str(getattr(asset, 'department_code', None)),
            "responsible_person": _safe_str(getattr(asset, 'responsible_person', None)),
            "location_address": _safe_str(getattr(asset, 'location_address', None)),
            "manufacturer_code": _safe_str(getattr(asset, 'manufacturer_code', None)),
            "manufacturer_name": _safe_str(getattr(asset, 'manufacturer_name', None)),
            "purchase_date": _safe_isoformat(getattr(asset, 'purchase_date', None)),
            "commissioning_date": _safe_isoformat(getattr(asset, 'commissioning_date', None)),
            "warranty_expiry": _safe_isoformat(getattr(asset, 'warranty_expiry', None)),
            "serial_number": _safe_str(getattr(asset, 'serial_number', None)),
            "capacity": _safe_float(getattr(asset, 'capacity', None)),
            "power": _safe_str(getattr(asset, 'power', None)),
            "weight": _safe_str(getattr(asset, 'weight', None)),
            "consumable_type": _safe_str(getattr(asset, 'consumable_type', None)),
            "crypto_wallet_address": _safe_str(getattr(asset, 'crypto_wallet_address', None)),
            "crypto_token_symbol": _safe_str(getattr(asset, 'crypto_token_symbol', None)),
            "depreciation_years": _safe_int(getattr(asset, 'depreciation_years', None)),
            "next_maintenance_date": _safe_isoformat(getattr(asset, 'next_maintenance_date', None)),
            "created_at": _safe_isoformat(getattr(asset, 'created_at', None)),
            "updated_at": _safe_isoformat(getattr(asset, 'updated_at', None)),
            "is_active": getattr(asset, 'is_active', True),
            "last_inventory_date": _safe_isoformat(getattr(asset, 'last_inventory_date', None)),
            "last_inventory_by_id": _safe_int(getattr(asset, 'last_inventory_by_id', None)),
            "last_inventory_confirmed": getattr(asset, 'last_inventory_confirmed', False),
            "employee_id": _safe_int(getattr(asset, 'employee_id', None)),
            "room_id": _safe_int(getattr(asset, 'room_id', None)),
        })
    return result


@router.get("/export/all")
async def export_all_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Экспортирует все данные системы в JSON-формате.
    Включает: подразделения, помещения, сотрудников, активы.
    
    Формат файла:
    {
      "exported_at": "2026-08-12T20:00:00",
      "version": "1.0",
      "departments": [...],
      "rooms": [...],
      "employees": [...],
      "assets": [...]
    }
    """
    try:
        logger.info(f"[DataExport] Starting full export by user: {current_user.username}")
        
        data = {
            "exported_at": datetime.now().isoformat(),
            "version": "1.0",
            "departments": export_departments(db),
            "rooms": export_rooms(db),
            "employees": export_employees(db),
            "assets": export_assets(db),
        }
        
        logger.info(f"[DataExport] Exported: {len(data['departments'])} depts, "
                    f"{len(data['rooms'])} rooms, {len(data['employees'])} employees, "
                    f"{len(data['assets'])} assets")
        
        # Создаём JSON-файл для скачивания
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        
        output = BytesIO(json_str.encode('utf-8'))
        
        filename = f"papi_full_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        return StreamingResponse(
            iter([output.read()]),
            media_type='application/json',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )
        
    except Exception as e:
        logger.error(f"[DataExport] Export failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Импорт/восстановление данных
# ============================================================================

@router.post("/import/all")
async def import_all_data(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Восстанавливает все данные системы из JSON-файла экспорта.
    
    Порядок восстановления:
    1. Подразделения (зависят только от organization_id)
    2. Помещения (зависят от departments)
    3. Сотрудники (зависят от departments)
    4. Активы (зависят от departments, employees)
    
    Все существующие данные удаляются перед восстановлением.
    """
    try:
        body = await request.body()
        if not body:
            raise HTTPException(status_code=400, detail="Файл не передан")
        
        # Парсим JSON
        data = json.loads(body.decode('utf-8'))
        
        if not isinstance(data, dict):
            raise HTTPException(status_code=400, detail="Неверный формат файла")
        
        # Проверяем обязательные секции
        required_sections = ["departments", "rooms", "employees", "assets"]
        for section in required_sections:
            if section not in data:
                raise HTTPException(status_code=400, detail=f"Отсутствует раздел: {section}")
        
        logger.info(f"[DataImport] Starting full import by user: {current_user.username}")
        logger.info(f"[DataImport] Sections: depts={len(data['departments'])}, "
                    f"rooms={len(data['rooms'])}, employees={len(data['employees'])}, "
                    f"assets={len(data['assets'])}")
        
        stats = {
            "departments": {"imported": 0, "skipped": 0, "errors": []},
            "rooms": {"imported": 0, "skipped": 0, "errors": []},
            "employees": {"imported": 0, "skipped": 0, "errors": []},
            "assets": {"imported": 0, "skipped": 0, "errors": []},
        }
        
        # Очистка существующих данных (в обратном порядке зависимостей)
        logger.info("[DataImport] Clearing existing data...")
        from src.infrastructure.db.models.asset import Asset as AssetModel
        db.query(AssetModel).delete()
        db.query(Employee).delete()
        db.query(Room).delete()
        db.query(Department).delete()
        db.commit()
        
        # 1. Восстанавливаем подразделения
        logger.info("[DataImport] Restoring departments...")
        for dept_data in data.get("departments", []):
            try:
                dept = Department(
                    organization_id=dept_data.get("organization_id", 1),
                    name=dept_data.get("name", ""),
                    code=dept_data.get("code", ""),
                    parent_id=dept_data.get("parent_id"),
                    head=dept_data.get("head"),
                    phone=dept_data.get("phone"),
                    email=dept_data.get("email"),
                    location=dept_data.get("location"),
                    is_active=dept_data.get("is_active", True),
                    created_at=datetime.fromisoformat(dept_data["created_at"]) if dept_data.get("created_at") else datetime.now(),
                    updated_at=datetime.fromisoformat(dept_data["updated_at"]) if dept_data.get("updated_at") else datetime.now(),
                )
                db.add(dept)
                stats["departments"]["imported"] += 1
            except Exception as e:
                stats["departments"]["skipped"] += 1
                stats["departments"]["errors"].append(f"Department '{dept_data.get('code', '?')}': {str(e)}")
        
        db.commit()
        
        # 2. Восстанавливаем помещения
        logger.info("[DataImport] Restoring rooms...")
        for room_data in data.get("rooms", []):
            try:
                room = Room(
                    department_id=room_data.get("department_id"),
                    name=room_data.get("name", ""),
                    floor=room_data.get("floor"),
                    building=room_data.get("building"),
                    is_active=room_data.get("is_active", True),
                    created_at=datetime.fromisoformat(room_data["created_at"]) if room_data.get("created_at") else datetime.now(),
                    updated_at=datetime.fromisoformat(room_data["updated_at"]) if room_data.get("updated_at") else datetime.now(),
                )
                db.add(room)
                stats["rooms"]["imported"] += 1
            except Exception as e:
                stats["rooms"]["skipped"] += 1
                stats["rooms"]["errors"].append(f"Room '{room_data.get('name', '?')}': {str(e)}")
        
        db.commit()
        
        # 3. Восстанавливаем сотрудников
        logger.info("[DataImport] Restoring employees...")
        for emp_data in data.get("employees", []):
            try:
                emp = Employee(
                    department_id=emp_data.get("department_id"),
                    user_id=emp_data.get("user_id"),
                    first_name=emp_data.get("first_name", ""),
                    last_name=emp_data.get("last_name", ""),
                    middle_name=emp_data.get("middle_name"),
                    phone=emp_data.get("phone"),
                    email=emp_data.get("email"),
                    position=emp_data.get("position"),
                    position_code=emp_data.get("position_code"),
                    employee_number=emp_data.get("employee_number"),
                    hire_date=datetime.fromisoformat(emp_data["hire_date"]).date() if emp_data.get("hire_date") else None,
                    termination_date=datetime.fromisoformat(emp_data["termination_date"]).date() if emp_data.get("termination_date") else None,
                    is_active=emp_data.get("is_active", True),
                    created_at=datetime.fromisoformat(emp_data["created_at"]) if emp_data.get("created_at") else datetime.now(),
                    updated_at=datetime.fromisoformat(emp_data["updated_at"]) if emp_data.get("updated_at") else datetime.now(),
                )
                db.add(emp)
                stats["employees"]["imported"] += 1
            except Exception as e:
                stats["employees"]["skipped"] += 1
                stats["employees"]["errors"].append(f"Employee '{emp_data.get('last_name', '?')}': {str(e)}")
        
        db.commit()
        
        # 4. Восстанавливаем активы
        logger.info("[DataImport] Restoring assets...")
        from datetime import date
        for asset_data in data.get("assets", []):
            try:
                # Парсим даты
                purchase_date = None
                if asset_data.get("purchase_date"):
                    try:
                        purchase_date = datetime.fromisoformat(asset_data["purchase_date"]).date()
                    except:
                        pass
                
                commissioning_date = None
                if asset_data.get("commissioning_date"):
                    try:
                        commissioning_date = datetime.fromisoformat(asset_data["commissioning_date"]).date()
                    except:
                        pass
                
                warranty_expiry = None
                if asset_data.get("warranty_expiry"):
                    try:
                        warranty_expiry = datetime.fromisoformat(asset_data["warranty_expiry"]).date()
                    except:
                        pass
                
                next_maintenance_date = None
                if asset_data.get("next_maintenance_date"):
                    try:
                        next_maintenance_date = datetime.fromisoformat(asset_data["next_maintenance_date"]).date()
                    except:
                        pass
                
                last_inventory_date = None
                if asset_data.get("last_inventory_date"):
                    try:
                        last_inventory_date = datetime.fromisoformat(asset_data["last_inventory_date"])
                    except:
                        pass
                
                from decimal import Decimal
                asset = Asset(
                    inventory_number=asset_data.get("inventory_number", ""),
                    name=asset_data.get("name", ""),
                    description=asset_data.get("description"),
                    model=asset_data.get("model"),
                    asset_type=asset_data.get("asset_type"),
                    status=asset_data.get("status", "active"),
                    purchase_price=Decimal(str(asset_data["purchase_price"])) if asset_data.get("purchase_price") is not None else Decimal("0"),
                    current_value=Decimal(str(asset_data["current_value"])) if asset_data.get("current_value") is not None else Decimal("0"),
                    quantity=asset_data.get("quantity", 1),
                    department_code=asset_data.get("department_code"),
                    responsible_person=asset_data.get("responsible_person"),
                    location_address=asset_data.get("location_address"),
                    manufacturer_code=asset_data.get("manufacturer_code"),
                    manufacturer_name=asset_data.get("manufacturer_name"),
                    purchase_date=purchase_date,
                    commissioning_date=commissioning_date,
                    warranty_expiry=warranty_expiry,
                    serial_number=asset_data.get("serial_number"),
                    capacity=Decimal(str(asset_data["capacity"])) if asset_data.get("capacity") is not None else None,
                    power=asset_data.get("power"),
                    weight=asset_data.get("weight"),
                    consumable_type=asset_data.get("consumable_type"),
                    crypto_wallet_address=asset_data.get("crypto_wallet_address"),
                    crypto_token_symbol=asset_data.get("crypto_token_symbol"),
                    depreciation_years=asset_data.get("depreciation_years"),
                    next_maintenance_date=next_maintenance_date,
                    created_at=datetime.fromisoformat(asset_data["created_at"]) if asset_data.get("created_at") else datetime.now(),
                    updated_at=datetime.fromisoformat(asset_data["updated_at"]) if asset_data.get("updated_at") else datetime.now(),
                    is_active=asset_data.get("is_active", True),
                    last_inventory_date=last_inventory_date,
                    last_inventory_by_id=asset_data.get("last_inventory_by_id"),
                    last_inventory_confirmed=asset_data.get("last_inventory_confirmed", False),
                    employee_id=asset_data.get("employee_id"),
                    room_id=asset_data.get("room_id"),
                )
                db.add(asset)
                stats["assets"]["imported"] += 1
            except Exception as e:
                stats["assets"]["skipped"] += 1
                stats["assets"]["errors"].append(f"Asset '{asset_data.get('inventory_number', '?')}': {str(e)}")
        
        db.commit()
        
        total_imported = sum(s["imported"] for s in stats.values())
        total_skipped = sum(s["skipped"] for s in stats.values())
        
        logger.info(f"[DataImport] Import completed: imported={total_imported}, skipped={total_skipped}")
        
        return {
            "message": f"Данные восстановлены: импортировано {total_imported}, пропущено {total_skipped}",
            "imported": total_imported,
            "skipped": total_skipped,
            "stats": stats,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"[DataImport] Import failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
