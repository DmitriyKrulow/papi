# backend/src/presentation/http/routers/rfid.py
"""API для RFID-сканера — аутентификация, инвентаризация, поиск активов"""
import logging
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from src.infrastructure.db.init_db import get_db
from src.infrastructure.db.models.inventory_check import InventoryCheck
from src.infrastructure.db.models.inventory_check_item import InventoryCheckItem
from src.infrastructure.db.models.asset import Asset
from src.infrastructure.db.models.department import Department
from src.infrastructure.db.models.rfid_api_key import RfidApiKey
from src.presentation.http.dependencies.rfid_auth import get_rfid_scanner
from src.infrastructure.db.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rfid", tags=["rfid"])


# ======================================================================
# Аутентификация
# ======================================================================

@router.post("/auth/verify")
async def verify_scanner(
    scanner: dict = Depends(get_rfid_scanner),
    db: Session = Depends(get_db),
):
    """
    Проверка аутентификации RFID-сканера.
    Вызывается при запуске приложения для проверки ключа.
    
    Header: X-API-Key: rfid_abc123...
    """
    return {
        "authenticated": True,
        "scanner_id": scanner["id"],
        "scanner_name": scanner["name"],
        "message": f"Сканер '{scanner['name']}' авторизован"
    }


# ======================================================================
# Получение списка активных инвентаризаций
# ======================================================================

@router.get("/inventories")
async def get_active_inventories(
    scanner: dict = Depends(get_rfid_scanner),
    db: Session = Depends(get_db),
):
    """
    Получить список активных (in_progress) инвентаризаций для сканера.
    
    Header: X-API-Key: rfid_abc123...
    """
    inventories = db.query(InventoryCheck).options(
        joinedload(InventoryCheck.department),
        joinedload(InventoryCheck.creator),
        joinedload(InventoryCheck.responsible),
    ).filter(
        InventoryCheck.status == "in_progress"
    ).order_by(InventoryCheck.created_at.desc()).all()
    
    if not inventories:
        return {
            "inventories": [],
            "message": "Нет активных инвентаризаций"
        }
    
    result = []
    for inv in inventories:
        result.append({
            "id": inv.id,
            "name": inv.name,
            "check_date": inv.check_date.isoformat() if inv.check_date else None,
            "check_type": inv.check_type,
            "scope_id": inv.scope_id or 0,
            "scope_name": inv.scope_name or "",
            "department": inv.department.name if inv.department else "",
            "status": inv.status,
            "total_checked": inv.total_checked,
            "found": inv.found,
            "missing": inv.missing,
            "surplus": inv.surplus,
            "creator": inv.creator.full_name if inv.creator else "",
            "responsible": inv.responsible.full_name if inv.responsible else "",
            "started_at": inv.started_at.isoformat() if inv.started_at else None,
            "progress_percent": round(
                (inv.found + inv.missing) / inv.total_checked * 100, 1
            ) if inv.total_checked > 0 else 0,
        })
    
    return {
        "inventories": result,
        "count": len(result)
    }


# ======================================================================
# Получение списка активов для инвентаризации
# ======================================================================

@router.get("/inventories/{inventory_id}/assets")
async def get_inventory_assets(
    inventory_id: int,
    scanner: dict = Depends(get_rfid_scanner),
    db: Session = Depends(get_db),
):
    """
    Получить список активов, включённых в инвентаризацию.
    
    Header: X-API-Key: rfid_abc123...
    
    Возвращает:
    - id актива
    - инвентарный номер
    - название
    - статус подтверждения
    - rfid_tag (если привязан)
    """
    inv_check = db.query(InventoryCheck).filter(
        InventoryCheck.id == inventory_id,
        InventoryCheck.status == "in_progress"
    ).first()
    
    if not inv_check:
        raise HTTPException(
            status_code=404,
            detail="Инвентаризация не найдена или не активна"
        )
    
    # Получаем все активы инвентаризации
    items = db.query(InventoryCheckItem).options(
        joinedload(InventoryCheckItem.asset)
    ).filter(
        InventoryCheckItem.inventory_check_id == inventory_id
    ).all()
    
    assets = []
    for item in items:
        asset = item.asset
        if not asset:
            continue
        
        assets.append({
            "asset_id": asset.id,
            "inventory_number": asset.inventory_number or "",
            "name": asset.name or "",
            "model": asset.model or "",
            "location": asset.location_address or "",
            "responsible": asset.responsible_person or "",
            "department": asset.department_code or "",
            "rfid_tag": asset.rfid_tag or "",
            "check_status": item.result,  # pending / found / missing
            "confirmed_by": item.confirmed_by_user.full_name if item.confirmed_by_user else None,
            "confirmed_at": item.confirmed_at.isoformat() if item.confirmed_at else None,
        })
    
    # Сортируем: сначала pending, потом confirmed
    status_order = {"pending": 0, "found": 1, "missing": 1}
    assets.sort(key=lambda x: status_order.get(x["check_status"], 2))
    
    pending_count = sum(1 for a in assets if a["check_status"] == "pending")
    
    return {
        "inventory_id": inventory_id,
        "inventory_name": inv_check.name,
        "total": len(assets),
        "pending": pending_count,
        "confirmed": len(assets) - pending_count,
        "assets": assets
    }


