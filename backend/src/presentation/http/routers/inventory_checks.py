# backend/src/presentation/http/routers/inventory_checks.py
from datetime import datetime, date
from typing import Optional, List
import os
import io
import json

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Body
from fastapi.responses import JSONResponse, FileResponse, Response
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from src.infrastructure.db.init_db import get_db
from src.infrastructure.db.models.inventory_check import InventoryCheck
from src.infrastructure.db.models.inventory_check_item import InventoryCheckItem
from src.infrastructure.db.models.asset import Asset
from src.infrastructure.db.models.user import User
from src.infrastructure.db.models.department import Department, Room
from src.infrastructure.db.models.employee import Employee
from src.presentation.http.dependencies.auth import get_current_user, get_current_admin
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/inventory-checks", tags=["inventory-checks"])

QR_DIR = "uploads/inventory/qr"
os.makedirs(QR_DIR, exist_ok=True)


def safe_str(val, default=""):
    if val is None:
        return default
    return str(val)


def safe_float(val, default=0.0):
    if val is None:
        return default
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


# ======================================================================
# Получение списка активов для проверки
# ======================================================================

def _get_assets_for_check(db: Session, check_type: str, scope_id: Optional[int] = None) -> List[Asset]:
    """Возвращает активы для указанного типа проверки"""
    query = db.query(Asset).filter(Asset.is_active == True)

    if check_type == "by_room":
        # По кабинету — ищем по location_address
        room = db.query(Room).filter(Room.id == scope_id).first()
        if room:
            query = query.filter(Asset.location_address == room.name)
        else:
            raise HTTPException(status_code=404, detail="Помещение не найдено")
    elif check_type == "by_employee":
        # По сотруднику
        emp = db.query(Employee).filter(Employee.id == scope_id).first()
        if emp:
            full_name = f"{emp.last_name} {emp.first_name} {emp.middle_name or ''}".strip()
            query = query.filter(Asset.responsible_person == full_name)
        else:
            raise HTTPException(status_code=404, detail="Сотрудник не найден")
    elif check_type == "by_responsible":
        # По ответственному лицу
        if scope_id:
            emp = db.query(Employee).filter(Employee.id == scope_id).first()
            if emp:
                full_name = f"{emp.last_name} {emp.first_name} {emp.middle_name or ''}".strip()
                query = query.filter(Asset.responsible_person == full_name)
            else:
                query = query.filter(Asset.responsible_person == str(scope_id))
        else:
            query = query.filter(Asset.responsible_person.isnot(None))
    # "full" — все активы

    return query.order_by(Asset.inventory_number).all()


# ======================================================================
# CRUD инвентаризаций
# ======================================================================

