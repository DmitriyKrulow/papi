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


def _build_storage_tree(addresses, parent_wl_id, db):
    """Построить дерево storage_addresses из списка"""
    logger.info(f"Building storage tree for wl_id={parent_wl_id}, addresses count={len(addresses)}")
    
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
            "warehouse_location_id": addr.warehouse_location_id,
            "capacity": addr.capacity,
            "current_count": addr.current_count,
        })
    
    logger.info(f"By level: { {k: len(v) for k, v in by_level.items()} }")
    
    def build_tree(p_id=None, lvl=None):
        children = []
        # Определяем, какой уровень искать для детей
        level_map = {
            None: "rack",    # Корень -> ищем rack'и
            "rack": "shelf", # Rack -> ищем shelf'и
            "shelf": "cell", # Shelf -> ищем cell'ы
            "cell": None,    # Cell -> нет детей
        }
        search_level = level_map.get(lvl)
        
        if search_level is None:
            return children
        
        logger.info(f"build_tree: p_id={p_id}, lvl={lvl}, search_level={search_level}, items_count={len(by_level.get(search_level, []))}")
        logger.info(f"build_tree: by_level keys={list(by_level.keys())}")
        
        for item in by_level.get(search_level, []):
            node = None
            # Для rack: проверяем warehouse_location_id (привязка к зоне)
            if item.get("level") == "rack":
                logger.debug(f"Checking rack: id={item['id']}, wl_id={item['warehouse_location_id']}, p_id={p_id}")
                if item.get("warehouse_location_id") == p_id:
                    logger.info(f"Found rack: {item['name']} for wl_id={p_id}")
                    node = {
                        "id": item["id"],
                        "name": item["name"],
                        "code": item["code"],
                        "level": item["level"],
                        "capacity": item["capacity"],
                        "current_count": item["current_count"],
                        "children": build_tree(item["id"], item["level"]),
                    }
            # Для shelf и cell: проверяем warehouse_location_id И parent_id
            elif item.get("level") in ("shelf", "cell"):
                # warehouse_location_id == p_id — привязка к зоне (p_id = zone ID)
                # parent_id == p_id — привязка к родителю (rack или shelf)
                logger.debug(f"Checking {item['level']}: id={item['id']}, wl_id={item['warehouse_location_id']}, parent_id={item['parent_id']}, p_id={p_id}")
                if item.get("warehouse_location_id") == p_id or item.get("parent_id") == p_id:
                    logger.info(f"Found {item['level']}: {item['name']} for wl_id={p_id} / parent_id={p_id}")
                    node = {
                        "id": item["id"],
                        "name": item["name"],
                        "code": item["code"],
                        "level": item["level"],
                        "capacity": item["capacity"],
                        "current_count": item["current_count"],
                        "children": build_tree(item["id"], item["level"]),
                    }
            if node:
                children.append(node)
        logger.info(f"build_tree: p_id={p_id}, lvl={lvl}, children_count={len(children)}")
        return children
    
    return build_tree(parent_wl_id, None)


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
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Создать адрес хранения"""
    name = payload.get("name", "")
    level = payload.get("level", "")
    parent_id = payload.get("parent_id")
    warehouse_location_id = payload.get("warehouse_location_id")
    code = payload.get("code")
    capacity = payload.get("capacity")
    description = payload.get("description", "")
    room_id = payload.get("room_id")
    
    logger.info(f"Creating StorageAddress: name={name}, level={level}, parent_id={parent_id}, warehouse_location_id={warehouse_location_id}, room_id={room_id}")
    
    if not name:
        raise HTTPException(status_code=400, detail="Название обязательно")
    if not level:
        raise HTTPException(status_code=400, detail="Уровень обязателен")
    
    # Проверка уникальности имени в рамках родителя/зоны
    if parent_id:
        existing = db.query(StorageAddress).filter(
            StorageAddress.parent_id == parent_id,
            StorageAddress.name == name,
            StorageAddress.level == level,
            StorageAddress.is_active == True,
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Элемент '{name}' уже существует у родителя")
    elif warehouse_location_id:
        existing = db.query(StorageAddress).filter(
            StorageAddress.warehouse_location_id == warehouse_location_id,
            StorageAddress.name == name,
            StorageAddress.level == level,
            StorageAddress.is_active == True,
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Элемент '{name}' уже существует в этой зоне")
    
    parent = None
    if parent_id:
        parent = db.query(StorageAddress).filter(StorageAddress.id == parent_id).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Родитель не найден")
        # Наследуем warehouse_location_id от родителя (rack) для shelf/cell
        if level in ("shelf", "cell") and not warehouse_location_id and parent.warehouse_location_id:
            warehouse_location_id = parent.warehouse_location_id
            logger.info(f"Inherited warehouse_location_id={warehouse_location_id} from parent {parent.level} (id={parent.id}) for {level}")
    if code:
        existing = db.query(StorageAddress).filter(StorageAddress.code == code).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Код '{code}' уже существует")
    new_address = StorageAddress(
        parent_id=parent_id, level=level, name=name,
        code=code, capacity=capacity, description=description, room_id=room_id,
        warehouse_location_id=warehouse_location_id,
    )
    logger.info(f"Created StorageAddress: id={new_address.id}, name={name}, level={level}, warehouse_location_id={new_address.warehouse_location_id}, parent_id={new_address.parent_id}")
    db.add(new_address)
    db.flush()
    db.refresh(new_address)
    logger.info(f"StorageAddress refreshed: id={new_address.id}, parent_id={new_address.parent_id}, warehouse_location_id={new_address.warehouse_location_id}")
    db.commit()
    return {
        "success": True, "id": new_address.id,
        "name": new_address.name, "level": new_address.level,
        "full_address": new_address.get_full_address(),
        "code": new_address.code,
    }


@router.delete("/{address_id}")
async def delete_address(
    address_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Удалить адрес хранения (soft delete)"""
    address = db.query(StorageAddress).filter(StorageAddress.id == address_id).first()
    if not address:
        raise HTTPException(status_code=404, detail="Адрес не найден")
    
    # Проверяем, есть ли активы в этом адресе или его детях
    asset_count = db.query(Asset).filter(
        Asset.storage_address_id == address_id, Asset.is_active == True,
    ).count()
    
    if asset_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Нельзя удалить: {asset_count} активных активов. Сначала переместите активы.",
        )
    
    address.is_active = False
    db.commit()
    return {"success": True, "message": f"Адрес '{address.name}' удалён"}


