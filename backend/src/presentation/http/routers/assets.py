# backend/src/presentation/http/routers/assets.py
import os
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text
from datetime import datetime
from decimal import Decimal
from typing import Optional, Any

from src.infrastructure.db.init_db import get_db
from src.infrastructure.db.models.asset import Asset
from src.infrastructure.db.models.asset_photo import AssetPhoto as AssetPhotoModel
from src.infrastructure.db.models.document import Document
from src.infrastructure.db.models.department import Department
from src.infrastructure.db.models.user import User
from src.presentation.http.dependencies.auth import get_current_user
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
    assigned_employee_name = None
    
    if getattr(asset, 'employee_id', None) and db is not None:
        emp = db.query(Employee).filter(Employee.id == asset.employee_id).first()
        if emp:
            assigned_employee_name = f"{emp.last_name} {emp.first_name}"
    
    if db and getattr(asset, 'department_code', None):
        dept = db.query(Department).filter(
            (Department.code == asset.department_code) | (Department.name == asset.department_code),
            Department.is_active == True
        ).first()
        if dept:
            department_name = f"{dept.name} ({dept.code})"
            if not assigned_employee_name:
                employees = db.query(Employee).filter(
                    Employee.department_id == dept.id,
                    Employee.is_active == True
                ).order_by(Employee.last_name, Employee.first_name).all()
                if employees:
                    emp_names = [f"{e.last_name} {e.first_name}" for e in employees]
                    employee_name = ", ".join(emp_names[:5])

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
        "quantity": getattr(asset, 'quantity', 1),
        "department_code": safe_str(getattr(asset, 'department_code', None)),
        "department_name": safe_str(department_name),
        "responsible_person": safe_str(getattr(asset, 'responsible_person', None)),
        "employee_name": safe_str(assigned_employee_name or employee_name),
        "assigned_employee_id": getattr(asset, 'employee_id', None),
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
        "is_active": getattr(asset, 'is_active', True),
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
    include_hidden: bool = False,
    db: Session = Depends(get_db),
):
    """
    Получить список активов с пагинацией и фильтрацией.
    """
    try:
        query = db.query(Asset).options(joinedload(Asset.asset_type_config))
        
        if not include_hidden:
            query = query.filter(Asset.is_active == True)
        
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
        db.rollback()
        import traceback
        print(f"ERROR updating asset {asset_id}: {e}")
        traceback.print_exc()
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
            quantity=int(asset_data.get("quantity", 1)),
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
            employee_id=asset_data.get("employee_id"),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        db.add(asset)
        db.commit()
        db.refresh(asset)
        
        return asset_to_dict(asset, db)
        
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
    current_user: User = Depends(get_current_user),
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
            asset.purchase_price = Decimal(str(asset_data["purchase_price"])) if asset_data["purchase_price"] is not None else None
        if "current_value" in asset_data:
            asset.current_value = Decimal(str(asset_data["current_value"])) if asset_data["current_value"] is not None else None
        if "quantity" in asset_data:
            asset.quantity = int(asset_data["quantity"]) if asset_data["quantity"] is not None else 1
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
        if "capacity" in asset_data:
            asset.capacity = Decimal(str(asset_data["capacity"])) if asset_data["capacity"] is not None else None
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
            asset.depreciation_years = asset_data["depreciation_years"] if asset_data["depreciation_years"] is not None else None
        if "employee_id" in asset_data:
            asset.employee_id = asset_data["employee_id"] if asset_data["employee_id"] is not None else None
        
        asset.updated_at = datetime.now()
        
        db.commit()
        db.refresh(asset)
        
        return asset_to_dict(asset, db)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{asset_id}")