# ======================================================================
# Поиск актива по RFID-метке
# ======================================================================

@router.get("/assets/by-rfid/{rfid_tag}")
async def get_asset_by_rfid(
    rfid_tag: str,
    scanner: dict = Depends(get_rfid_scanner),
    db: Session = Depends(get_db),
):
    """
    Поиск актива по RFID-метке.
    
    Header: X-API-Key: rfid_abc123...
    
    Возвращает полную информацию об активе.
    """
    asset = db.query(Asset).options(
        joinedload(Asset.assigned_employee),
        joinedload(Asset.assigned_room),
    ).filter(
        Asset.rfid_tag == rfid_tag,
        Asset.is_active == True
    ).first()
    
    if not asset:
        return {
            "found": False,
            "message": f"Актив с RFID-меткой '{rfid_tag}' не найден"
        }
    
    return {
        "found": True,
        "asset": {
            "id": asset.id,
            "inventory_number": asset.inventory_number or "",
            "name": asset.name or "",
            "description": asset.description or "",
            "model": asset.model or "",
            "asset_type": asset.asset_type or "",
            "status": asset.status,
            "location": asset.location_address or "",
            "room": asset.assigned_room.name if asset.assigned_room else "",
            "responsible": asset.responsible_person or "",
            "employee": f"{asset.assigned_employee.last_name} {asset.assigned_employee.first_name}" if asset.assigned_employee else "",
            "department": asset.department_code or "",
            "purchase_date": asset.purchase_date.isoformat() if asset.purchase_date else None,
            "purchase_price": str(asset.purchase_price) if asset.purchase_price else None,
            "current_value": str(asset.current_value) if asset.current_value else None,
            "serial_number": asset.serial_number or "",
            "rfid_tag": asset.rfid_tag or "",
            "last_inventory_date": asset.last_inventory_date.isoformat() if asset.last_inventory_date else None,
            "last_inventory_confirmed": asset.last_inventory_confirmed,
        }
    }


# ======================================================================
# Отправка результата сканирования RFID-метки
# ======================================================================

@router.post("/inventories/{inventory_id}/scan")
async def scan_rfid_for_inventory(
    inventory_id: int,
    request: Request,
    rfid_tag: Optional[str] = Query(None, description="RFID-метка сканированного актива"),
    result: str = Query("found", description="Результат: found / missing / surplus"),
    scanner: dict = Depends(get_rfid_scanner),
    db: Session = Depends(get_db),
):
    """
    Отправка результата сканирования RFID-метки.

    Метку можно передать query-параметром (?rfid_tag=xxx) или в JSON-теле
    ({"rfid_tag": "xxx", "result": "found"}).

    Логика:
    1. Ищем актив по RFID-метке
    2. Если актив есть в инвентаризации — проставляем result (found/missing)
    3. Если актива нет в инвентаризации — фиксируем как "surplus" (лишний)
    """
    # Метка может прийти из query или из JSON-тела
    if not rfid_tag:
        try:
            payload = await request.json()
        except Exception:
            payload = None
        if isinstance(payload, dict):
            rfid_tag = payload.get("rfid_tag") or payload.get("tag")
            result = payload.get("result") or result

    if not rfid_tag:
        raise HTTPException(status_code=400, detail="Не указана RFID-метка (rfid_tag)")

    result = (result or "found").lower()
    if result not in ("found", "missing", "surplus"):
        raise HTTPException(status_code=400, detail=f"Недопустимый результат: {result}")

    # Проверяем инвентаризацию
    inv_check = db.query(InventoryCheck).filter(
        InventoryCheck.id == inventory_id,
        InventoryCheck.status == "in_progress"
    ).first()
    
    if not inv_check:
        raise HTTPException(
            status_code=404,
            detail="Инвентаризация не найдена или не активна"
        )
    
    # Ищем актив по RFID
    asset = db.query(Asset).filter(
        Asset.rfid_tag == rfid_tag,
        Asset.is_active == True
    ).first()
    
    if not asset:
        return {
            "success": False,
            "message": f"Актив с RFID-меткой '{rfid_tag}' не найден в базе",
            "rfid_tag": rfid_tag,
            "inventory_id": inventory_id
        }

    # Проверяем, есть ли актив в инвентаризации
    item = db.query(InventoryCheckItem).filter(
        InventoryCheckItem.inventory_check_id == inventory_id,
        InventoryCheckItem.asset_id == asset.id
    ).first()

    # Актива нет в списке — фиксируем как лишний (surplus)
    if not item:
        item = InventoryCheckItem(
            inventory_check_id=inventory_id,
            asset_id=asset.id,
            result="surplus",
            comment="Найден при сканировании, не был в списке инвентаризации",
            confirmed_at=datetime.now(),
        )
        db.add(item)
        inv_check.surplus = (inv_check.surplus or 0) + 1
        inv_check.total_checked += 1
        asset.last_inventory_date = datetime.now()
        asset.last_inventory_confirmed = True
        asset.last_inventory_source = 'rfid'
        db.commit()

        return {
            "success": True,
            "message": "Актив не был в списке — зафиксирован как лишний (surplus)",
            "asset_id": asset.id,
            "inventory_number": asset.inventory_number,
            "asset_name": asset.name,
            "result": "surplus",
            "is_surplus": True,
            "inventory_id": inventory_id,
            "found_count": inv_check.found,
            "missing_count": inv_check.missing,
            "surplus_count": inv_check.surplus,
        }

    # Уже отмечен тем же результатом — ничего не делаем
    if item.result == result:
        return {
            "success": True,
            "message": f"Актив уже отмечен как '{item.result}'",
            "asset_id": asset.id,
            "inventory_number": asset.inventory_number,
            "asset_name": asset.name,
            "result": item.result,
            "already_marked": True,
            "inventory_id": inventory_id,
            "found_count": inv_check.found,
            "missing_count": inv_check.missing,
            "remaining": inv_check.total_checked - inv_check.found - inv_check.missing
        }

    # Снимаем предыдущий счётчик
    if item.result == "found":
        inv_check.found = max(0, inv_check.found - 1)
    elif item.result == "missing":
        inv_check.missing = max(0, inv_check.missing - 1)

    if result == "missing":
        item.result = "missing"
        inv_check.missing += 1
        asset_status = "отсутствует"
        confirmed_flag = False
    else:
        item.result = "found"
        inv_check.found += 1
        asset_status = "найден"
        confirmed_flag = True

    item.confirmed_by = None  # RFID-сканер не имеет user_id
    item.confirmed_at = datetime.now()

    # Обновляем актив
    asset.last_inventory_date = datetime.now()
    asset.last_inventory_confirmed = confirmed_flag
    asset.last_inventory_source = 'rfid'

    db.commit()
    
    return {
        "success": True,
        "message": f"Актив {asset_status} и отмечен",
        "asset_id": asset.id,
        "inventory_number": asset.inventory_number,
        "asset_name": asset.name,
        "location": asset.location_address or "",
        "responsible": asset.responsible_person or "",
        "rfid_tag": rfid_tag,
        "result": item.result,
        "inventory_id": inventory_id,
        "found_count": inv_check.found,
        "missing_count": inv_check.missing,
        "surplus_count": inv_check.surplus,
        "remaining": inv_check.total_checked - inv_check.found - inv_check.missing
    }


