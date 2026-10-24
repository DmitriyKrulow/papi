# backend/src/presentation/http/routers/storage_addresses.py
"""Адресное хранение — управление стеллажами, полками, ячейками и складскими локациями"""
import logging
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from src.infrastructure.db.init_db import get_db
from src.infrastructure.db.models.storage_address import StorageAddress
from src.infrastructure.db.models.warehouse_location import WarehouseLocation
from src.infrastructure.db.models.asset import Asset
from src.infrastructure.db.models.user import User
from src.presentation.http.dependencies.auth import get_current_user, get_current_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/storage-addresses", tags=["storage-addresses"])


@router.get("/tree")
async def get_address_tree(
    level: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Дерево адресов хранения"""
    query = db.query(StorageAddress).filter(StorageAddress.is_active == True)
    if level:
        query = query.filter(StorageAddress.level == level)
    all_addresses = query.all()
    by_level = {}
    for addr in all_addresses:
        if addr.level not in by_level:
            by_level[addr.level] = []
        by_level[addr.level].append({
            "id": addr.id, "name": addr.name,
            "code": addr.code or "", "level": addr.level,
            "parent_id": addr.parent_id,
            "current_count": addr.current_count,
            "capacity": addr.capacity,
        })
    def build_tree(parent_id=None, lvl=None):
        children = []
        for item in by_level.get(lvl, []):
            if item.get("parent_id") == parent_id:
                node = {
                    "id": item["id"], "name": item["name"],
                    "code": item["code"], "level": item["level"],
                    "current_count": item["current_count"],
                    "capacity": item["capacity"],
                    "children": build_tree(item["id"], item["level"]),
                }
                children.append(node)
        return children
    return {"tree": build_tree(None, "building"), "by_level": by_level}


@router.post("")
async def create_address(
    name: str = Query(...),
    level: str = Query(...),
    parent_id: Optional[int] = None,
    code: Optional[str] = None,
    capacity: Optional[int] = None,
    description: str = "",
    room_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Создать адрес хранения"""
    parent = None
    if parent_id:
        parent = db.query(StorageAddress).filter(StorageAddress.id == parent_id).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Родитель не найден")
    if code:
        existing = db.query(StorageAddress).filter(StorageAddress.code == code).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Код '{code}' уже существует")
    new_address = StorageAddress(
        parent_id=parent_id, level=level, name=name,
        code=code, capacity=capacity, description=description, room_id=room_id,
    )
    db.add(new_address)
    db.commit()
    db.refresh(new_address)
    return {
        "success": True, "id": new_address.id,
        "name": new_address.name, "level": new_address.level,
        "full_address": new_address.get_full_address(),
        "code": new_address.code,
    }


@router.get("/{address_id}")
async def get_address_details(
    address_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Детали адреса и активы в нём"""
    address = db.query(StorageAddress).filter(StorageAddress.id == address_id).first()
    if not address:
        raise HTTPException(status_code=404, detail="Адрес не найден")
    assets = db.query(Asset).filter(
        Asset.storage_address_id == address_id, Asset.is_active == True
    ).all()
    children = db.query(StorageAddress).filter(
        StorageAddress.parent_id == address_id, StorageAddress.is_active == True
    ).all()
    return {
        "id": address.id, "name": address.name,
        "code": address.code or "", "level": address.level,
        "full_address": address.get_full_address(),
        "description": address.description or "",
        "capacity": address.capacity,
        "current_count": address.current_count,
        "children": [
            {"id": c.id, "name": c.name, "code": c.code or "",
             "level": c.level, "current_count": c.current_count}
            for c in children
        ],
        "assets": [
            {"id": a.id, "inventory_number": a.inventory_number or "",
             "name": a.name or "", "model": a.model or "",
             "rfid_tag": a.rfid_tag or "",
             "responsible_person": a.responsible_person or ""}
            for a in assets
        ],
    }


@router.get("/{address_id}/assets")
async def get_address_assets(
    address_id: int,
    include_children: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Активы в адресе (опционально рекурсивно)"""
    address = db.query(StorageAddress).filter(StorageAddress.id == address_id).first()
    if not address:
        raise HTTPException(status_code=404, detail="Адрес не найден")
    assets = []
    if not include_children:
        assets = db.query(Asset).filter(
            Asset.storage_address_id == address_id, Asset.is_active == True
        ).all()
    else:
        all_ids = [address_id]
        queue = [address_id]
        while queue:
            current = queue.pop(0)
            children = db.query(StorageAddress).filter(
                StorageAddress.parent_id == current, StorageAddress.is_active == True
            ).all()
            for child in children:
                all_ids.append(child.id)
                queue.append(child.id)
        assets = db.query(Asset).filter(
            Asset.storage_address_id.in_(all_ids), Asset.is_active == True
        ).all()
    return {
        "address_id": address.id, "address_name": address.name,
        "full_address": address.get_full_address(),
        "include_children": include_children,
        "total_assets": len(assets),
        "assets": [
            {"id": a.id, "inventory_number": a.inventory_number or "",
             "name": a.name or "", "model": a.model or "",
             "rfid_tag": a.rfid_tag or "",
             "responsible_person": a.responsible_person or ""}
            for a in assets
        ],
    }


@router.post("/{address_id}/move")
async def move_asset_to_address(
    address_id: int,
    asset_ids: List[int] = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Переместить активы в адрес хранения"""
    address = db.query(StorageAddress).filter(StorageAddress.id == address_id).first()
    if not address:
        raise HTTPException(status_code=404, detail="Адрес не найден")
    results = {"moved": [], "not_found": [], "already_here": []}
    for asset_id in asset_ids:
        asset = db.query(Asset).filter(
            Asset.id == asset_id, Asset.is_active == True
        ).first()
        if not asset:
            results["not_found"].append({"asset_id": asset_id})
            continue
        if asset.storage_address_id == address_id:
            results["already_here"].append({
                "asset_id": asset_id,
                "inventory_number": asset.inventory_number,
            })
            continue
        asset.storage_address_id = address_id
        results["moved"].append({
            "asset_id": asset_id,
            "inventory_number": asset.inventory_number,
            "name": asset.name,
            "new_address": address.get_full_address(),
        })
    db.commit()
    return {
        "success": True, "address": address.get_full_address(),
        "total": len(asset_ids),
        "moved": len(results["moved"]),
        "not_found": len(results["not_found"]),
        "already_here": len(results["already_here"]),
        "details": results,
    }


@router.get("/search/by-code/{code}")
async def search_by_code(
    code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Поиск адреса по коду (для сканирования QR-кода адреса)"""
    address = db.query(StorageAddress).filter(StorageAddress.code == code).first()
    if not address:
        return {"found": False, "message": f"Адрес с кодом '{code}' не найден"}
    assets = db.query(Asset).filter(
        Asset.storage_address_id == address.id, Asset.is_active == True
    ).all()
    return {
        "found": True,
        "address": {
            "id": address.id, "name": address.name,
            "code": address.code or "", "level": address.level,
            "full_address": address.get_full_address(),
            "current_count": address.current_count,
            "capacity": address.capacity,
        },
        "assets_count": len(assets),
        "assets": [
            {"id": a.id, "inventory_number": a.inventory_number or "",
             "name": a.name or "", "rfid_tag": a.rfid_tag or ""}
            for a in assets
        ],
    }


@router.get("/stats")
async def get_storage_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Статистика адресного хранения"""
    total_addresses = db.query(StorageAddress).filter(
        StorageAddress.is_active == True
    ).count()
    by_level = {}
    for level in ["building", "floor", "zone", "aisle", "shelf", "cell"]:
        by_level[level] = db.query(StorageAddress).filter(
            StorageAddress.level == level, StorageAddress.is_active == True
        ).count()
    total_with = db.query(Asset).filter(
        Asset.is_active == True, Asset.storage_address_id.isnot(None)
    ).count()
    total_without = db.query(Asset).filter(
        Asset.is_active == True, Asset.storage_address_id.is_(None)
    ).count()
    return {
        "total_addresses": total_addresses,
        "by_level": by_level,
        "total_assets_with_address": total_with,
        "total_assets_without_address": total_without,
        "address_coverage_percent": round(
            total_with / (total_with + total_without) * 100, 1
        ) if (total_with + total_without) > 0 else 0,
    }


# ======================================================================
# Складские помещения
# ======================================================================

@router.get("/rooms")
async def get_warehouse_rooms(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Список всех складских помещений (room_type='warehouse')"""
    from src.infrastructure.db.models.department import Room as RoomModel
    
    rooms = db.query(RoomModel).filter(
        RoomModel.room_type == "warehouse",
        RoomModel.is_active == True,
    ).order_by(RoomModel.name).all()
    
    return [
        {
            "id": r.id,
            "name": r.name,
            "department_id": r.department_id,
            "department_name": r.department.name if r.department else "",
            "floor": r.floor,
            "building": r.building,
            "room_type": r.room_type,
        }
        for r in rooms
    ]


@router.get("/rooms/{room_id}/tree")
async def get_room_location_tree(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Дерево локаций (storage_addresses) для конкретного склада"""
    from src.infrastructure.db.models.department import Room as RoomModel
    
    room = db.query(RoomModel).filter(
        RoomModel.id == room_id,
        RoomModel.room_type == "warehouse",
    ).first()
    if not room:
        raise HTTPException(status_code=404, detail="Складское помещение не найдено")
    
    # Получаем все адреса хранения для этого склада
    addresses = db.query(StorageAddress).filter(
        StorageAddress.room_id == room_id,
        StorageAddress.is_active == True,
    ).order_by(StorageAddress.level, StorageAddress.name).all()
    
    # Группируем по уровням
    by_level = {}
    for addr in addresses:
        if addr.level not in by_level:
            by_level[addr.level] = []
        by_level[addr.level].append({
            "id": addr.id,
            "name": addr.name,
            "code": addr.code or "",
            "level": addr.level,
            "parent_id": addr.parent_id,
            "capacity": addr.capacity,
            "current_count": addr.current_count,
        })
    
    # Строим дерево
    def build_tree(parent_id=None, lvl=None):
        children = []
        for item in by_level.get(lvl, []):
            if item.get("parent_id") == parent_id:
                node = {
                    "id": item["id"],
                    "name": item["name"],
                    "code": item["code"],
                    "level": item["level"],
                    "capacity": item["capacity"],
                    "current_count": item["current_count"],
                    "children": build_tree(item["id"], item["level"]),
                }
                children.append(node)
        return children
    
    return {
        "room_id": room.id,
        "room_name": room.name,
        "tree": build_tree(None, "building"),
        "by_level": by_level,
    }


@router.get("/rooms/{room_id}/assets")
async def get_room_assets(
    room_id: int,
    storage_address_id: Optional[int] = Query(None, description="ID локации для фильтрации"),
    search: Optional[str] = Query(None, description="Поиск по названию/инв. номеру"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Активы склада, с фильтрацией по локации и поиском"""
    from src.infrastructure.db.models.department import Room as RoomModel
    
    room = db.query(RoomModel).filter(
        RoomModel.id == room_id,
        RoomModel.room_type == "warehouse",
    ).first()
    if not room:
        raise HTTPException(status_code=404, detail="Складское помещение не найдено")
    
    # Получаем все storage_addresses этого склада
    room_address_ids = [
        sa.id for sa in db.query(StorageAddress.id).filter(
            StorageAddress.room_id == room_id,
            StorageAddress.is_active == True,
        ).all()
    ]
    
    if storage_address_id:
        # Получаем все дочерние локации от указанной
        all_ids = [storage_address_id]
        queue = [storage_address_id]
        while queue:
            current = queue.pop(0)
            children = db.query(StorageAddress).filter(
                StorageAddress.parent_id == current,
                StorageAddress.is_active == True,
            ).all()
            for child in children:
                all_ids.append(child.id)
                queue.append(child.id)
        
        # Фильтруем: только локации, принадлежащие этому складу
        all_ids = [aid for aid in all_ids if aid in room_address_ids]
        
        query = db.query(Asset).filter(
            Asset.is_active == True,
            Asset.storage_address_id.in_(all_ids),
        )
    else:
        # Все активы со склада (привязанные к любым локациям этого склада)
        query = db.query(Asset).filter(
            Asset.is_active == True,
            Asset.storage_address_id.in_(room_address_ids) if room_address_ids else False,
        )
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Asset.name.ilike(search_pattern),
                Asset.inventory_number.ilike(search_pattern),
                Asset.responsible_person.ilike(search_pattern),
            )
        )
    
    assets = query.order_by(Asset.inventory_number).all()
    
    return {
        "room_id": room.id,
        "room_name": room.name,
        "storage_address_id": storage_address_id,
        "total_assets": len(assets),
        "assets": [
            {
                "id": a.id,
                "inventory_number": a.inventory_number or "",
                "name": a.name or "",
                "model": a.model or "",
                "responsible_person": a.responsible_person or "",
                "storage_address_id": a.storage_address_id,
                "storage_address_name": a.storage_address.name if a.storage_address else "",
                "full_address": a.storage_address.get_full_address() if a.storage_address else "",
            }
            for a in assets
        ],
    }


# ======================================================================
# Дополнительные endpoints для управления складами
# ======================================================================

@router.get("/rooms/{room_id}/stats")
async def get_warehouse_stats(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Статистика склада: заполненность, количество активов по уровням"""
    from src.infrastructure.db.models.department import Room as RoomModel
    
    room = db.query(RoomModel).filter(
        RoomModel.id == room_id,
        RoomModel.room_type == "warehouse",
    ).first()
    if not room:
        raise HTTPException(status_code=404, detail="Складское помещение не найдено")
    
    # Все локации склада
    addresses = db.query(StorageAddress).filter(
        StorageAddress.room_id == room_id,
        StorageAddress.is_active == True,
    ).all()
    
    # Активы по уровням
    by_level = {}
    for level in ["building", "floor", "zone", "aisle", "shelf", "cell"]:
        level_addresses = [a for a in addresses if a.level == level]
        level_ids = [a.id for a in level_addresses]
        
        if level_ids:
            assets_in_level = db.query(Asset).filter(
                Asset.is_active == True,
                Asset.storage_address_id.in_(level_ids),
            ).count()
        else:
            assets_in_level = 0
        
        total_capacity = sum(a.capacity or 0 for a in level_addresses)
        
        by_level[level] = {
            "count": len(level_addresses),
            "assets": assets_in_level,
            "capacity": total_capacity,
        }
    
    # Итого
    all_address_ids = [a.id for a in addresses]
    total_assets = 0
    if all_address_ids:
        total_assets = db.query(Asset).filter(
            Asset.is_active == True,
            Asset.storage_address_id.in_(all_address_ids),
        ).count()
    
    return {
        "room_id": room.id,
        "room_name": room.name,
        "total_locations": len(addresses),
        "total_assets": total_assets,
        "by_level": by_level,
    }


@router.get("/assets/{asset_id}/location")
async def get_asset_location(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить полный путь локации для актива"""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Актив не найден")
    
    if not asset.storage_address_id:
        return {
            "asset_id": asset.id,
            "inventory_number": asset.inventory_number or "",
            "name": asset.name or "",
            "has_location": False,
            "location": None,
        }
    
    storage_addr = db.query(StorageAddress).filter(
        StorageAddress.id == asset.storage_address_id
    ).first()
    
    if not storage_addr:
        return {
            "asset_id": asset.id,
            "inventory_number": asset.inventory_number or "",
            "name": asset.name or "",
            "has_location": False,
            "location": None,
        }
    
    return {
        "asset_id": asset.id,
        "inventory_number": asset.inventory_number or "",
        "name": asset.name or "",
        "has_location": True,
        "location": {
            "id": storage_addr.id,
            "name": storage_addr.name,
            "level": storage_addr.level,
            "full_address": storage_addr.get_full_address(),
            "code": storage_addr.code or "",
            "room_id": storage_addr.room_id,
            "room_name": storage_addr.room.name if storage_addr.room else "",
        },
    }


@router.get("/search/by-location")
async def search_by_location(
    location_id: int = Query(..., description="ID локации (storage_address)"),
    recursive: bool = Query(True, description="Рекурсивный поиск по дочерним локациям"),
    search: Optional[str] = Query(None, description="Доп. поиск по названию/инв. номеру"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Поиск активов по локации склада.
    
    Если recursive=True — ищет активы во всех дочерних локациях.
    """
    location = db.query(StorageAddress).filter(
        StorageAddress.id == location_id,
        StorageAddress.is_active == True,
    ).first()
    if not location:
        raise HTTPException(status_code=404, detail="Локация не найдена")
    
    # Получаем все ID локаций для поиска
    if recursive:
        all_ids = [location_id]
        queue = [location_id]
        while queue:
            current = queue.pop(0)
            children = db.query(StorageAddress).filter(
                StorageAddress.parent_id == current,
                StorageAddress.is_active == True,
            ).all()
            for child in children:
                all_ids.append(child.id)
                queue.append(child.id)
    else:
        all_ids = [location_id]
    
    query = db.query(Asset).filter(
        Asset.is_active == True,
        Asset.storage_address_id.in_(all_ids),
    )
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Asset.name.ilike(search_pattern),
                Asset.inventory_number.ilike(search_pattern),
                Asset.responsible_person.ilike(search_pattern),
            )
        )
    
    assets = query.order_by(Asset.inventory_number).all()
    
    return {
        "location_id": location.id,
        "location_name": location.name,
        "location_level": location.level,
        "full_address": location.get_full_address(),
        "recursive": recursive,
        "total_assets": len(assets),
        "assets": [
            {
                "id": a.id,
                "inventory_number": a.inventory_number or "",
                "name": a.name or "",
                "model": a.model or "",
                "responsible_person": a.responsible_person or "",
                "rfid_tag": a.rfid_tag or "",
                "storage_address_id": a.storage_address_id,
                "storage_address_name": a.storage_address.name if a.storage_address else "",
                "full_address": a.storage_address.get_full_address() if a.storage_address else "",
            }
            for a in assets
        ],
    }

# ======================================================================
# Складские локации (WarehouseLocation) — CRUD
# ======================================================================

@router.get("/warehouse-locations")
async def get_warehouse_locations(
    room_id: Optional[int] = Query(None, description="ID складского помещения"),
    location_type: Optional[str] = Query(None, description="Тип локации: receiving, storage, shipping, returns, quarantine"),
    search: Optional[str] = Query(None, description="Поиск по названию/коду"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Список складских локаций с фильтрацией"""
    query = db.query(WarehouseLocation).filter(
        WarehouseLocation.is_active == True,
    )
    if room_id:
        query = query.filter(WarehouseLocation.room_id == room_id)
    if location_type:
        query = query.filter(WarehouseLocation.location_type == location_type)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                WarehouseLocation.name.ilike(search_pattern),
                WarehouseLocation.code.ilike(search_pattern),
                WarehouseLocation.description.ilike(search_pattern),
            )
        )
    locations = query.order_by(WarehouseLocation.room_id, WarehouseLocation.name).all()
    return {
        "total": len(locations),
        "locations": [
            {
                "id": loc.id, "name": loc.name, "code": loc.code or "",
                "location_type": loc.location_type, "description": loc.description or "",
                "room_id": loc.room_id, "room_name": loc.room.name if loc.room else "",
                "capacity": loc.capacity, "current_count": loc.current_count,
                "storage_addresses_count": len(loc.storage_addresses) if loc.storage_addresses else 0,
            }
            for loc in locations
        ],
    }


@router.get("/warehouse-locations/{location_id}")
async def get_warehouse_location_details(
    location_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Детали складской локации: стеллажи, полки, активы"""
    location = db.query(WarehouseLocation).filter(WarehouseLocation.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Складская локация не найдена")
    addresses = db.query(StorageAddress).filter(
        StorageAddress.warehouse_location_id == location_id, StorageAddress.is_active == True,
    ).all()
    direct_assets = db.query(Asset).filter(
        Asset.warehouse_location_id == location_id, Asset.is_active == True,
    ).all()
    sa_ids = [sa.id for sa in addresses]
    child_assets = []
    if sa_ids:
        child_assets = db.query(Asset).filter(
            Asset.storage_address_id.in_(sa_ids), Asset.is_active == True,
        ).all()
    all_assets = direct_assets + child_assets
    by_level = {}
    for level in ["rack", "shelf", "cell"]:
        level_addrs = [a for a in addresses if a.level == level]
        level_ids = [a.id for a in level_addrs]
        asset_count = 0
        if level_ids:
            asset_count = db.query(Asset).filter(
                Asset.storage_address_id.in_(level_ids), Asset.is_active == True,
            ).count()
        by_level[level] = {
            "count": len(level_addrs), "assets": asset_count,
            "capacity": sum(a.capacity or 0 for a in level_addrs),
        }
    return {
        "id": location.id, "name": location.name, "code": location.code or "",
        "location_type": location.location_type, "description": location.description or "",
        "room_id": location.room_id, "room_name": location.room.name if location.room else "",
        "full_name": location.get_full_name(), "capacity": location.capacity,
        "current_count": location.current_count, "by_level": by_level,
        "total_assets": len(all_assets),
        "assets": [
            {
                "id": a.id, "inventory_number": a.inventory_number or "",
                "name": a.name or "", "model": a.model or "",
                "responsible_person": a.responsible_person or "",
                "storage_address_id": a.storage_address_id,
                "full_address": a.storage_address.get_full_address() if a.storage_address else "",
            }
            for a in all_assets[:100]
        ],
    }


@router.post("/warehouse-locations")
async def create_warehouse_location(
    name: str = Query(...),
    room_id: int = Query(..., description="ID складского помещения"),
    code: Optional[str] = Query(None),
    location_type: str = Query("storage"),
    description: str = "",
    capacity: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Создать складскую локацию (зону/участок склада)"""
    from src.infrastructure.db.models.department import Room as RoomModel
    room = db.query(RoomModel).filter(
        RoomModel.id == room_id, RoomModel.room_type == "warehouse",
    ).first()
    if not room:
        raise HTTPException(status_code=404, detail="Складское помещение не найдено")
    if code:
        existing = db.query(WarehouseLocation).filter(
            WarehouseLocation.room_id == room_id, WarehouseLocation.code == code,
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Код '{code}' уже существует в этом складе")
    new_location = WarehouseLocation(
        room_id=room_id, name=name, code=code,
        location_type=location_type, description=description, capacity=capacity,
    )
    db.add(new_location)
    db.commit()
    db.refresh(new_location)
    return {
        "success": True, "id": new_location.id, "name": new_location.name,
        "code": new_location.code, "location_type": new_location.location_type,
        "full_name": new_location.get_full_name(),
    }


@router.put("/warehouse-locations/{location_id}")
async def update_warehouse_location(
    location_id: int,
    name: Optional[str] = Query(None),
    code: Optional[str] = Query(None),
    location_type: Optional[str] = Query(None),
    description: Optional[str] = Query(None),
    capacity: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Обновить складскую локацию"""
    location = db.query(WarehouseLocation).filter(WarehouseLocation.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Складская локация не найдена")
    if name is not None:
        location.name = name
    if code is not None:
        existing = db.query(WarehouseLocation).filter(
            WarehouseLocation.room_id == location.room_id,
            WarehouseLocation.code == code, WarehouseLocation.id != location_id,
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Код '{code}' уже существует в этом складе")
        location.code = code
    if location_type is not None:
        location.location_type = location_type
    if description is not None:
        location.description = description
    if capacity is not None:
        location.capacity = capacity
    if is_active is not None:
        location.is_active = is_active
    db.commit()
    db.refresh(location)
    return {
        "success": True, "id": location.id, "name": location.name,
        "code": location.code, "location_type": location.location_type,
    }


@router.delete("/warehouse-locations/{location_id}")
async def delete_warehouse_location(
    location_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Деактивировать складскую локацию (soft delete)"""
    location = db.query(WarehouseLocation).filter(WarehouseLocation.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Складская локация не найдена")
    direct_assets = db.query(Asset).filter(
        Asset.warehouse_location_id == location_id, Asset.is_active == True,
    ).count()
    if direct_assets > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Нельзя деактивировать: {direct_assets} активных активов. Сначала переместите активы.",
        )
    location.is_active = False
    db.commit()
    return {"success": True, "message": f"Локация '{location.name}' деактивирована"}


@router.get("/warehouse-locations/{location_id}/search")
async def search_assets_in_location(
    location_id: int,
    search: Optional[str] = Query(None),
    level: Optional[str] = Query(None, description="rack, shelf, cell"),
    recursive: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Поиск активов в складской локации"""
    location = db.query(WarehouseLocation).filter(WarehouseLocation.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Складская локация не найдена")
    sa_query = db.query(StorageAddress).filter(
        StorageAddress.warehouse_location_id == location_id, StorageAddress.is_active == True,
    )
    if level:
        sa_query = sa_query.filter(StorageAddress.level == level)
    all_addresses = sa_query.all()
    sa_ids = [sa.id for sa in all_addresses]
    if recursive and sa_ids:
        all_sa_ids = list(sa_ids)
        queue = list(sa_ids)
        while queue:
            current = queue.pop(0)
            children = db.query(StorageAddress).filter(
                StorageAddress.parent_id == current, StorageAddress.is_active == True,
            ).all()
            for child in children:
                if child.id not in all_sa_ids:
                    all_sa_ids.append(child.id)
                    queue.append(child.id)
        sa_ids = all_sa_ids
    direct_assets = db.query(Asset).filter(
        Asset.warehouse_location_id == location_id, Asset.is_active == True,
    ).all()
    child_assets = db.query(Asset).filter(
        Asset.storage_address_id.in_(sa_ids) if sa_ids else False, Asset.is_active == True,
    ).all()
    all_asset_ids = set()
    all_assets = []
    for asset in direct_assets:
        if asset.id not in all_asset_ids:
            all_asset_ids.add(asset.id)
            all_assets.append(asset)
    for asset in child_assets:
        if asset.id not in all_asset_ids:
            all_asset_ids.add(asset.id)
            all_assets.append(asset)
    if search:
        all_assets = [
            a for a in all_assets
            if (a.name and search.lower() in a.name.lower()
                or a.inventory_number and search.lower() in a.inventory_number.lower()
                or a.responsible_person and search.lower() in a.responsible_person.lower())
        ]
    return {
        "location_id": location.id, "location_name": location.name,
        "location_code": location.code or "", "room_name": location.room.name if location.room else "",
        "recursive": recursive, "total_assets": len(all_assets),
        "assets": [
            {
                "id": a.id, "inventory_number": a.inventory_number or "",
                "name": a.name or "", "model": a.model or "",
                "responsible_person": a.responsible_person or "", "rfid_tag": a.rfid_tag or "",
                "warehouse_location_id": a.warehouse_location_id,
                "storage_address_id": a.storage_address_id,
                "full_address": a.storage_address.get_full_address() if a.storage_address else "",
                "direct_location": a.warehouse_location_id is not None,
            }
            for a in all_assets
        ],
    }


@router.get("/warehouse-locations/stats")
async def get_warehouse_locations_stats(
    room_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Статистика по складским локациям"""
    query = db.query(WarehouseLocation).filter(WarehouseLocation.is_active == True)
    if room_id:
        query = query.filter(WarehouseLocation.room_id == room_id)
    locations = query.all()
    by_type = {}
    total_assets = 0
    total_storage_addresses = 0
    for loc in locations:
        loc_type = loc.location_type
        if loc_type not in by_type:
            by_type[loc_type] = {"count": 0, "total_capacity": 0, "total_assets": 0}
        by_type[loc_type]["count"] += 1
        by_type[loc_type]["total_capacity"] += loc.capacity or 0
        total_storage_addresses += len(loc.storage_addresses) if loc.storage_addresses else 0
        direct_count = 0
        child_count = 0
        if loc.storage_addresses:
            sa_ids = [sa.id for sa in loc.storage_addresses]
            direct_count = db.query(Asset).filter(
                Asset.warehouse_location_id == loc.id, Asset.is_active == True,
            ).count()
            child_count = db.query(Asset).filter(
                Asset.storage_address_id.in_(sa_ids), Asset.is_active == True,
            ).count()
        loc_total = direct_count + child_count
        total_assets += loc_total
        by_type[loc_type]["total_assets"] += loc_total
    return {
        "room_id": room_id, "total_locations": len(locations),
        "total_storage_addresses": total_storage_addresses,
        "total_assets": total_assets, "by_type": by_type,
    }


# ======================================================================
# Управление типами помещений (room <-> warehouse)
# ======================================================================

@router.put("/rooms/{room_id}/toggle-type")
async def toggle_room_type(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Переключить тип помещения: room <-> warehouse.
    
    При переключении room -> warehouse:
    - room_type устанавливается в 'warehouse'
    - Создаётся дерево storage_addresses: rack -> shelf -> cell
    - Создаётся WarehouseLocation по умолчанию
    
    При переключении warehouse -> room:
    - room_type устанавливается в 'room'
    - Деактивируются storage_addresses и warehouse_locations
    - Активы, привязанные к storage_address, сохраняют ссылку
    """
    from src.infrastructure.db.models.department import Room as RoomModel
    
    room = db.query(RoomModel).filter(RoomModel.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Помещение не найдено")
    
    if room.room_type == "room":
        # Конвертируем в склад
        room.room_type = "warehouse"
        
        # Создаём WarehouseLocation по умолчанию
        wl = WarehouseLocation(
            room_id=room_id,
            name="Основная зона",
            code=f"STO-{room_id:03d}",
            location_type="storage",
        )
        db.add(wl)
        db.flush()
        
        # Создаём дерево storage_addresses
        # Уровень 1: Стеллажи (racks)
        rack_names = ["A", "B", "C", "D", "E"]
        wl_id = wl.id
        for rack_letter in rack_names:
            rack = StorageAddress(
                warehouse_location_id=wl_id,
                room_id=room_id,
                level="rack",
                name=f"Стеллаж {rack_letter}",
                code=f"{room_id}-{rack_letter}",
            )
            db.add(rack)
            db.flush()
            
            # Уровень 2: Полки (shelves)
            for shelf_num in range(1, 6):
                shelf = StorageAddress(
                    parent_id=rack.id,
                    warehouse_location_id=wl_id,
                    room_id=room_id,
                    level="shelf",
                    name=f"Полка {shelf_num}",
                    code=f"{room_id}-{rack_letter}-{shelf_num}",
                )
                db.add(shelf)
                db.flush()
                
                # Уровень 3: Ячейки (cells)
                for cell_num in range(1, 11):
                    cell = StorageAddress(
                        parent_id=shelf.id,
                        warehouse_location_id=wl_id,
                        room_id=room_id,
                        level="cell",
                        name=f"Ячейка {cell_num}",
                        code=f"{room_id}-{rack_letter}-{shelf_num}-{cell_num}",
                        capacity=1,
                    )
                    db.add(cell)
        
        db.commit()
        db.refresh(room)
        
        return {
            "success": True,
            "message": f"Помещение '{room.name}' преобразовано в склад",
            "room_type": "warehouse",
            "storage_tree_created": True,
        }
    
    else:
        # Конвертируем в обычное помещение
        room.room_type = "room"
        
        # Деактивируем warehouse_locations
        wls = db.query(WarehouseLocation).filter(
            WarehouseLocation.room_id == room_id,
            WarehouseLocation.is_active == True,
        ).all()
        for wl in wls:
            wl.is_active = False
            # Деактивируем связанные storage_addresses
            sas = db.query(StorageAddress).filter(
                StorageAddress.warehouse_location_id == wl.id,
                StorageAddress.is_active == True,
            ).all()
            for sa in sas:
                sa.is_active = False
        
        db.commit()
        db.refresh(room)
        
        return {
            "success": True,
            "message": f"Помещение '{room.name}' преобразовано в обычное помещение",
            "room_type": "room",
            "storage_tree_deactivated": True,
        }


@router.get("/rooms/{room_id}/convert-preview")
async def preview_room_conversion(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Предпросмотр дерева storage_addresses при конвертации помещения в склад.
    Возвращает структуру без сохранения в БД.
    """
    from src.infrastructure.db.models.department import Room as RoomModel
    
    room = db.query(RoomModel).filter(RoomModel.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Помещение не найдено")
    
    rack_names = ["A", "B", "C", "D", "E"]
    tree = []
    for rack_letter in rack_names:
        rack_node = {
            "id": None, "name": f"Стеллаж {rack_letter}",
            "level": "rack", "code": f"{room_id}-{rack_letter}",
            "children": [],
        }
        for shelf_num in range(1, 6):
            shelf_node = {
                "id": None, "name": f"Полка {shelf_num}",
                "level": "shelf", "code": f"{room_id}-{rack_letter}-{shelf_num}",
                "children": [],
            }
            for cell_num in range(1, 11):
                shelf_node["children"].append({
                    "id": None, "name": f"Ячейка {cell_num}",
                    "level": "cell", "code": f"{room_id}-{rack_letter}-{shelf_num}-{cell_num}",
                    "children": [],
                })
            rack_node["children"].append(shelf_node)
        tree.append(rack_node)
    
    return {
        "room_id": room.id,
        "room_name": room.name,
        "current_type": room.room_type,
        "would_be_type": "warehouse" if room.room_type == "room" else "room",
        "preview_tree": tree,
        "total_racks": len(rack_names),
        "total_shelves": len(rack_names) * 5,
        "total_cells": len(rack_names) * 5 * 10,
    }


@router.get("/rooms/all")
async def get_all_rooms(
    room_type: Optional[str] = Query(None, description="filter by room_type: room or warehouse"),
    search: Optional[str] = Query(None, description="Search by name or department"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Список всех помещений с фильтрацией по типу"""
    from src.infrastructure.db.models.department import Room as RoomModel
    
    query = db.query(RoomModel).filter(RoomModel.is_active == True)
    if room_type:
        query = query.filter(RoomModel.room_type == room_type)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                RoomModel.name.ilike(search_pattern),
                RoomModel.building.ilike(search_pattern),
            )
        )
    rooms = query.order_by(RoomModel.department_id, RoomModel.name).all()
    
    return [
        {
            "id": r.id,
            "name": r.name,
            "department_id": r.department_id,
            "department_name": r.department.name if r.department else "",
            "floor": r.floor,
            "building": r.building,
            "room_type": r.room_type,
            "storage_addresses_count": len(r.storage_addresses) if r.storage_addresses else 0,
            "warehouse_locations_count": len(r.warehouse_locations) if hasattr(r, 'warehouse_locations') and r.warehouse_locations else 0,
        }
        for r in rooms
    ]