async def delete_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Скрыть актив (soft delete). Статус меняется на 'written_off'.
    """
    try:
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        asset.is_active = False
        asset.status = "written_off"
        asset.updated_at = datetime.now()
        db.commit()
        
        return {"message": "Asset hidden successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{asset_id}/hard")
async def hard_delete_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Полностью удалить актив (hard delete). Только для администраторов.
    Также удаляются связанные заявки на ремонт и события обслуживания.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Только администратор может полностью удалять активы")
    
    try:
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        # Удаляем фотографии и связанные документы
        photos = db.query(AssetPhotoModel).filter(AssetPhotoModel.asset_id == asset_id).all()
        for photo in photos:
            doc = db.query(Document).filter(Document.id == photo.document_id).first()
            if doc:
                if os.path.exists(doc.file_path):
                    os.remove(doc.file_path)
                db.delete(doc)
            db.delete(photo)
        
        # Удаляем связанные заявки на ремонт
        from src.infrastructure.db.models.repair_request import RepairRequest
        db.query(RepairRequest).filter(RepairRequest.asset_id == asset_id).delete()
        
        # Удаляем связанные события обслуживания
        from src.infrastructure.db.models.maintenance_event import MaintenanceEvent
        db.query(MaintenanceEvent).filter(MaintenanceEvent.asset_id == asset_id).delete()
        
        # Удаляем сам актив
        db.delete(asset)
        db.commit()
        
        return {"message": "Asset permanently deleted", "deleted_id": asset_id}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{asset_id}/restore")
async def restore_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Восстановить скрытый актив.
    """
    try:
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        asset.is_active = True
        asset.status = "active"
        asset.updated_at = datetime.now()
        db.commit()
        db.refresh(asset)
        
        return asset_to_dict(asset, db)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{asset_id}/repair-history")
async def get_asset_repair_history(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Получить историю ремонтов для актива.
    Возвращает только одобренные, выполняемые и завершённые заявки.
    Для скрытых (списанных) активов доступно только администраторам.
    """
    try:
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        # Скрытые активы видны только администраторам
        if not asset.is_active and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Актив скрыт. Доступно только администраторам")
        
        from src.infrastructure.db.models.repair_request import RepairRequest
        
        repairs = db.query(RepairRequest).options(
            joinedload(RepairRequest.creator),
            joinedload(RepairRequest.assignee)
        ).filter(
            RepairRequest.asset_id == asset_id,
            RepairRequest.status.in_(["approved", "in_progress", "completed"])
        ).order_by(RepairRequest.updated_at.desc()).all()
        
        def safe_str(val):
            if val is None:
                return None
            return str(val)
        
        def safe_isoformat(val):
            if val is None:
                return None
            if hasattr(val, 'isoformat') and callable(getattr(val, 'isoformat')):
                return val.isoformat()
            return str(val)
        
        def safe_decimal_to_float(val, default=0.0):
            if val is None:
                return default
            try:
                return float(val)
            except (TypeError, ValueError):
                return default
        
        items = []
        for r in repairs:
            items.append({
                "id": r.id,
                "asset_id": r.asset_id,
                "title": safe_str(r.title),
                "description": safe_str(r.description),
                "priority": r.priority.value if r.priority else "medium",
                "status": r.status.value if r.status else "draft",
                "created_by": r.created_by,
                "creator_name": safe_str(r.creator.username) if r.creator else None,
                "created_at": safe_isoformat(r.created_at),
                "assigned_to": r.assigned_to,
                "assigned_at": safe_isoformat(r.assigned_at),
                "actual_completion_date": safe_isoformat(r.actual_completion_date),
                "actual_cost": safe_decimal_to_float(r.actual_cost) if r.actual_cost else None,
                "completion_notes": safe_str(r.completion_notes),
                "rejection_reason": safe_str(r.rejection_reason),
                "updated_at": safe_isoformat(r.updated_at),
                "assigned_to_name": safe_str(r.assignee.username) if r.assignee else None,
                "desired_completion_date": safe_isoformat(r.desired_completion_date),
                "deadline": safe_isoformat(r.deadline),
                "estimated_cost": safe_decimal_to_float(r.estimated_cost) if r.estimated_cost else None,
            })
        
        return {
            "items": items,
            "total": len(items),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{asset_id}/photos")
async def get_asset_photos(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Получить все фотографии актива.
    """
    try:
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        photos = db.query(AssetPhotoModel).filter(
            AssetPhotoModel.asset_id == asset_id
        ).order_by(AssetPhotoModel.sort_order, AssetPhotoModel.uploaded_at.desc()).all()
        
        items = []
        for photo in photos:
            doc = db.query(Document).filter(Document.id == photo.document_id).first() if photo.document_id else None
            items.append({
                "id": photo.id,
                "asset_id": photo.asset_id,
                "document_id": photo.document_id,
                "uploaded_by": photo.uploaded_by,
                "stage": photo.stage,
                "photo_category": photo.photo_category,
                "description": photo.description,
                "is_before": photo.is_before,
                "is_after": photo.is_after,
                "sort_order": photo.sort_order,
                "uploaded_at": photo.uploaded_at.isoformat() if photo.uploaded_at else None,
                "filename": doc.filename if doc else None,
                "file_size": doc.file_size if doc else None,
                "mime_type": doc.mime_type if doc else None,
            })
        
        return {"items": items, "total": len(items)}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))