# ======================================================================
# Пакетная отправка результатов сканирования
# ======================================================================

@router.post("/inventories/{inventory_id}/scan-batch")
async def scan_rfid_batch(
    inventory_id: int,
    rfid_tags: List[str],
    scanner: dict = Depends(get_rfid_scanner),
    db: Session = Depends(get_db),
):
    """
    Пакетная отправка результатов сканирования.
    
    Header: X-API-Key: rfid_abc123...
    Body: {"rfid_tags": ["tag1", "tag2", "tag3"]}
    
    Позволяет отправить список всех отсканированных меток за раз.
    """
    inv_check = db.query(InventoryCheck).filter(
        InventoryCheck.id == inventory_id,
        InventoryCheck.status == "in_progress"
    ).first()
    
    if not inv_check:
        raise HTTPException(
            status_code=404,
            detail="Инвентаризация не найдена или не активна"
        )
    
    results = {
        "found": [],
        "not_found": [],
        "already_confirmed": []
    }
    
    for rfid_tag in rfid_tags:
        # Ищем актив
        asset = db.query(Asset).filter(
            Asset.rfid_tag == rfid_tag,
            Asset.is_active == True
        ).first()
        
        if not asset:
            results["not_found"].append({
                "rfid_tag": rfid_tag,
                "message": "Актив не найден"
            })
            continue
        
        # Проверяем в инвентаризации
        item = db.query(InventoryCheckItem).filter(
            InventoryCheckItem.inventory_check_id == inventory_id,
            InventoryCheckItem.asset_id == asset.id
        ).first()
        
        if not item:
            results["not_found"].append({
                "rfid_tag": rfid_tag,
                "asset_id": asset.id,
                "message": "Актив не в инвентаризации"
            })
            continue
        
        if item.result != "pending":
            results["already_confirmed"].append({
                "rfid_tag": rfid_tag,
                "asset_id": asset.id,
                "inventory_number": asset.inventory_number,
                "result": item.result
            })
            continue
        
        # Отмечаем found
        item.result = "found"
        item.confirmed_at = datetime.now()
        inv_check.found += 1
        asset.last_inventory_date = datetime.now()
        asset.last_inventory_confirmed = True
        asset.last_inventory_source = 'rfid'
        
        results["found"].append({
            "rfid_tag": rfid_tag,
            "asset_id": asset.id,
            "inventory_number": asset.inventory_number,
            "asset_name": asset.name
        })
    
    db.commit()
    
    return {
        "success": True,
        "inventory_id": inventory_id,
        "total_scanned": len(rfid_tags),
        "found": len(results["found"]),
        "not_found": len(results["not_found"]),
        "already_confirmed": len(results["already_confirmed"]),
        "details": results
    }


