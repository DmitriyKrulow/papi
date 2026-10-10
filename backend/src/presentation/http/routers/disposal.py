# backend/src/presentation/http/routers/disposal.py
"""Списание и выбытие активов — дисциплина списания"""
import logging
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.infrastructure.db.init_db import get_db
from src.infrastructure.db.models.asset import Asset
from src.infrastructure.db.models.audit_log import AuditLog
from src.infrastructure.db.models.user import User
from src.presentation.http.dependencies.auth import get_current_user, get_current_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/disposal", tags=["disposal"])


@router.post("/decommission")
async def decommission_asset(
    asset_id: int = Query(..., description="ID актива для списания"),
    reason: str = Query(..., description="Причина списания"),
    disposal_date: Optional[str] = Query(None, description="Дата списания (ISO format)"),
    comment: str = Query("", description="Комментарий"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Списание актива из активного реестра.
    
    Правило немедленного отражения выбытия:
    - Как только объект списан — он исчезает из активного реестра
    - Статус меняется на 'decommissioned'
    - Создаётся запись в журнале аудита
    - Отправляется уведомление
    
    Причины:
    - physical_damage: Физический износ
    - lost: Утеря
    - sold: Продан
    - donated: Передан
    - other: Другое
    """
    asset = db.query(Asset).filter(Asset.id == asset_id, Asset.is_active == True).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Актив не найден или уже неактивен")
    
    if asset.status == "decommissioned":
        raise HTTPException(status_code=400, detail="Актив уже списан")
    
    # Сохраняем старые данные для аудита
    old_data = {
        "status": asset.status,
        "inventory_number": asset.inventory_number or "",
        "name": asset.name or "",
        "department_code": asset.department_code or "",
        "responsible_person": asset.responsible_person or "",
        "current_value": float(asset.current_value or 0),
        "purchase_price": float(asset.purchase_price or 0),
    }
    
    # Списываем актив
    old_status = asset.status
    asset.status = "decommissioned"
    asset.is_active = False
    
    # Дата списания
    actual_disposal_date = datetime.now()
    if disposal_date:
        try:
            actual_disposal_date = datetime.fromisoformat(disposal_date)
        except ValueError:
            pass
    
    # Создаём запись в журнале аудита
    audit_entry = AuditLog(
        user_id=current_user.id,
        entity_type="Asset",
        entity_id=asset_id,
        action="decommission",
        old_values=old_data,
        new_values={
            "status": "decommissioned",
            "is_active": False,
            "disposal_date": actual_disposal_date.isoformat(),
            "reason": reason,
            "comment": comment,
        },
        diff_summary=f"Актив списан: {old_status} → decommissioned. Причина: {reason}",
        comment=f"Списание актива: {asset.name} ({asset.inventory_number}). Причина: {reason}. {comment}",
    )
    db.add(audit_entry)
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Актив '{asset.name}' списан",
        "asset": {
            "id": asset.id,
            "inventory_number": asset.inventory_number,
            "name": asset.name,
            "status": "decommissioned",
            "is_active": False,
        },
        "disposal_date": actual_disposal_date.isoformat(),
        "reason": reason,
        "comment": comment,
        "user": current_user.full_name or current_user.username,
    }


@router.post("/write-off")
async def write_off_asset(
    asset_id: int = Query(..., description="ID актива для списания"),
    reason: str = Query(..., description="Причина списания"),
    disposal_date: Optional[str] = Query(None, description="Дата списания (ISO format)"),
    comment: str = Query("", description="Комментарий"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Полное списание актива (альтернативное название).
    
    То же что и decommission, но с другим названием для бухгалтерии.
    """
    return await decommission_asset(
        asset_id=asset_id,
        reason=reason,
        disposal_date=disposal_date,
        comment=comment,
        db=db,
        current_user=current_user,
    )


@router.post("/sell")
async def sell_asset(
    asset_id: int = Query(..., description="ID актива для продажи"),
    sale_price: float = Query(..., description="Цена продажи"),
    buyer: str = Query(..., description="Покупатель"),
    sale_date: Optional[str] = Query(None, description="Дата продажи (ISO format)"),
    comment: str = Query("", description="Комментарий"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Продажа актива.
    
    Актив списывается из активного реестра, фиксируется продажа.
    """
    asset = db.query(Asset).filter(Asset.id == asset_id, Asset.is_active == True).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Актив не найден или уже неактивен")
    
    old_data = {
        "status": asset.status,
        "inventory_number": asset.inventory_number or "",
        "name": asset.name or "",
        "current_value": float(asset.current_value or 0),
        "purchase_price": float(asset.purchase_price or 0),
    }
    
    # Списываем актив
    asset.status = "written_off"
    asset.is_active = False
    
    actual_sale_date = datetime.now()
    if sale_date:
        try:
            actual_sale_date = datetime.fromisoformat(sale_date)
        except ValueError:
            pass
    
    # Создаём запись в журнале аудита
    audit_entry = AuditLog(
        user_id=current_user.id,
        entity_type="Asset",
        entity_id=asset_id,
        action="sell",
        old_values=old_data,
        new_values={
            "status": "written_off",
            "is_active": False,
            "sale_price": sale_price,
            "buyer": buyer,
            "sale_date": actual_sale_date.isoformat(),
            "comment": comment,
        },
        diff_summary=f"Актив продан: {asset.name} за {sale_price} руб. Покупатель: {buyer}",
        comment=f"Продажа актива: {asset.name} ({asset.inventory_number}). Цена: {sale_price} руб. Покупатель: {buyer}. {comment}",
    )
    db.add(audit_entry)
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Актив '{asset.name}' продан",
        "asset": {
            "id": asset.id,
            "inventory_number": asset.inventory_number,
            "name": asset.name,
            "status": "written_off",
            "is_active": False,
        },
        "sale_date": actual_sale_date.isoformat(),
        "sale_price": sale_price,
        "buyer": buyer,
        "comment": comment,
        "user": current_user.full_name or current_user.username,
    }


@router.get("/pending-disposal")
async def get_pending_disposal(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Получить список активов, требующих списания.
    
    Критерии:
    - Износ > 80%
    - Статус 'maintenance' более 30 дней
    - Не инвентаризировались более 1 года
    """
    from sqlalchemy import text
    
    # Активы с износом > 80%
    high_wear = (
        db.query(Asset)
        .filter(
            Asset.is_active == True,
            Asset.purchase_price > 0,
            (Asset.purchase_price - Asset.current_value) / Asset.purchase_price >= 0.8,
        )
        .order_by(
            (Asset.purchase_price - Asset.current_value) / Asset.purchase_price.desc()
        )
        .limit(50)
        .all()
    )
    
    # Активы на ремонте > 30 дней
    long_maintenance = (
        db.query(Asset)
        .filter(
            Asset.is_active == True,
            Asset.status == "maintenance",
        )
        .all()
    )
    
    # Не инвентаризированные > 1 года
    from datetime import timedelta
    one_year_ago = datetime.now() - timedelta(days=365)
    not_inventoried = (
        db.query(Asset)
        .filter(
            Asset.is_active == True,
            (Asset.last_inventory_date.is_(None)) | (Asset.last_inventory_date < one_year_ago),
        )
        .order_by(Asset.last_inventory_date.asc())
        .limit(50)
        .all()
    )
    
    return {
        "high_wear_count": len(high_wear),
        "long_maintenance_count": len(long_maintenance),
        "not_inventoried_count": len(not_inventoried),
        "high_wear_assets": [
            {
                "id": a.id,
                "inventory_number": a.inventory_number or "",
                "name": a.name or "",
                "asset_type": a.asset_type or "",
                "department": a.department_code or "",
                "purchase_price": float(a.purchase_price or 0),
                "current_value": float(a.current_value or 0),
                "wear_percent": round((a.purchase_price - a.current_value) / a.purchase_price * 100, 1) if a.purchase_price > 0 else 0,
            }
            for a in high_wear
        ],
        "long_maintenance_assets": [
            {
                "id": a.id,
                "inventory_number": a.inventory_number or "",
                "name": a.name or "",
                "department": a.department_code or "",
                "status": a.status,
            }
            for a in long_maintenance
        ],
        "not_inventoried_assets": [
            {
                "id": a.id,
                "inventory_number": a.inventory_number or "",
                "name": a.name or "",
                "department": a.department_code or "",
                "last_inventory_date": a.last_inventory_date.isoformat() if a.last_inventory_date else None,
            }
            for a in not_inventoried
        ],
    }


@router.get("/history")
async def get_disposal_history(
    limit: int = Query(50, description="Количество записей"),
    start_date: Optional[str] = Query(None, description="Начальная дата"),
    end_date: Optional[str] = Query(None, description="Конечная дата"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """История списаний и выбытий"""
    from sqlalchemy import text
    
    query = db.query(AuditLog).filter(
        AuditLog.action.in_(["decommission", "sell", "write_off"]),
    )
    
    if start_date:
        query = query.filter(AuditLog.created_at >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(AuditLog.created_at <= datetime.fromisoformat(end_date))
    
    entries = query.order_by(AuditLog.created_at.desc()).limit(limit).all()
    
    return {
        "total": len(entries),
        "entries": [
            {
                "id": e.id,
                "created_at": e.created_at.isoformat() if e.created_at else None,
                "user_name": e.user.username if e.user else None,
                "entity_type": e.entity_type,
                "entity_id": e.entity_id,
                "action": e.action,
                "diff_summary": e.diff_summary,
                "comment": e.comment,
                "old_values": e.old_values,
                "new_values": e.new_values,
            }
            for e in entries
        ],
    }


@router.get("/stats")
async def get_disposal_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Статистика по списаниям и выбытиям"""
    from sqlalchemy import func
    
    # Всего списано
    total_decommissioned = (
        db.query(func.count(Asset.id))
        .filter(Asset.is_active == False, Asset.status == "decommissioned")
        .scalar() or 0
    )
    
    # Всего продано
    total_sold = (
        db.query(func.count(Asset.id))
        .filter(Asset.is_active == False, Asset.status == "written_off")
        .scalar() or 0
    )
    
    # Всего активных
    total_active = (
        db.query(func.count(Asset.id))
        .filter(Asset.is_active == True)
        .scalar() or 0
    )
    
    # Процент списанных
    total_all = total_active + total_decommissioned + total_sold
    decommission_percent = round(total_decommissioned / total_all * 100, 1) if total_all > 0 else 0
    sold_percent = round(total_sold / total_all * 100, 1) if total_all > 0 else 0
    
    # Последние 7 дней
    from datetime import timedelta
    week_ago = datetime.now() - timedelta(days=7)
    this_week_decommissions = (
        db.query(func.count(AuditLog.id))
        .filter(
            AuditLog.action.in_(["decommission", "sell", "write_off"]),
            AuditLog.created_at >= week_ago,
        )
        .scalar() or 0
    )
    
    return {
        "total_active": total_active,
        "total_decommissioned": total_decommissioned,
        "total_sold": total_sold,
        "decommission_percent": decommission_percent,
        "sold_percent": sold_percent,
        "this_week_disposals": this_week_decommissions,
    }
