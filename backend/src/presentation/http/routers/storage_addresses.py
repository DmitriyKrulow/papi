# backend/src/presentation/http/routers/storage_addresses.py
"""Адресное хранение — управление стеллажами, полками, ячейками"""
import logging
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.infrastructure.db.init_db import get_db
from src.infrastructure.db.models.storage_address import StorageAddress
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
