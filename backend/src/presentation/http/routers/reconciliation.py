# backend/src/presentation/http/routers/reconciliation.py
"""Ежемесячная сверка с бухгалтерией"""
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from src.infrastructure.db.init_db import get_db
from src.infrastructure.db.models.inventory_schedule import ReconciliationRecord
from src.infrastructure.db.models.asset import Asset
from src.infrastructure.db.models.user import User
from src.presentation.http.dependencies.auth import get_current_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/reconciliation", tags=["reconciliation"])


@router.post("")
async def create_reconciliation(
    year: int = Query(..., description="Год"),
    month: int = Query(..., description="Месяц (1-12)"),
    papi_total_assets: int = Query(..., description="Количество активов в системе"),
    papi_purchase_value: float = Query(0, description="Первоначальная стоимость"),
    papi_current_value: float = Query(0, description="Текущая стоимость"),
    accounting_total_assets: Optional[int] = Query(None, description="Количество в бухгалтерии"),
    accounting_purchase_value: Optional[float] = Query(None, description="Первоначальная стоимость в бухгалтерии"),
    accounting_current_value: Optional[float] = Query(None, description="Текущая стоимость в бухгалтерии"),
    discrepancy_count: int = Query(0, description="Количество расхождений"),
    discrepancy_value: str = Query("", description="JSON расхождений"),
    comment: str = Query("", description="Комментарий"),
    report_file: Optional[str] = Query(None, description="Путь к файлу отчёта"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Создать запись ежемесячной сверки"""
    # Проверяем не создана ли уже сверка за этот период
    existing = db.query(ReconciliationRecord).filter(
        ReconciliationRecord.period_year == year,
        ReconciliationRecord.period_month == month,
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail=f"Сверка за {year}-{month:02d} уже существует")
    
    record = ReconciliationRecord(
        period_year=year,
        period_month=month,
        reconciliation_date=datetime.now(),
        papi_total_assets=papi_total_assets,
        papi_total_value=f"{papi_purchase_value},{papi_current_value}",
        accounting_total_assets=accounting_total_assets,
        accounting_total_value=f"{accounting_purchase_value},{accounting_current_value}" if accounting_purchase_value else None,
        discrepancy_count=discrepancy_count,
        discrepancy_value=discrepancy_value,
        status="completed" if discrepancy_count == 0 else "discrepancies_found",
        reconciled_by=current_user.id,
        comment=comment,
        report_file=report_file,
    )
    
    db.add(record)
    db.commit()
    db.refresh(record)
    
    return {
        "success": True,
        "id": record.id,
        "period": f"{year}-{month:02d}",
        "status": record.status,
        "message": "Сверка создана" if discrepancy_count == 0 else "Обнаружены расхождения!",
    }


@router.get("/history")
async def get_reconciliation_history(
    limit: int = Query(12, description="Количество записей"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """История сверок"""
    records = db.query(ReconciliationRecord).order_by(
        ReconciliationRecord.period_year.desc(),
        ReconciliationRecord.period_month.desc(),
    ).limit(limit).all()
    
    return {
        "records": [
            {
                "id": r.id,
                "period": f"{r.period_year}-{r.period_month:02d}",
                "year": r.period_year,
                "month": r.period_month,
                "reconciliation_date": r.reconciliation_date.isoformat() if r.reconciliation_date else None,
                "papi_total_assets": r.papi_total_assets,
                "accounting_total_assets": r.accounting_total_assets,
                "discrepancy_count": r.discrepancy_count,
                "status": r.status,
                "reconciled_by_name": r.reconciled_by_user.full_name if r.reconciled_by_user else None,
                "comment": r.comment,
            }
            for r in records
        ],
        "total": len(records),
    }


@router.get("/stats")
async def get_reconciliation_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Статистика сверок"""
    total = db.query(func.count(ReconciliationRecord.id)).scalar() or 0
    
    with_discrepancies = db.query(func.count(ReconciliationRecord.id)).filter(
        ReconciliationRecord.discrepancy_count > 0
    ).scalar() or 0
    
    # Последние 12 месяцев
    last_12 = db.query(ReconciliationRecord).order_by(
        ReconciliationRecord.period_year.desc(),
        ReconciliationRecord.period_month.desc(),
    ).limit(12).all()
    
    # Процент сверок без расхождений
    clean_percent = round((total - with_discrepancies) / total * 100, 1) if total > 0 else 0
    
    return {
        "total_reconciliations": total,
        "with_discrepancies": with_discrepancies,
        "clean_percent": clean_percent,
        "last_12_months": [
            {
                "period": f"{r.period_year}-{r.period_month:02d}",
                "discrepancy_count": r.discrepancy_count,
                "status": r.status,
            }
            for r in last_12
        ],
    }


@router.get("/monthly-trend")
async def get_monthly_trend(
    months: int = Query(12, description="Количество месяцев"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Тренд расхождений по месяцам"""
    records = db.query(ReconciliationRecord).order_by(
        ReconciliationRecord.period_year.desc(),
        ReconciliationRecord.period_month.desc(),
    ).limit(months).all()
    
    # Группируем по месяцам
    trend = []
    for r in records:
        trend.append({
            "period": f"{r.period_year}-{r.period_month:02d}",
            "discrepancy_count": r.discrepancy_count,
            "status": r.status,
        })
    
    # Разворачиваем для хронологического порядка
    trend.reverse()
    
    return {
        "trend": trend,
        "average_discrepancies": round(
            sum(r.discrepancy_count for r in records) / len(records), 1
        ) if records else 0,
    }