@router.get("")
async def list_inventory_checks(
    status: Optional[str] = Query(None, description="Фильтр по статусу"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Список всех инвентаризаций"""
    query = db.query(InventoryCheck).options(
        joinedload(InventoryCheck.creator),
        joinedload(InventoryCheck.responsible),
        joinedload(InventoryCheck.department),
    )
    if status:
        query = query.filter(InventoryCheck.status == status)
    checks = query.order_by(InventoryCheck.created_at.desc()).all()

    return JSONResponse(content=[
        {
            "id": c.id,
            "name": c.name,
            "check_date": c.check_date.isoformat() if c.check_date else None,
            "check_type": c.check_type,
            "scope_id": c.scope_id,
            "scope_name": c.scope_name,
            "department_id": c.department_id,
            "department_name": c.department.name if c.department else None,
            "total_checked": c.total_checked,
            "found": c.found,
            "missing": c.missing,
            "surplus": c.surplus,
            "status": c.status,
            "responsible_name": c.responsible.full_name if c.responsible else None,
            "creator_name": c.creator.full_name if c.creator else c.creator.username if c.creator else None,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "started_at": c.started_at.isoformat() if c.started_at else None,
            "completed_at": c.completed_at.isoformat() if c.completed_at else None,
        }
        for c in checks
    ])


@router.post("")
async def create_inventory_check(
    name: str = Query(..., description="Название проверки"),
    check_date: str = Query(..., description="Дата проверки (YYYY-MM-DD)"),
    check_type: str = Query("full", description="Тип: full, by_room, by_employee, by_responsible"),
    scope_id: Optional[int] = Query(None, description="ID помещения/сотрудника"),
    scope_name: Optional[str] = Query(None, description="Название объекта проверки"),
    department_id: Optional[int] = Query(None, description="ID подразделения"),
    commission_members: Optional[str] = Query(None, description="Члены комиссии"),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Создать новую инвентаризацию (только админ)"""
    try:
        check_date_parsed = date.fromisoformat(check_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат даты. Используйте YYYY-MM-DD")

    inv_check = InventoryCheck(
        name=name,
        check_date=check_date_parsed,
        check_type=check_type,
        scope_id=scope_id,
        scope_name=scope_name,
        department_id=department_id,
        status="draft",
        responsible_id=admin.id,
        commission_members=commission_members,
        created_by=admin.id,
        created_at=datetime.now(),
    )
    db.add(inv_check)
    db.commit()
    db.refresh(inv_check)

    return JSONResponse(content={
        "id": inv_check.id,
        "name": inv_check.name,
        "check_type": inv_check.check_type,
        "status": inv_check.status,
        "message": "Инвентаризация создана",
    })


@router.get("/{check_id:int}")
async def get_inventory_check(
    check_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Детальная информация об инвентаризации"""
    inv_check = db.query(InventoryCheck).options(
        joinedload(InventoryCheck.creator),
        joinedload(InventoryCheck.responsible),
        joinedload(InventoryCheck.department),
        joinedload(InventoryCheck.items).joinedload(InventoryCheckItem.asset),
        joinedload(InventoryCheck.items).joinedload(InventoryCheckItem.confirmed_by_user),
    ).filter(InventoryCheck.id == check_id).first()

    if not inv_check:
        raise HTTPException(status_code=404, detail="Инвентаризация не найдена")

    items_list = []
    for item in inv_check.items:
        a = item.asset
        items_list.append({
            "id": item.id,
            "asset_id": item.asset_id,
            "inventory_number": safe_str(a.inventory_number),
            "asset_name": safe_str(a.name),
            "asset_type": safe_str(a.asset_type),
            "model": safe_str(a.model),
            "location": safe_str(a.location_address),
            "responsible": safe_str(a.responsible_person),
            "result": item.result,
            "comment": item.comment,
            "confirmed_by": item.confirmed_by_user.full_name if item.confirmed_by_user else None,
            "confirmed_at": item.confirmed_at.isoformat() if item.confirmed_at else None,
        })

    return JSONResponse(content={
        "id": inv_check.id,
        "name": inv_check.name,
        "check_date": inv_check.check_date.isoformat() if inv_check.check_date else None,
        "check_type": inv_check.check_type,
        "scope_id": inv_check.scope_id,
        "scope_name": inv_check.scope_name,
        "department_id": inv_check.department_id,
        "department_name": inv_check.department.name if inv_check.department else None,
        "status": inv_check.status,
        "total_checked": inv_check.total_checked,
        "found": inv_check.found,
        "missing": inv_check.missing,
        "surplus": inv_check.surplus,
        "responsible_name": inv_check.responsible.full_name if inv_check.responsible else None,
        "creator_name": inv_check.creator.full_name if inv_check.creator else None,
        "commission_members": inv_check.commission_members,
        "created_at": inv_check.created_at.isoformat() if inv_check.created_at else None,
        "started_at": inv_check.started_at.isoformat() if inv_check.started_at else None,
        "completed_at": inv_check.completed_at.isoformat() if inv_check.completed_at else None,
        "items": items_list,
    })


@router.post("/{check_id:int}/start")
async def start_inventory_check(
    check_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Начать инвентаризацию (только админ) — сбрасывает подтверждения у активов"""
    inv_check = db.query(InventoryCheck).filter(InventoryCheck.id == check_id).first()
    if not inv_check:
        raise HTTPException(status_code=404, detail="Инвентаризация не найдена")

    if inv_check.status != "draft":
        raise HTTPException(status_code=400, detail="Инвентаризация уже начата или завершена")

    # Получаем активы для проверки
    assets = _get_assets_for_check(db, inv_check.check_type, inv_check.scope_id)

    # Удаляем старые элементы, если были
    db.query(InventoryCheckItem).filter(
        InventoryCheckItem.inventory_check_id == check_id
    ).delete()

    # Сбрасываем статус подтверждения у всех активов
    for a in assets:
        a.last_inventory_confirmed = False
        a.last_inventory_date = None
        a.last_inventory_by_id = None

    # Создаём элементы проверки
    for a in assets:
        item = InventoryCheckItem(
            inventory_check_id=check_id,
            asset_id=a.id,
            result="pending",
        )
        db.add(item)

    inv_check.total_checked = len(assets)
    inv_check.found = 0
    inv_check.missing = 0
    inv_check.status = "in_progress"
    inv_check.started_at = datetime.now()

    db.commit()

    # Отправляем уведомления ответственному лицу
    try:
        from src.core.services.notification_service import NotificationService
        service = NotificationService()
        # Уведомляем ответственного
        if inv_check.responsible_id:
            responsible = db.query(User).filter(User.id == inv_check.responsible_id).first()
            if responsible:
                service.send_inventory_notification(responsible, inv_check)
        
        # Уведомляем создателя
        if inv_check.created_by and inv_check.created_by != inv_check.responsible_id:
            creator = db.query(User).filter(User.id == inv_check.created_by).first()
            if creator:
                service.send_inventory_notification(creator, inv_check)
    except Exception as e:
        logger.warning(f"Failed to send inventory notifications: {e}")

    return JSONResponse(content={
        "message": f"Инвентаризация начата. Активов для проверки: {len(assets)}",
        "total_assets": len(assets),
    })


@router.post("/{check_id:int}/confirm/{asset_id:int}")
async def confirm_asset(
    check_id: int,
    asset_id: int,
    found: bool = Query(True, description="Актив найден?"),
    comment: Optional[str] = Query(None, description="Комментарий"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Подтвердить/отметить отсутствие актива"""
    inv_check = db.query(InventoryCheck).filter(InventoryCheck.id == check_id).first()
    if not inv_check:
        raise HTTPException(status_code=404, detail="Инвентаризация не найдена")

    if inv_check.status != "in_progress":
        raise HTTPException(status_code=400, detail="Инвентаризация не в процессе")

    item = db.query(InventoryCheckItem).filter(
        InventoryCheckItem.inventory_check_id == check_id,
        InventoryCheckItem.asset_id == asset_id,
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Актив не найден в этой инвентаризации")

    # Если актив уже был подтверждён, корректируем счётчики
    if item.result == "found":
        inv_check.found = max(0, inv_check.found - 1)
    elif item.result == "missing":
        inv_check.missing = max(0, inv_check.missing - 1)

    # Устанавливаем новый результат
    if found:
        item.result = "found"
        inv_check.found += 1
    else:
        item.result = "missing"
        inv_check.missing += 1

    item.comment = comment
    item.confirmed_by = current_user.id
    item.confirmed_at = datetime.now()

    # Обновляем информацию об активе
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if asset:
        asset.last_inventory_date = datetime.now()
        asset.last_inventory_by_id = current_user.id
        asset.last_inventory_confirmed = found

    db.commit()

    return JSONResponse(content={
        "message": f"Актив {'найден' if found else 'отсутствует'}",
        "asset_id": asset_id,
        "result": item.result,
        "found_count": inv_check.found,
        "missing_count": inv_check.missing,
        "remaining": inv_check.total_checked - inv_check.found - inv_check.missing,
    })


@router.post("/{check_id:int}/complete")
async def complete_inventory_check(
    check_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Завершить инвентаризацию (только админ)"""
    inv_check = db.query(InventoryCheck).filter(InventoryCheck.id == check_id).first()
    if not inv_check:
        raise HTTPException(status_code=404, detail="Инвентаризация не найдена")

    if inv_check.status != "in_progress":
        raise HTTPException(status_code=400, detail="Инвентаризация не в процессе или уже завершена")

    inv_check.status = "completed"
    inv_check.completed_at = datetime.now()

    db.commit()

    # Отправляем уведомления о завершении
    try:
        from src.core.services.notification_service import NotificationService
        service = NotificationService()
        if inv_check.responsible_id:
            responsible = db.query(User).filter(User.id == inv_check.responsible_id).first()
            if responsible:
                service.send_inventory_notification(responsible, inv_check)
        if inv_check.created_by and inv_check.created_by != inv_check.responsible_id:
            creator = db.query(User).filter(User.id == inv_check.created_by).first()
            if creator:
                service.send_inventory_notification(creator, inv_check)
    except Exception as e:
        logger.warning(f"Failed to send completion notifications: {e}")

    return JSONResponse(content={
        "message": "Инвентаризация завершена",
        "total": inv_check.total_checked,
        "found": inv_check.found,
        "missing": inv_check.missing,
        "accuracy": f"{(inv_check.found / inv_check.total_checked * 100):.1f}%" if inv_check.total_checked > 0 else "0%",
    })


@router.post("/{check_id:int}/cancel")
async def cancel_inventory_check(
    check_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Отменить инвентаризацию (только админ)"""
    inv_check = db.query(InventoryCheck).filter(InventoryCheck.id == check_id).first()
    if not inv_check:
        raise HTTPException(status_code=404, detail="Инвентаризация не найдена")

    if inv_check.status == "completed":
        raise HTTPException(status_code=400, detail="Нельзя отменить завершённую инвентаризацию")

    inv_check.status = "cancelled"
    db.commit()

    return JSONResponse(content={"message": "Инвентаризация отменена"})


@router.delete("/{check_id:int}")
async def delete_inventory_check(
    check_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Удалить инвентаризацию (только админ)"""
    inv_check = db.query(InventoryCheck).filter(InventoryCheck.id == check_id).first()
    if not inv_check:
        raise HTTPException(status_code=404, detail="Инвентаризация не найдена")

    db.delete(inv_check)
    db.commit()

    return JSONResponse(content={"message": "Инвентаризация удалена"})


@router.post("/{check_id:int}/reset-asset/{asset_id:int}")
async def reset_asset_confirmation(
    check_id: int,
    asset_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Сбросить статус подтверждения актива (только админ)"""
    item = db.query(InventoryCheckItem).filter(
        InventoryCheckItem.inventory_check_id == check_id,
        InventoryCheckItem.asset_id == asset_id,
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Запись не найдена")

    # Корректируем счётчики
    inv_check = db.query(InventoryCheck).filter(InventoryCheck.id == check_id).first()
    if item.result == "found":
        inv_check.found = max(0, inv_check.found - 1)
    elif item.result == "missing":
        inv_check.missing = max(0, inv_check.missing - 1)

    item.result = "pending"
    item.comment = None
    item.confirmed_by = None
    item.confirmed_at = None

    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if asset:
        asset.last_inventory_confirmed = False

    db.commit()

    return JSONResponse(content={"message": "Статус подтверждения сброшен"})


# ======================================================================
# QR-коды
# ======================================================================

@router.get("/{check_id:int}/qr-text")
async def get_inventory_qr_text(
    check_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить текст для QR-кода инвентаризации (для печати/генерации)"""
    inv_check = db.query(InventoryCheck).filter(InventoryCheck.id == check_id).first()
    if not inv_check:
        raise HTTPException(status_code=404, detail="Инвентаризация не найдена")

    # Формируем ссылку для проверки
    base_url = "http://localhost:5173"
    qr_data = {
        "type": "inventory_check",
        "check_id": check_id,
        "check_name": inv_check.name,
        "check_date": inv_check.check_date.isoformat() if inv_check.check_date else None,
        "url": f"{base_url}/inventory/{check_id:int}",
    }

    return JSONResponse(content={
        "qr_text": json.dumps(qr_data, ensure_ascii=False),
        "qr_url": f"{base_url}/inventory/{check_id:int}",
        "check_id": check_id,
        "check_name": inv_check.name,
    })


@router.get("/{check_id:int}/qr/{asset_id:int}")
async def get_asset_qr(
    check_id: int,
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Сгенерировать QR-код для конкретного актива в инвентаризации"""
    inv_check = db.query(InventoryCheck).filter(InventoryCheck.id == check_id).first()
    if not inv_check:
        raise HTTPException(status_code=404, detail="Инвентаризация не найдена")

    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Актив не найден")

    # Формируем ссылку на мобильную страницу актива
    base_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    asset_url = f"{base_url}/inventory/asset/{asset_id}?check_id={check_id}"
    
    qr_data = json.dumps({
        "type": "asset_check",
        "check_id": check_id,
        "asset_id": asset_id,
        "inventory_number": safe_str(asset.inventory_number),
        "asset_name": safe_str(asset.name),
        "url": asset_url,
    }, ensure_ascii=False)

    return JSONResponse(content={
        "qr_text": qr_data,
        "qr_url": asset_url,
        "asset_id": asset_id,
        "inventory_number": safe_str(asset.inventory_number),
        "asset_name": safe_str(asset.name),
    })


@router.get("/{check_id:int}/qr-image")
async def get_inventory_qr_image(
    check_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Сгенерировать и скачать QR-код инвентаризации как PNG"""
    try:
        import qrcode
        from PIL import Image
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="Библиотека qrcode не установлена. Выполните: pip install qrcode[pil]"
        )

    inv_check = db.query(InventoryCheck).filter(InventoryCheck.id == check_id).first()
    if not inv_check:
        raise HTTPException(status_code=404, detail="Инвентаризация не найдена")

    base_url = "http://localhost:5173"
    qr_text = f"{base_url}/inventory/{check_id:int}"

    qr = qrcode.QRCode(version=2, box_size=10, border=2)
    qr.add_data(qr_text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    return Response(
        content=buf.getvalue(),
        media_type="image/png",
        headers={
            "Content-Disposition": f'attachment; filename="inventory_{check_id:int}_qr.png"'
        },
    )


# ======================================================================
# Вспомогательные endpoints
# ======================================================================

@router.get("/scope-options")
async def get_scope_options(
    check_type: str = Query(..., description="Тип проверки"),
    department_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить список доступных объектов для проверки (комнаты, сотрудники, пользователи)"""
    try:
        if check_type == "by_room":
            query = db.query(Room).filter(Room.is_active == True)
            if department_id:
                query = query.filter(Room.department_id == department_id)
            rooms = query.order_by(Room.name).all()
            return [
                {"id": r.id, "name": r.name, "department_id": r.department_id,
                 "building": r.building, "floor": r.floor}
                for r in rooms
            ]
        elif check_type == "by_employee":
            employees = db.query(Employee).filter(Employee.is_active == True).order_by(Employee.last_name).all()
            return [
                {
                    "id": e.id,
                    "name": f"{e.last_name} {e.first_name} {e.middle_name or ''}".strip(),
                    "department_id": e.department_id,
                    "position": e.position,
                    "type": "employee",
                }
                for e in employees
            ]
        elif check_type == "by_responsible":
            users = db.query(User).filter(User.is_active == True).order_by(User.username).all()
            return [
                {
                    "id": u.id,
                    "name": u.full_name or u.username,
                    "username": u.username,
                    "role": u.role,
                    "type": "user",
                }
                for u in users
            ]
        return []
    except Exception as e:
        return []
    except Exception as e:
        return JSONResponse(content=[])


@router.get("/asset-check-status/{asset_id:int}")
async def get_asset_check_status(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить статус проверки актива"""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Актив не найден")

    return JSONResponse(content={
        "asset_id": asset.id,
        "inventory_number": safe_str(asset.inventory_number),
        "last_inventory_date": asset.last_inventory_date.isoformat() if asset.last_inventory_date else None,
        "last_inventory_by_id": asset.last_inventory_by_id,
        "last_inventory_confirmed": asset.last_inventory_confirmed,
    })


@router.get("/active")
async def get_active_inventory_check(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить текущую активную инвентаризацию (если есть)"""
    active_check = db.query(InventoryCheck).filter(
        InventoryCheck.status == "in_progress"
    ).order_by(InventoryCheck.created_at.desc()).first()

    if not active_check:
        return JSONResponse(content=None)

    return JSONResponse(content={
        "id": active_check.id,
        "name": active_check.name,
        "check_type": active_check.check_type,
        "started_at": active_check.started_at.isoformat() if active_check.started_at else None,
        "found": active_check.found,
        "missing": active_check.missing,
        "total_checked": active_check.total_checked,
    })


@router.get("/my-assets")
async def get_my_assets_for_inventory(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить список активов пользователя для инвентаризации"""
    # Получаем активы, где пользователь указан как ответственное лицо
    assets = db.query(Asset).filter(
        Asset.responsible_person == (current_user.full_name or current_user.username),
        Asset.is_active == True
    ).order_by(Asset.inventory_number).all()
    
    return JSONResponse(content=[{
        "id": a.id,
        "inventory_number": safe_str(a.inventory_number),
        "name": safe_str(a.name),
        "model": safe_str(a.model),
        "location": safe_str(a.location_address),
        "responsible": safe_str(a.responsible_person),
        "last_inventory_date": a.last_inventory_date.isoformat() if a.last_inventory_date else None,
        "last_inventory_confirmed": a.last_inventory_confirmed,
    } for a in assets])


@router.post("/{check_id:int}/scan-qr")
async def scan_qr_for_inventory(
    check_id: int,
    inventory_number: str = Query(..., description="Инвентарный номер актива"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Сканирование QR-кода для быстрой отметки актива"""
    inv_check = db.query(InventoryCheck).filter(
        InventoryCheck.id == check_id,
        InventoryCheck.status == "in_progress"
    ).first()
    
    if not inv_check:
        raise HTTPException(status_code=404, detail="Инвентаризация не найдена или не активна")
    
    # Ищем актив по инвентарному номеру
    asset = db.query(Asset).filter(
        Asset.inventory_number == inventory_number,
        Asset.is_active == True
    ).first()
    
    if not asset:
        raise HTTPException(status_code=404, detail="Актив не найден")
    
    # Проверяем, есть ли актив в инвентаризации
    item = db.query(InventoryCheckItem).filter(
        InventoryCheckItem.inventory_check_id == check_id,
        InventoryCheckItem.asset_id == asset.id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Актив не включен в эту инвентаризацию")
    
    # Если уже подтвержден
    if item.result != "pending":
        return JSONResponse(content={
            "message": f"Актив уже отмечен как '{item.result}'",
            "result": item.result,
        })
    
    # Отмечаем как найденный
    item.result = "found"
    item.confirmed_by = current_user.id
    item.confirmed_at = datetime.now()
    
    inv_check.found += 1
    
    # Обновляем актив
    asset.last_inventory_date = datetime.now()
    asset.last_inventory_by_id = current_user.id
    asset.last_inventory_confirmed = True
    
    db.commit()
    
    return JSONResponse(content={
        "message": "Актив найден и отмечен",
        "asset_id": asset.id,
        "inventory_number": safe_str(asset.inventory_number),
        "asset_name": safe_str(asset.name),
        "result": "found",
        "found_count": inv_check.found,
        "missing_count": inv_check.missing,
        "remaining": inv_check.total_checked - inv_check.found - inv_check.missing,
    })