# ======================================================================
# Пассивное сканирование по помещению (ключевая фича!)
# ======================================================================

@router.post("/scan-room")
async def passive_room_scan(
    room_id: int = Query(..., description="ID помещения для сканирования"),
    rfid_tags: List[str] = Query(..., description="Список всех отсканированных RFID-меток в зоне"),
    scanner: dict = Depends(get_rfid_scanner),
    db: Session = Depends(get_db),
):
    """
    Пассивное сканирование помещения — ТСД проходит по помещению,
    RFID-ридер автоматически собирает ВСЕ метки в зоне.
    
    Система автоматически определяет:
    - Какие активы НАЙДЕНЫ в помещении
    - Какие активы ОТСУТСТВУЮТ (были в реестре помещения, но не отсканированы)
    
    Это КЛЮЧЕВОЕ отличие от ручного ввода — не нужно сканировать каждый актив отдельно.
    Просто проходите по помещению с ТСД.
    """
    # Проверяем помещение
    from src.infrastructure.db.models.department import Room
    room = db.query(Room).filter(Room.id == room_id, Room.is_active == True).first()
    
    if not room:
        raise HTTPException(status_code=404, detail="Помещение не найдено")
    
    # Находим все активы в этом помещении
    room_assets = db.query(Asset).filter(
        Asset.room_id == room_id,
        Asset.is_active == True,
        Asset.rfid_tag.isnot(None),  # Только активы с RFID-метками
    ).all()
    
    # Создаём словарь: rfid_tag -> asset
    known_tags = {a.rfid_tag: a for a in room_assets if a.rfid_tag}
    
    # Определяем найденные и отсутствующие
    found_assets = []
    missing_assets = []
    unknown_tags = []
    
    for tag in rfid_tags:
        if tag in known_tags:
            asset = known_tags[tag]
            found_assets.append({
                "asset_id": asset.id,
                "inventory_number": asset.inventory_number or "",
                "name": asset.name or "",
                "location": f"{room.name}" if room else "",
                "responsible": asset.responsible_person or "",
                "rfid_tag": tag,
            })
        else:
            unknown_tags.append(tag)
    
    # Активы, которые должны быть в помещении, но не отсканированы
    scanned_tags = set(rfid_tags)
    for tag, asset in known_tags.items():
        if tag not in scanned_tags:
            missing_assets.append({
                "asset_id": asset.id,
                "inventory_number": asset.inventory_number or "",
                "name": asset.name or "",
                "location": f"{room.name}" if room else "",
                "responsible": asset.responsible_person or "",
                "rfid_tag": tag,
                "reason": "Не отсканирован при обходе помещения",
            })
    
    return {
        "success": True,
        "room_id": room_id,
        "room_name": room.name,
        "building": room.building or "",
        "floor": room.floor or "",
        "total_known_assets": len(room_assets),
        "total_scanned": len(rfid_tags),
        "found": len(found_assets),
        "missing": len(missing_assets),
        "unknown_tags": len(unknown_tags),
        "found_assets": found_assets,
        "missing_assets": missing_assets,
        "unknown_tags_list": unknown_tags[:20],  # Не показываем больше 20
        "message": (
            f"Обход помещения '{room.name}': "
            f"найдено {len(found_assets)}, отсутствует {len(missing_assets)}, "
            f"неизвестных меток {len(unknown_tags)}"
        )
    }


# ======================================================================
# Создание и управление инвентаризациями через RFID-сканер
# ======================================================================