@router.patch("/{address_id}")
async def update_address(
    address_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Обновить адрес хранения (переименование)"""
    address = db.query(StorageAddress).filter(StorageAddress.id == address_id).first()
    if not address:
        raise HTTPException(status_code=404, detail="Адрес не найден")
    
    name = payload.get("name")
    if name is not None:
        address.name = name
    
    db.commit()
    db.refresh(address)
    return {
        "success": True,
        "id": address.id,
        "name": address.name,
        "level": address.level,
    }


@router.get("/rooms/{room_id}/tree")
async def get_room_location_tree(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Дерево склада: зоны (warehouse_locations) + storage_addresses + нераспределённые активы"""
    from src.infrastructure.db.models.department import Room as RoomModel
    
    room = db.query(RoomModel).filter(
        RoomModel.id == room_id,
        RoomModel.room_type == "warehouse",
    ).first()
    if not room:
        raise HTTPException(status_code=404, detail="Складское помещение не найдено")
    
    # ---- ZONES (WarehouseLocation) ----
    zones = db.query(WarehouseLocation).filter(
        WarehouseLocation.room_id == room_id,
        WarehouseLocation.is_active == True,
    ).order_by(WarehouseLocation.name).all()
    
    zone_list = []
    for z in zones:
        # Загружаем ВСЕ storage_addresses для зоны (rack, shelf, cell)
        # Rack привязан по warehouse_location_id, shelf/cell привязаны по parent_id (рекурсивно)
        all_sas = db.query(StorageAddress).filter(
            StorageAddress.room_id == z.room_id,
            StorageAddress.is_active == True,
        ).all()
        
        # Фильтруем только те, что принадлежат этой зоне
        zone_sas = []
        for sa in all_sas:
            if sa.warehouse_location_id == z.id:
                zone_sas.append(sa)
            elif sa.parent_id:
                # Проверяем, является ли родитель частью зоны
                parent = db.query(StorageAddress).filter(StorageAddress.id == sa.parent_id).first()
                if parent and parent.warehouse_location_id == z.id:
                    zone_sas.append(sa)
        
        logger.info(f"Zone {z.id} ({z.name}): found {len(zone_sas)} storage_addresses")
        for sa in zone_sas:
            logger.info(f"  SA: id={sa.id}, name={sa.name}, level={sa.level}, parent_id={sa.parent_id}, wl_id={sa.warehouse_location_id}")
        
        # Детальное логирование для отладки дерева
        logger.info(f"Calling _build_storage_tree with {len(zone_sas)} addresses, zone_id={z.id}")
        if zone_sas:
            levels = set(sa.level for sa in zone_sas)
            logger.info(f"  Levels in zone_sas: {levels}")
        
        sa_ids = [sa.id for sa in zone_sas]
        direct_count = db.query(Asset).filter(
            Asset.warehouse_location_id == z.id, Asset.is_active == True,
        ).count()
        child_count = 0
        if sa_ids:
            child_count = db.query(Asset).filter(
                Asset.storage_address_id.in_(sa_ids), Asset.is_active == True,
            ).count()
        
        zone_node = {
            "id": z.id,
            "name": z.name,
            "code": z.code or "",
            "level": "zone",
            "location_type": z.location_type,
            "capacity": z.capacity,
            "current_count": direct_count + child_count,
            "children": [],
            "is_zone": True,
        }
        
        if zone_sas:
            zone_node["children"] = _build_storage_tree(zone_sas, z.id, db)
        
        zone_list.append(zone_node)
    
    # ---- STORAGE ADDRESSES (не привязанные к warehouse_location) ----
    storage_addrs = db.query(StorageAddress).filter(
        StorageAddress.room_id == room_id,
        StorageAddress.is_active == True,
        StorageAddress.warehouse_location_id.is_(None),
    ).order_by(StorageAddress.level, StorageAddress.name).all()
    
    storage_tree = _build_storage_tree(storage_addrs, None, db)
    
    # ---- UNASSIGNED ASSETS ----
    unassigned = db.query(Asset).filter(
        Asset.is_active == True,
        Asset.room_id == room_id,
        Asset.storage_address_id.is_(None),
        Asset.warehouse_location_id.is_(None),
    ).order_by(Asset.inventory_number).all()
    
    unassigned_list = [
        {
            "id": a.id,
            "name": a.name or "",
            "inventory_number": a.inventory_number or "",
            "level": "asset",
        }
        for a in unassigned
    ]
    
    return {
        "room_id": room.id,
        "room_name": room.name,
        "zones": zone_list,
        "storage_tree": storage_tree,
        "unassigned_assets": unassigned_list,
        "unassigned_count": len(unassigned_list),
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
    
    # Получаем активы, привязанные к storage_address этого склада
    storage_address_asset_ids = []
    if room_address_ids:
        storage_address_asset_ids = [
            a.id for a in db.query(Asset.id).filter(
                Asset.is_active == True,
                Asset.storage_address_id.in_(room_address_ids),
            ).all()
        ]
    
    # Получаем все warehouse_location этого склада
    wl_ids = [
        wl.id for wl in db.query(WarehouseLocation.id).filter(
            WarehouseLocation.room_id == room_id,
            WarehouseLocation.is_active == True,
        ).all()
    ]
    
    # Получаем активы, привязанные напрямую к warehouse_location этого склада
    warehouse_location_asset_ids = []
    if wl_ids:
        warehouse_location_asset_ids = [
            a.id for a in db.query(Asset.id).filter(
                Asset.is_active == True,
                Asset.warehouse_location_id.in_(wl_ids),
            ).all()
        ]
    
    # Получаем активы, привязанные напрямую к помещению (room_id)
    room_asset_ids = [
        a.id for a in db.query(Asset.id).filter(
            Asset.is_active == True,
            Asset.room_id == room_id,
        ).all()
    ]
    
    # Объединяем уникальные ID активов
    all_asset_ids = list(set(storage_address_asset_ids + warehouse_location_asset_ids + room_asset_ids))
    
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
        
        # Фильтруем по ID активов
        query = db.query(Asset).filter(
            Asset.id.in_(all_asset_ids),
            Asset.is_active == True,
            Asset.storage_address_id.in_(all_ids),
        )
    else:
        # Все активы со склада
        query = db.query(Asset).filter(
            Asset.id.in_(all_asset_ids),
            Asset.is_active == True,
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
# Доступные адреса хранения для выбора
# ======================================================================

@router.get("/available-addresses")
async def get_available_storage_addresses(
    room_id: Optional[int] = Query(None, description="ID помещения для фильтрации"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Список всех активных storage_addresses уровня 'cell' для выбора в качестве места размещения актива.
    Можно отфильтровать по room_id.
    """
    query = db.query(StorageAddress).filter(
        StorageAddress.level == "cell",
        StorageAddress.is_active == True,
    )
    if room_id:
        query = query.filter(StorageAddress.room_id == room_id)
    
    addresses = query.order_by(StorageAddress.room_id, StorageAddress.name).all()
    
    return [
        {
            "id": sa.id,
            "name": sa.name,
            "room_id": sa.room_id,
            "room_name": sa.room.name if sa.room else "",
            "full_address": sa.get_full_address(),
            "parent_id": sa.parent_id,
        }
        for sa in addresses
    ]


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
        is_active=True,
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
        
        # Создаём WarehouseLocation по умолчанию (зона склада)
        wl = WarehouseLocation(
            room_id=room_id,
            name="Основная зона",
            code=f"STO-{room_id:03d}",
            location_type="storage",
        )
        db.add(wl)
        db.flush()
        
        # НЕ создаём ячейки автоматически — они создаются при добавлении стеллажей/полок вручную
        
        # Переназначаем активы из помещения на склад
        from src.infrastructure.db.models.asset import Asset as AssetModel
        
        # Ищем активы:
        # 1. С room_id = room_id (уже привязаны к помещению)
        # 2. С location_address, содержащим название помещения
        existing_assets = db.query(AssetModel).filter(
            AssetModel.is_active == True,
            (AssetModel.room_id == room_id) | 
            (AssetModel.location_address.like(f'%{room.name}%')),
        ).all()
        
        assets_assigned = 0
        if existing_assets:
            for asset in existing_assets:
                # Привязываем актив к складу через room_id и warehouse_location_id
                asset.room_id = room_id
                asset.warehouse_location_id = wl.id
                assets_assigned += 1
        
        db.commit()
        db.refresh(room)
        
        return {
            "success": True,
            "message": f"Помещение '{room.name}' преобразовано в склад",
            "room_type": "warehouse",
            "storage_tree_created": False,
            "cells_created": 0,
            "assets_assigned": assets_assigned,
            "debug": {
                "room_id": room_id,
                "room_name": room.name,
                "existing_assets_found": len(existing_assets),
                "assets_assigned": assets_assigned,
            }
        }
    
    else:
        # Конвертируем в обычное помещение
        room.room_type = "room"
        
        # Собираем все warehouse_location этого склада
        from src.infrastructure.db.models.asset import Asset as AssetModel
        wls = db.query(WarehouseLocation).filter(
            WarehouseLocation.room_id == room_id,
            WarehouseLocation.is_active == True,
        ).all()
        wl_ids = [wl.id for wl in wls]
        
        # Собираем все storage_addresses этого помещения
        sa_ids = []
        sas = db.query(StorageAddress).filter(
            StorageAddress.room_id == room_id,
            StorageAddress.is_active == True,
        ).all()
        for sa in sas:
            sa_ids.append(sa.id)
            # Рекурсивно собираем дочерние
            queue = [sa.id]
            while queue:
                current = queue.pop(0)
                children = db.query(StorageAddress).filter(
                    StorageAddress.parent_id == current,
                    StorageAddress.is_active == True,
                ).all()
                for child in children:
                    sa_ids.append(child.id)
                    queue.append(child.id)
        
        # Проставляем room_id всем активам, привязанным к storage_addresses или warehouse_location этого склада
        assets_to_assign = db.query(AssetModel).filter(
            AssetModel.is_active == True,
            (AssetModel.storage_address_id.in_(sa_ids)) | (AssetModel.warehouse_location_id.in_(wl_ids)),
        ).all()
        rooms_assigned = 0
        for asset in assets_to_assign:
            asset.room_id = room_id
            asset.storage_address_id = None
            asset.warehouse_location_id = None
            rooms_assigned += 1
        
        # Удаляем storage_addresses (cascade через warehouse_locations)
        for wl in wls:
            # Удаляем все storage_addresses этой warehouse_location
            db.query(StorageAddress).filter(
                StorageAddress.warehouse_location_id == wl.id,
            ).delete(synchronize_session=False)
            wl.is_active = False
        
        db.commit()
        db.refresh(room)
        
        return {
            "success": True,
            "message": f"Помещение '{room.name}' преобразовано в обычное помещение",
            "room_type": "room",
            "storage_tree_removed": True,
            "rooms_assigned": rooms_assigned,
        }


@router.get("/rooms/{room_id}/convert-preview")
async def preview_room_conversion(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Предпросмотр конвертации помещения в склад.
    Возвращает информацию без создания структуры.
    """
    from src.infrastructure.db.models.department import Room as RoomModel
    from src.infrastructure.db.models.asset import Asset as AssetModel
    from sqlalchemy import func
    
    room = db.query(RoomModel).filter(RoomModel.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Помещение не найдено")
    
    # Считаем активы, которые будут перенесены на склад
    asset_count = db.query(func.count(AssetModel.id)).filter(
        AssetModel.is_active == True,
        (AssetModel.room_id == room_id) | (AssetModel.location_address == room.name),
    ).scalar() or 0
    
    return {
        "room_id": room.id,
        "room_name": room.name,
        "current_type": room.room_type,
        "would_be_type": "warehouse" if room.room_type == "room" else "room",
        "assets_count": asset_count,
        "message": "При конвертации активы из помещения будут привязаны к складу. Ячейки создаются вручную при добавлении стеллажей.",
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
    
    # Получаем count активов для всех помещений одним запросом
    from src.infrastructure.db.models.asset import Asset as AssetModel
    from sqlalchemy import func
    room_id_to_asset_count = dict(
        db.query(
            AssetModel.room_id, func.count(AssetModel.id)
        ).filter(
            AssetModel.room_id.isnot(None),
            AssetModel.is_active == True,
        ).group_by(AssetModel.room_id).all()
    )
    
    # cell_count убран — активы разного размера, ячейки не имеют смысла
    # Считаем активы по storage_addresses ИЛИ warehouse_location
    
    # Получаем count активов для всех складов по storage_address_id ИЛИ warehouse_location_id
    room_id_to_storage_asset_count = {}
    for room in rooms:
        if room.room_type == "warehouse":
            # Считаем активы по storage_addresses этого склада
            sa_ids = [
                sa.id for sa in db.query(StorageAddress.id).filter(
                    StorageAddress.room_id == room.id,
                    StorageAddress.is_active == True,
                ).all()
            ]
            # Считаем активы по warehouse_location этого склада
            wl_ids = [
                wl.id for wl in db.query(WarehouseLocation.id).filter(
                    WarehouseLocation.room_id == room.id,
                    WarehouseLocation.is_active == True,
                ).all()
            ]
            # Объединяем: активы с storage_address_id ИЛИ warehouse_location_id
            from sqlalchemy import or_
            
            or_conditions = []
            if sa_ids:
                or_conditions.append(AssetModel.storage_address_id.in_(sa_ids))
            if wl_ids:
                or_conditions.append(AssetModel.warehouse_location_id.in_(wl_ids))
            
            if or_conditions:
                count = db.query(func.count(AssetModel.id)).filter(
                    AssetModel.is_active == True,
                    or_(*or_conditions),
                ).scalar() or 0
                room_id_to_storage_asset_count[room.id] = count
    
    # Считаем storage_addresses и warehouse_locations для всех помещений
    room_id_to_sa_count = {}
    room_id_to_wl_count = {}
    for room in rooms:
        room_id_to_sa_count[room.id] = db.query(func.count(StorageAddress.id)).filter(
            StorageAddress.room_id == room.id,
            StorageAddress.is_active == True,
        ).scalar() or 0
        room_id_to_wl_count[room.id] = db.query(func.count(WarehouseLocation.id)).filter(
            WarehouseLocation.room_id == room.id,
            WarehouseLocation.is_active == True,
        ).scalar() or 0
    
    return [
        {
            "id": r.id,
            "name": r.name,
            "department_id": r.department_id,
            "department_name": r.department.name if r.department else "",
            "floor": r.floor,
            "building": r.building,
            "room_type": r.room_type,
            "storage_addresses_count": room_id_to_sa_count.get(r.id, 0),
            "warehouse_locations_count": room_id_to_wl_count.get(r.id, 0),
            "full_name": f"{r.name} ({r.department.name})" if r.department else r.name,
            # asset_count: для складов — активы по storage_address_id, для обычных — по room_id
            "asset_count": room_id_to_storage_asset_count.get(r.id, 0) if r.room_type == "warehouse" else room_id_to_asset_count.get(r.id, 0),
        }
        for r in rooms
    ]


@router.get("/tree/{room_id}")
async def get_warehouse_tree(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить дерево склада с активами"""
    from src.infrastructure.db.models.department import Room as RoomModel
    
    room = db.query(RoomModel).filter(
        RoomModel.id == room_id,
        RoomModel.is_active == True,
    ).first()
    if not room:
        raise HTTPException(status_code=404, detail="Помещение не найдено")
    
    # Получаем все storage_addresses для этого помещения
    all_addresses = db.query(StorageAddress).filter(
        StorageAddress.room_id == room_id,
        StorageAddress.is_active == True,
    ).all()
    
    # Получаем все активы для этого помещения
    assets = db.query(Asset).filter(
        Asset.is_active == True,
        (Asset.room_id == room_id) | (Asset.warehouse_location_id.isnot(None)),
    ).all()
    
    # Группируем адреса по parent_id
    by_parent = {}
    for addr in all_addresses:
        if addr.parent_id not in by_parent:
            by_parent[addr.parent_id] = []
        by_parent[addr.parent_id].append(addr)
    
    # Считаем активы по storage_address_id
    assets_by_address = {}
    for asset in assets:
        if asset.storage_address_id:
            if asset.storage_address_id not in assets_by_address:
                assets_by_address[asset.storage_address_id] = []
            assets_by_address[asset.storage_address_id].append(asset)
    
    # Считаем активы без storage_address_id (нераспределённые)
    unassigned_assets = [a for a in assets if not a.storage_address_id]
    
    def build_node(addr):
        children = by_parent.get(addr.id, [])
        node = {
            "id": addr.id,
            "name": addr.name,
            "level": addr.level,
            "code": addr.code or "",
            "children": [],
            "asset_count": len(assets_by_address.get(addr.id, [])),
            "has_children": len(children) > 0,
        }
        # Рекурсивно добавляем детей
        for child in children:
            node["children"].append(build_node(child))
        return node
    
    # Корень — помещение
    root_nodes = by_parent.get(None, [])
    
    # Собираем дерево
    tree = []
    for node in root_nodes:
        tree.append(build_node(node))
    
    return {
        "room_id": room.id,
        "room_name": room.name,
        "full_name": f"{room.name} ({room.department.name})" if room.department else room.name,
        "tree": tree,
        "unassigned_assets": [
            {
                "id": a.id,
                "name": a.name or "",
                "inventory_number": a.inventory_number or "",
            }
            for a in unassigned_assets
        ],
        "unassigned_count": len(unassigned_assets),
    }
