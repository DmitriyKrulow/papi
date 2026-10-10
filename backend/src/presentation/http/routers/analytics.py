# backend/src/presentation/http/routers/analytics.py
"""Аналитика: тренды поломок, расхождения, рекомендации по закупкам"""
import logging
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from src.infrastructure.db.init_db import get_db
from src.infrastructure.db.models.asset import Asset
from src.infrastructure.db.models.repair_request import RepairRequest
from src.infrastructure.db.models.inventory_check import InventoryCheck
from src.infrastructure.db.models.inventory_check_item import InventoryCheckItem
from src.infrastructure.db.models.asset_type_config import AssetTypeConfig
from src.infrastructure.db.models.user import User
from src.presentation.http.dependencies.auth import get_current_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/breakdown-trends")
async def get_breakdown_trends(
    months: int = Query(12, description="Количество месяцев для анализа"),
    limit: int = Query(20, description="Лимит записей"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Тренды поломок: какие активы чаще всего ломаются.
    
    Показывает:
    - Топ-20 активов с наибольшим количеством ремонтов
    - Топ-10 типов активов с наибольшим количеством ремонтов
    - Динамику ремонтов по месяцам
    """
    cutoff_date = datetime.now() - timedelta(days=months * 30)
    
    # Топ активов по ремонтам
    top_assets = (
        db.query(
            RepairRequest.asset_id,
            Asset.name,
            Asset.inventory_number,
            Asset.asset_type,
            func.count(RepairRequest.id).label("repair_count"),
            func.sum(case((RepairRequest.status == "completed", 1), else_=0)).label("completed_count"),
            func.avg(RepairRequest.estimated_cost).label("avg_cost"),
        )
        .outerjoin(Asset, RepairRequest.asset_id == Asset.id)
        .filter(
            RepairRequest.created_at >= cutoff_date,
            Asset.is_active == True,
        )
        .group_by(RepairRequest.asset_id, Asset.name, Asset.inventory_number, Asset.asset_type)
        .order_by(func.desc("repair_count"))
        .limit(limit)
        .all()
    )
    
    # Топ типов активов по ремонтам
    type_configs = {tc.code: tc for tc in db.query(AssetTypeConfig).all()}
    
    top_types = (
        db.query(
            Asset.asset_type,
            func.count(RepairRequest.id).label("repair_count"),
            func.sum(case((RepairRequest.status == "completed", 1), else_=0)).label("completed_count"),
            func.avg(RepairRequest.estimated_cost).label("avg_cost"),
        )
        .outerjoin(RepairRequest, Asset.id == RepairRequest.asset_id)
        .filter(
            RepairRequest.created_at >= cutoff_date,
            Asset.is_active == True,
        )
        .group_by(Asset.asset_type)
        .order_by(func.desc("repair_count"))
        .limit(10)
        .all()
    )
    
    # Динамика по месяцам
    monthly_repairs = (
        db.query(
            func.strftime('%Y-%m', RepairRequest.created_at).label("month"),
            func.count(RepairRequest.id).label("count"),
        )
        .filter(RepairRequest.created_at >= cutoff_date)
        .group_by(func.strftime('%Y-%m', RepairRequest.created_at))
        .order_by("month")
        .all()
    )
    
    # Статусы ремонтов
    status_stats = (
        db.query(
            RepairRequest.status,
            func.count(RepairRequest.id).label("count"),
        )
        .filter(RepairRequest.created_at >= cutoff_date)
        .group_by(RepairRequest.status)
        .all()
    )
    
    return {
        "period_months": months,
        "cutoff_date": cutoff_date.isoformat(),
        "top_assets": [
            {
                "asset_id": a.asset_id,
                "name": a.name or "",
                "inventory_number": a.inventory_number or "",
                "asset_type": a.asset_type or "",
                "repair_count": a.repair_count or 0,
                "completed_count": a.completed_count or 0,
                "avg_cost": float(a.avg_cost or 0),
            }
            for a in top_assets
        ],
        "top_types": [
            {
                "type_code": t.asset_type or "unknown",
                "type_name": type_configs.get(t.asset_type or "").name if t.asset_type else "unknown",
                "repair_count": t.repair_count or 0,
                "completed_count": t.completed_count or 0,
                "avg_cost": float(t.avg_cost or 0),
            }
            for t in top_types
        ],
        "monthly_trend": [
            {"month": m.month, "count": m.count}
            for m in monthly_repairs
        ],
        "status_distribution": [
            {"status": s.status, "count": s.count}
            for s in status_stats
        ],
    }


@router.get("/discrepancy-analysis")
async def get_discrepancy_analysis(
    months: int = Query(12, description="Количество месяцев для анализа"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Анализ расхождений: где возникают систематические проблемы.
    
    Показывает:
    - Подразделения с наибольшим количеством расхождений
    - Типы активов с наибольшим процентом расхождений
    - Динамику расхождений по месяцам
    """
    cutoff_date = datetime.now() - timedelta(days=months * 30)
    
    # Расхождения по подразделениям
    dept_discrepancies = (
        db.query(
            Asset.department_code,
            func.count(InventoryCheckItem.id).label("total_checked"),
            func.sum(case((InventoryCheckItem.result == "missing", 1), else_=0)).label("missing_count"),
            func.sum(case((InventoryCheckItem.result == "surplus", 1), else_=0)).label("surplus_count"),
        )
        .join(InventoryCheck, InventoryCheckItem.inventory_check_id == InventoryCheck.id)
        .filter(
            InventoryCheck.created_at >= cutoff_date,
            InventoryCheck.status == "completed",
            Asset.is_active == True,
        )
        .group_by(Asset.department_code)
        .order_by(func.desc("missing_count"))
        .all()
    )
    
    # Расхождения по типам активов
    type_discrepancies = (
        db.query(
            Asset.asset_type,
            func.count(InventoryCheckItem.id).label("total_checked"),
            func.sum(case((InventoryCheckItem.result == "missing", 1), else_=0)).label("missing_count"),
            func.sum(case((InventoryCheckItem.result == "surplus", 1), else_=0)).label("surplus_count"),
        )
        .join(InventoryCheck, InventoryCheckItem.inventory_check_id == InventoryCheck.id)
        .filter(
            InventoryCheck.created_at >= cutoff_date,
            InventoryCheck.status == "completed",
            Asset.is_active == True,
        )
        .group_by(Asset.asset_type)
        .order_by(func.desc("missing_count"))
        .all()
    )
    
    # Динамика расхождений по месяцам
    monthly_discrepancies = (
        db.query(
            func.strftime('%Y-%m', InventoryCheck.created_at).label("month"),
            func.sum(case((InventoryCheckItem.result == "missing", 1), else_=0)).label("missing"),
            func.sum(case((InventoryCheckItem.result == "surplus", 1), else_=0)).label("surplus"),
        )
        .join(InventoryCheckItem, InventoryCheckItem.inventory_check_id == InventoryCheck.id)
        .filter(
            InventoryCheck.created_at >= cutoff_date,
            InventoryCheck.status == "completed",
        )
        .group_by(func.strftime('%Y-%m', InventoryCheck.created_at))
        .order_by("month")
        .all()
    )
    
    return {
        "period_months": months,
        "dept_discrepancies": [
            {
                "department": d.department_code or "Не указано",
                "total_checked": d.total_checked or 0,
                "missing": d.missing_count or 0,
                "surplus": d.surplus_count or 0,
                "discrepancy_rate": round((d.missing_count or 0) / (d.total_checked or 1) * 100, 1),
            }
            for d in dept_discrepancies
        ],
        "type_discrepancies": [
            {
                "type": t.asset_type or "unknown",
                "total_checked": t.total_checked or 0,
                "missing": t.missing_count or 0,
                "surplus": t.surplus_count or 0,
                "discrepancy_rate": round((t.missing_count or 0) / (t.total_checked or 1) * 100, 1),
            }
            for t in type_discrepancies
        ],
        "monthly_trend": [
            {"month": m.month, "missing": m.missing, "surplus": m.surplus}
            for m in monthly_discrepancies
        ],
    }


@router.get("/purchase-recommendations")
async def get_purchase_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Рекомендации по закупкам на основе аналитики.
    
    Показывает:
    - Какие типы активов чаще всего ломаются (нужна замена)
    - Какие позиции систематически отсутствуют при инвентаризации
    - Активы с высоким износом (>80%)
    - Тренды роста стоимости ремонта
    """
    # Топ-5 типов активов для замены (чаще всего ломаются)
    replacement_candidates = (
        db.query(
            Asset.asset_type,
            func.count(RepairRequest.id).label("repair_count"),
            func.avg(RepairRequest.estimated_cost).label("avg_repair_cost"),
            func.count(Asset.id).label("total_assets"),
        )
        .outerjoin(RepairRequest, Asset.id == RepairRequest.asset_id)
        .filter(Asset.is_active == True)
        .group_by(Asset.asset_type)
        .having(func.count(RepairRequest.id) > 0)
        .order_by(func.desc("repair_count"))
        .limit(5)
        .all()
    )
    
    # Активы с высоким износом (пора списывать)
    high_wear = (
        db.query(
            Asset.id,
            Asset.inventory_number,
            Asset.name,
            Asset.asset_type,
            Asset.department_code,
            Asset.purchase_price,
            Asset.current_value,
            ((Asset.purchase_price - Asset.current_value) / Asset.purchase_price * 100).label("wear_percent"),
        )
        .filter(
            Asset.is_active == True,
            Asset.purchase_price > 0,
            (Asset.purchase_price - Asset.current_value) / Asset.purchase_price >= 0.8,
        )
        .order_by(func.desc("wear_percent"))
        .limit(20)
        .all()
    )
    
    # Систематически отсутствующие позиции
    missing_items = (
        db.query(
            Asset.asset_type,
            func.count(InventoryCheckItem.id).label("missing_count"),
        )
        .join(InventoryCheck, InventoryCheckItem.inventory_check_id == InventoryCheck.id)
        .filter(
            InventoryCheck.status == "completed",
            InventoryCheckItem.result == "missing",
            Asset.is_active == True,
        )
        .group_by(Asset.asset_type)
        .order_by(func.desc("missing_count"))
        .limit(10)
        .all()
    )
    
    type_configs = {tc.code: tc for tc in db.query(AssetTypeConfig).all()}
    
    return {
        "replacement_candidates": [
            {
                "type_code": r.asset_type or "unknown",
                "type_name": type_configs.get(r.asset_type or "").name if r.asset_type else "unknown",
                "repair_count": r.repair_count or 0,
                "avg_repair_cost": float(r.avg_repair_cost or 0),
                "total_assets": r.total_assets or 0,
                "recommendation": "Рассмотреть замену на новые модели",
            }
            for r in replacement_candidates
        ],
        "high_wear_assets": [
            {
                "asset_id": h.id,
                "inventory_number": h.inventory_number or "",
                "name": h.name or "",
                "asset_type": h.asset_type or "",
                "department": h.department_code or "",
                "purchase_price": float(h.purchase_price or 0),
                "current_value": float(h.current_value or 0),
                "wear_percent": round(float(h.wear_percent or 0), 1),
                "recommendation": "Списать и закупить новый",
            }
            for h in high_wear
        ],
        "missing_items": [
            {
                "type": m.asset_type or "unknown",
                "missing_count": m.missing_count or 0,
                "recommendation": "Проверить наличие на складе",
            }
            for m in missing_items
        ],
    }


@router.get("/overview")
async def get_analytics_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Обзорная аналитика по системе"""
    total_assets = db.query(func.count(Asset.id)).filter(Asset.is_active == True).scalar() or 0
    
    # Статусы активов
    status_breakdown = (
        db.query(Asset.status, func.count(Asset.id))
        .filter(Asset.is_active == True)
        .group_by(Asset.status)
        .all()
    )
    
    # Активы требующие ремонта
    pending_repairs = (
        db.query(func.count(RepairRequest.id))
        .filter(RepairRequest.status.in_(["open", "in_progress"]))
        .scalar() or 0
    )
    
    # Активы с высоким износом
    high_wear_count = (
        db.query(func.count(Asset.id))
        .filter(
            Asset.is_active == True,
            Asset.purchase_price > 0,
            (Asset.purchase_price - Asset.current_value) / Asset.purchase_price >= 0.8,
        )
        .scalar() or 0
    )
    
    # Расхождения за последние 30 дней
    from datetime import timedelta
    thirty_days_ago = datetime.now() - timedelta(days=30)
    discrepancies = (
        db.query(func.count(InventoryCheckItem.id))
        .join(InventoryCheck, InventoryCheckItem.inventory_check_id == InventoryCheck.id)
        .filter(
            InventoryCheck.created_at >= thirty_days_ago,
            InventoryCheckItem.result.in_(["missing", "surplus"]),
        )
        .scalar() or 0
    )
    
    return {
        "total_assets": total_assets,
        "status_breakdown": [
            {"status": s.status, "count": s.count}
            for s in status_breakdown
        ],
        "pending_repairs": pending_repairs,
        "high_wear_assets": high_wear_count,
        "discrepancies_last_30_days": discrepancies,
        "recommendations_count": len(
            db.query(Asset.id)
            .filter(
                Asset.is_active == True,
                Asset.purchase_price > 0,
                (Asset.purchase_price - Asset.current_value) / Asset.purchase_price >= 0.8,
            )
            .all()
        ),
    }