@router.post("/inventories")
async def create_inventory_for_scanner(
    room_id: int = Query(..., description="ID помещения"),
    room_name: str = Query(..., description="Название помещения"),
    scanner: dict = Depends(get_rfid_scanner),
    db: Session = Depends(get_db),
):
    """
    Создать инвентаризацию для помещения через RFID-сканер.
    Автоматически добавляет все активы помещения в проверку.
    
    Header: X-API-Key: rfid_abc123...
    """
    from src.infrastructure.db.models.department import Room
    from datetime import date
    
    room = db.query(Room).filter(Room.id == room_id, Room.is_active == True).first()
    if not room:
        raise HTTPException(status_code=404, detail="Помещение не найдено")
    
    # Проверяем, нет ли уже активной инвентаризации для этого помещения
    existing = db.query(InventoryCheck).filter(
        InventoryCheck.status == "in_progress",
        InventoryCheck.check_type == "by_room",
        InventoryCheck.scope_id == room_id
    ).first()
    
    if existing:
        return {
            "id": existing.id,
            "name": existing.name,
            "status": existing.status,
            "message": f"Инвентаризация уже создана: {existing.name}",
            "created": False
        }
    
    # Находим первого пользователя для created_by
    from src.infrastructure.db.models.user import User
    first_user = db.query(User).first()
    creator_id = first_user.id if first_user else 0
    
    # Создаём инвентаризацию
    inv_check = InventoryCheck(
        name=f"Инвентаризация: {room_name}",
        check_date=date.today(),
        check_type="by_room",
        scope_id=room_id,
        scope_name=room_name,
        status="in_progress",
        created_at=datetime.now(),
        started_at=datetime.now(),
        created_by=creator_id,
        responsible_id=creator_id,
    )
    db.add(inv_check)
    db.commit()  # Фиксируем инвентаризацию чтобы получить ID
    db.refresh(inv_check)
    
    # Добавляем все активы помещения
    from sqlalchemy import or_
    import re
    
    # Сначала ищем по room_id (более надёжно), затем по location_address
    room_assets = db.query(Asset).filter(
        Asset.is_active == True,
        Asset.room_id == room_id
    ).all()
    
    # Если по room_id ничего не найдено, ищем по location_address (старые данные)
    if not room_assets:
        room_name_pattern = re.escape(room_name)
        room_assets = db.query(Asset).filter(
            Asset.is_active == True,
            or_(
                Asset.location_address == room_name,
                Asset.location_address.like(f"%{room_name_pattern} -%"),
                Asset.location_address.like(f"%{room_name_pattern} ("),
            )
        ).all()
    
    assets = room_assets
    
    for a in assets:
        item = InventoryCheckItem(
            inventory_check_id=inv_check.id,
            asset_id=a.id,
            result="pending",
        )
        db.add(item)
        a.last_inventory_confirmed = False
        a.last_inventory_date = None
    
    inv_check.total_checked = len(assets)
    db.commit()
    db.refresh(inv_check)
    
    return {
        "id": inv_check.id,
        "name": inv_check.name,
        "status": inv_check.status,
        "total_checked": inv_check.total_checked,
        "found": inv_check.found,
        "missing": inv_check.missing,
        "message": f"Инвентаризация создана: {inv_check.total_checked} активов",
        "created": True
    }


# ======================================================================
# Пропуск непроверенных и пакетная синхронизация результатов
# ======================================================================

@router.post("/inventories/{inventory_id}/skip-all")
async def skip_all_pending(
    inventory_id: int,
    scanner: dict = Depends(get_rfid_scanner),
    db: Session = Depends(get_db),
):
    """Пометить все pending-элементы инвентаризации как отсутствующие."""
    inv_check = db.query(InventoryCheck).filter(
        InventoryCheck.id == inventory_id,
        InventoryCheck.status == "in_progress"
    ).first()

    if not inv_check:
        raise HTTPException(status_code=404, detail="Инвентаризация не найдена или не активна")

    pending_items = db.query(InventoryCheckItem).filter(
        InventoryCheckItem.inventory_check_id == inventory_id,
        InventoryCheckItem.result == "pending",
    ).all()

    for item in pending_items:
        item.result = "missing"
        item.comment = "Пропущено сканером"
        item.confirmed_at = datetime.now()

    inv_check.missing += len(pending_items)
    db.commit()

    return {
        "success": True,
        "inventory_id": inventory_id,
        "skipped": len(pending_items),
        "found": inv_check.found,
        "missing": inv_check.missing,
        "remaining": inv_check.total_checked - inv_check.found - inv_check.missing
    }


@router.post("/inventories/{inventory_id}/sync")
async def sync_scan_results(
    inventory_id: int,
    request: Request,
    scanner: dict = Depends(get_rfid_scanner),
    db: Session = Depends(get_db),
):
    """
    Пакетная синхронизация результатов сканирования с ТСД.

    Тело: [{"rfid_tag": "...", "result": "found"|"missing"|"surplus"}, ...]
    Позволяет дослать всё, что не удалось отправить в момент сканирования.
    """
    inv_check = db.query(InventoryCheck).filter(
        InventoryCheck.id == inventory_id,
        InventoryCheck.status == "in_progress"
    ).first()

    if not inv_check:
        raise HTTPException(status_code=404, detail="Инвентаризация не найдена или не активна")

    try:
        payload = await request.json()
    except Exception:
        payload = None

    if isinstance(payload, dict):
        payload = payload.get("results", [])
    if not isinstance(payload, list):
        raise HTTPException(status_code=400, detail="Ожидается JSON-массив результатов")

    stats = {"found": 0, "missing": 0, "surplus": 0, "already": 0, "unknown": 0}

    for entry in payload:
        if not isinstance(entry, dict):
            continue
        tag = entry.get("rfid_tag") or entry.get("tag")
        if not tag:
            continue

        res = (entry.get("result") or "found").lower()
        if res not in ("found", "missing", "surplus"):
            res = "found"

        asset = db.query(Asset).filter(
            Asset.rfid_tag == tag,
            Asset.is_active == True
        ).first()

        if not asset:
            stats["unknown"] += 1
            continue

        item = db.query(InventoryCheckItem).filter(
            InventoryCheckItem.inventory_check_id == inventory_id,
            InventoryCheckItem.asset_id == asset.id
        ).first()

        # Актив вне списка — лишняя находка
        if not item:
            db.add(InventoryCheckItem(
                inventory_check_id=inventory_id,
                asset_id=asset.id,
                result="surplus",
                comment="Найден при сканировании, не был в списке инвентаризации",
                confirmed_at=datetime.now(),
            ))
            inv_check.surplus = (inv_check.surplus or 0) + 1
            inv_check.total_checked += 1
            asset.last_inventory_date = datetime.now()
            asset.last_inventory_confirmed = True
            asset.last_inventory_source = 'rfid'
            stats["surplus"] += 1
            continue

        if item.result == res:
            stats["already"] += 1
            continue

        if item.result == "found":
            inv_check.found = max(0, inv_check.found - 1)
        elif item.result == "missing":
            inv_check.missing = max(0, inv_check.missing - 1)

        item.result = res
        item.confirmed_at = datetime.now()

        if res == "missing":
            inv_check.missing += 1
            asset.last_inventory_confirmed = False
            stats["missing"] += 1
        else:
            inv_check.found += 1
            asset.last_inventory_confirmed = True
            stats["found"] += 1

        asset.last_inventory_date = datetime.now()
        asset.last_inventory_source = 'rfid'

    db.commit()

    return {
        "success": True,
        "inventory_id": inventory_id,
        **stats,
        "found": inv_check.found,
        "missing": inv_check.missing,
        "surplus": inv_check.surplus,
    }


# ======================================================================
# Приёмка имущества через RFID
# ======================================================================

@router.post("/receive")
async def receive_assets_via_rfid(
    department_code: str = Query(..., description="Код подразделения-получателя"),
    responsible_person: str = Query(..., description="ФИО ответственного лица"),
    rfid_tags: List[str] = Query(..., description="Список RFID-меток принимаемых активов"),
    document_number: str = Query("", description="Номер приёмного документа"),
    scanner: dict = Depends(get_rfid_scanner),
    db: Session = Depends(get_db),
):
    """
    Приёмка имущества через RFID-сканирование.
    
    При приёмке:
    1. Сканируете все RFID-метки новой техники/оборудования
    2. Система автоматически находит активы по меткам
    3. Привязывает их к подразделению и ответственному лицу
    4. Фиксирует приём в журнале
    """
    results = {
        "received": [],
        "not_found": [],
        "already_assigned": []
    }
    
    for rfid_tag in rfid_tags:
        asset = db.query(Asset).filter(
            Asset.rfid_tag == rfid_tag,
            Asset.is_active == True
        ).first()
        
        if not asset:
            results["not_found"].append({
                "rfid_tag": rfid_tag,
                "message": "Актив не найден в базе"
            })
            continue
        
        # Проверяем, не присвоен ли уже
        if asset.department_code and asset.department_code != department_code:
            results["already_assigned"].append({
                "rfid_tag": rfid_tag,
                "asset_id": asset.id,
                "current_department": asset.department_code,
                "message": "Актив уже закреплён за другим подразделением"
            })
            continue
        
        # Принимаем актив
        old_department = asset.department_code
        asset.department_code = department_code
        asset.responsible_person = responsible_person
        asset.status = "active"
        
        results["received"].append({
            "rfid_tag": rfid_tag,
            "asset_id": asset.id,
            "inventory_number": asset.inventory_number,
            "name": asset.name,
            "old_department": old_department or "(не присвоен)",
            "new_department": department_code,
            "new_responsible": responsible_person,
        })
    
    db.commit()
    
    return {
        "success": True,
        "document_number": document_number,
        "department_code": department_code,
        "responsible_person": responsible_person,
        "total_scanned": len(rfid_tags),
        "received": len(results["received"]),
        "not_found": len(results["not_found"]),
        "already_assigned": len(results["already_assigned"]),
        "details": results
    }


# ======================================================================
# Перемещение между помещениями через RFID
# ======================================================================

@router.post("/move")
async def move_assets_via_rfid(
    from_room_id: int = Query(..., description="ID помещения-отправителя"),
    to_room_id: int = Query(..., description="ID помещения-получателя"),
    rfid_tags: List[str] = Query(..., description="Список RFID-меток перемещаемых активов"),
    reason: str = Query("", description="Причина перемещения"),
    document_number: str = Query("", description="Номер документа перемещения"),
    scanner: dict = Depends(get_rfid_scanner),
    db: Session = Depends(get_db),
):
    """
    Перемещение имущества между помещениями через RFID.
    
    При перемещении:
    1. Сканируете метки в исходном помещении
    2. Указываете целевое помещение
    3. Система обновляет location и фиксирует перемещение
    """
    from src.infrastructure.db.models.department import Room
    from datetime import datetime
    
    from_room = db.query(Room).filter(Room.id == from_room_id).first()
    to_room = db.query(Room).filter(Room.id == to_room_id).first()
    
    if not from_room or not to_room:
        raise HTTPException(status_code=404, detail="Помещение не найдено")
    
    results = {
        "moved": [],
        "not_found": [],
        "not_in_source_room": []
    }
    
    for rfid_tag in rfid_tags:
        asset = db.query(Asset).filter(
            Asset.rfid_tag == rfid_tag,
            Asset.is_active == True
        ).first()
        
        if not asset:
            results["not_found"].append({
                "rfid_tag": rfid_tag,
                "message": "Актив не найден"
            })
            continue
        
        # Проверяем, что актив в исходном помещении
        if asset.room_id != from_room_id:
            results["not_in_source_room"].append({
                "rfid_tag": rfid_tag,
                "asset_id": asset.id,
                "current_room_id": asset.room_id,
                "message": f"Актив находится в другом помещении (ID: {asset.room_id})"
            })
            continue
        
        # Перемещаем
        old_room_id = asset.room_id
        old_room_name = from_room.name
        asset.room_id = to_room_id
        asset.location_address = to_room.name
        
        # Создаём запись о перемещении
        from src.infrastructure.db.models.movement_record import MovementRecord
        movement = MovementRecord(
            asset_id=asset.id,
            movement_date=datetime.now(),
            from_department_id=from_room.department_id,
            from_department_name=from_room.name,
            from_location=old_room_name,
            to_department_id=to_room.department_id,
            to_department_name=to_room.name,
            to_location=to_room.name,
            reason=reason,
            document_number=document_number,
        )
        db.add(movement)
        
        results["moved"].append({
            "rfid_tag": rfid_tag,
            "asset_id": asset.id,
            "inventory_number": asset.inventory_number,
            "name": asset.name,
            "from_room": old_room_name,
            "to_room": to_room.name,
        })
    
    db.commit()
    
    return {
        "success": True,
        "from_room": from_room.name,
        "to_room": to_room.name,
        "total_scanned": len(rfid_tags),
        "moved": len(results["moved"]),
        "not_found": len(results["not_found"]),
        "not_in_source_room": len(results["not_in_source_room"]),
        "details": results
    }


# ======================================================================
# Статус инвентаризации
# ======================================================================

@router.get("/inventories/{inventory_id}/status")
async def get_inventory_status(
    inventory_id: int,
    scanner: dict = Depends(get_rfid_scanner),
    db: Session = Depends(get_db),
):
    """
    Получить текущий статус инвентаризации.
    
    Header: X-API-Key: rfid_abc123...
    """
    inv_check = db.query(InventoryCheck).filter(
        InventoryCheck.id == inventory_id
    ).first()
    
    if not inv_check:
        raise HTTPException(
            status_code=404,
            detail="Инвентаризация не найдена"
        )
    
    pending = db.query(InventoryCheckItem).filter(
        InventoryCheckItem.inventory_check_id == inventory_id,
        InventoryCheckItem.result == "pending"
    ).count()
    
    return {
        "inventory_id": inventory_id,
        "name": inv_check.name,
        "status": inv_check.status,
        "total_checked": inv_check.total_checked,
        "found": inv_check.found,
        "missing": inv_check.missing,
        "pending": pending,
        "progress_percent": round(
            (inv_check.found + inv_check.missing) / inv_check.total_checked * 100, 1
        ) if inv_check.total_checked > 0 else 0
    }


# ======================================================================
# Завершение инвентаризации через RFID-сканер
# ======================================================================

@router.post("/inventories/{inventory_id}/finish")
async def finish_inventory_check(
    inventory_id: int,
    skip_pending: bool = Query(True, description="Пометить непроверенные активы как пропущенные"),
    scanner: dict = Depends(get_rfid_scanner),
    db: Session = Depends(get_db),
):
    """
    Завершить инвентаризацию через RFID-сканер.

    При завершении:
    1. Непроверенные активы помечаются как "missing" (если skip_pending=true)
    2. Счётчики пересчитываются из элементов
    3. У активов проставляются last_inventory_date / last_inventory_confirmed
    4. Статус инвентаризации меняется на "completed"
    """
    inv_check = db.query(InventoryCheck).filter(
        InventoryCheck.id == inventory_id
    ).first()

    if not inv_check:
        raise HTTPException(status_code=404, detail="Инвентаризация не найдена")

    # Идемпотентность: если уже завершена — возвращаем сводку без ошибки
    if inv_check.status == "completed":
        counts = (
            db.query(InventoryCheckItem.result, func.count(InventoryCheckItem.id))
            .filter(InventoryCheckItem.inventory_check_id == inventory_id)
            .group_by(InventoryCheckItem.result)
            .all()
        )
        return {
            "success": True,
            "inventory_id": inv_check.id,
            "name": inv_check.name,
            "status": "completed",
            "already_completed": True,
            "completed_at": inv_check.completed_at.isoformat() if inv_check.completed_at else None,
        }

    if inv_check.status == "cancelled":
        raise HTTPException(status_code=400, detail="Нельзя завершить отменённую инвентаризацию")

    skipped_count = 0
    if skip_pending:
        pending_items = db.query(InventoryCheckItem).filter(
            InventoryCheckItem.inventory_check_id == inventory_id,
            InventoryCheckItem.result == "pending",
        ).all()

        for item in pending_items:
            item.result = "missing"
            item.comment = "Пропущено при завершении инвентаризации"
            item.confirmed_at = datetime.now()
            skipped_count += 1

    # Пересчёт счётчиков из элементов (надёжнее, чем накопление в переменной)
    counts = (
        db.query(InventoryCheckItem.result, func.count(InventoryCheckItem.id))
        .filter(InventoryCheckItem.inventory_check_id == inventory_id)
        .group_by(InventoryCheckItem.result)
        .all()
    )
    for result_type, cnt in counts:
        if result_type == "found":
            inv_check.found = cnt
        elif result_type == "missing":
            inv_check.missing = cnt
        elif result_type == "surplus":
            inv_check.surplus = cnt

    # Обновляем активы: проставляем дату проверки и флаг подтверждения
    items = (
        db.query(InventoryCheckItem)
        .options(joinedload(InventoryCheckItem.asset))
        .filter(InventoryCheckItem.inventory_check_id == inventory_id)
        .all()
    )
    updated_count = 0
    for item in items:
        if item.asset:
            item.asset.last_inventory_date = datetime.now()
            item.asset.last_inventory_confirmed = item.result == "found"
            item.asset.last_inventory_source = 'rfid'
            updated_count += 1
    logger.info(f"[finish_inventory_check] Updated last_inventory_date for {updated_count} assets in inventory {inventory_id}")

    inv_check.status = "completed"
    inv_check.completed_at = datetime.now()
    db.commit()

    # Запись в системный аудит
    try:
        from src.core.services.audit_service import AuditService
        audit_service = AuditService(db)
        audit_service.log_inventory_complete(
            inv_check.id,
            inv_check.name,
            user_id=inv_check.responsible_id or inv_check.created_by,
        )
    except Exception as e:
        logger.warning(f"Failed to log inventory completion to audit: {e}")

    return {
        "success": True,
        "inventory_id": inv_check.id,
        "name": inv_check.name,
        "status": inv_check.status,
        "total_checked": inv_check.total_checked,
        "found": inv_check.found,
        "missing": inv_check.missing,
        "surplus": inv_check.surplus,
        "skipped": skipped_count,
        "completed_at": inv_check.completed_at.isoformat() if inv_check.completed_at else None,
        "message": (
            f"Инвентаризация завершена. "
            f"Найдено: {inv_check.found}, "
            f"Отсутствует: {inv_check.missing}"
            + (f" (пропущено: {skipped_count})" if skipped_count > 0 else "")
        )
    }


# ======================================================================
# Помещения и активы для RFID-сканера (отдельные эндпоинты с API Key auth)
# ======================================================================

@router.get("/rooms")
async def get_rooms_for_scanner(
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    scanner: dict = Depends(get_rfid_scanner),
):
    """
    Получить список помещений для RFID-сканера.
    Использует X-API-Key аутентификацию вместо admin Bearer token.
    
    Header: X-API-Key: rfid_abc123...
    Query: search=текст
    """
    from src.infrastructure.db.models.department import Room, Department
    
    query = db.query(Room).options(
        joinedload(Room.department)
    ).filter(
        Room.is_active == True
    )
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Room.name.ilike(search_pattern)) |
            (Room.floor.ilike(search_pattern)) |
            (Room.building.ilike(search_pattern))
        )
    
    rooms = query.order_by(Room.name).all()
    
    return {
        "rooms": [
            {
                "id": r.id,
                "name": r.name or "",
                "building": r.building or "",
                "floor": r.floor or "",
                "department": r.department.name if r.department else "",
            }
            for r in rooms
        ],
        "count": len(rooms)
    }


@router.get("/rooms/{room_id}/assets")
async def get_room_assets_for_scanner(
    room_id: int,
    db: Session = Depends(get_db),
    scanner: dict = Depends(get_rfid_scanner),
):
    """
    Получить список активов для помещения.
    Использует X-API-Key аутентификацию вместо admin Bearer token.
    
    Header: X-API-Key: rfid_abc123...
    """
    from src.infrastructure.db.models.department import Room
    
    room = db.query(Room).filter(Room.id == room_id, Room.is_active == True).first()
    if not room:
        raise HTTPException(status_code=404, detail="Помещение не найдено")
    
    assets = db.query(Asset).options(
        joinedload(Asset.assigned_room)
    ).filter(
        Asset.room_id == room_id,
        Asset.is_active == True
    ).all()
    
    return {
        "room_id": room_id,
        "room_name": room.name,
        "total": len(assets),
        "assets": [
            {
                "id": a.id,
                "rfid_tag": a.rfid_tag or "",
                "inventory_number": a.inventory_number or "",
                "name": a.name or "",
                "model": a.model or "",
                "serial_number": a.serial_number or "",
                "department": a.department_code or "",
                "responsible": a.responsible_person or "",
                "location": a.location_address or "",
                "status": a.status,
            }
            for a in assets
        ]
    }
