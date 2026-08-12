# src/presentation/http/routers/audit.py
"""API-роутер для журнала аудита."""

import json
from fastapi import APIRouter, Depends, Query, Response
from typing import Optional
from sqlalchemy.orm import Session

from src.presentation.http.dependencies.auth import get_current_admin, get_current_user, get_db
from src.core.services.audit_service import AuditService

router = APIRouter(prefix="/api/audit", tags=["Audit Log"])

# Словари для перевода типов сущностей
ENTITY_LABELS = {
    "Asset": "Актив",
    "User": "Пользователь",
    "RepairRequest": "Заявка на ремонт",
    "InventoryCheck": "Инвентаризация",
    "Department": "Подразделение",
    "Employee": "Сотрудник",
}

ACTION_LABELS = {
    "create": "Создание",
    "update": "Изменение",
    "delete": "Удаление",
    "login": "Вход",
    "logout": "Выход",
    "status_change": "Смена статуса",
    "import": "Импорт",
    "export": "Экспорт",
    "inventory_start": "Начало инвентаризации",
    "inventory_complete": "Завершение инвентаризации",
    "repair_create": "Создание заявки",
    "repair_update": "Обновление заявки",
}


def _format_diff_summary(diff: Optional[str]) -> str:
    """Форматирует diff_summary для отображения."""
    if not diff:
        return "—"
    return diff


def _get_entity_name(db: Session, entity_type: str, entity_id: int) -> str:
    """Получает человеко-читаемое имя сущности."""
    if entity_id == 0:
        return ""
    
    try:
        if entity_type == "Asset":
            from src.infrastructure.db.models.asset import Asset
            asset = db.query(Asset).filter(Asset.id == entity_id).first()
            if asset:
                return f"{str(asset.name)} ({str(asset.inventory_number)})"
        elif entity_type == "User":
            from src.infrastructure.db.models.user import User
            user = db.query(User).filter(User.id == entity_id).first()
            if user:
                return str(user.full_name) or str(user.username)
        elif entity_type == "RepairRequest":
            from src.infrastructure.db.models.repair_request import RepairRequest
            req = db.query(RepairRequest).filter(RepairRequest.id == entity_id).first()
            if req:
                return str(req.title)
        elif entity_type == "Department":
            from src.infrastructure.db.models.department import Department
            dept = db.query(Department).filter(Department.id == entity_id).first()
            if dept:
                return f"{str(dept.name)} ({str(dept.code)})"
        elif entity_type == "Employee":
            from src.infrastructure.db.models.employee import Employee
            emp = db.query(Employee).filter(Employee.id == entity_id).first()
            if emp:
                return f"{emp.last_name} {emp.first_name}"
    except Exception:
        pass
    
    return ""


@router.get("/")
def get_audit_log(
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200, description="Количество записей"),
    offset: int = Query(0, ge=0, description="Смещение"),
    entity_type: Optional[str] = Query(None, description="Тип сущности (Asset, User, RepairRequest...)"),
    action: Optional[str] = Query(None, description="Действие (create, update, delete...)"),
    user_id: Optional[int] = Query(None, description="ID пользователя"),
    start_date: Optional[str] = Query(None, description="Начальная дата (ISO format)"),
    end_date: Optional[str] = Query(None, description="Конечная дата (ISO format)"),
    search: Optional[str] = Query(None, description="Поиск по комментарию или diff"),
    current_user=Depends(get_current_admin),
):
    """Получить журнал аудита с фильтрацией (только администратор)."""
    service = AuditService(db)
    data = service.get_all(
        limit=limit,
        offset=offset,
        entity_type=entity_type,
        action=action,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        search=search,
    )
    
    # Обогащаем записи
    for item in data["items"]:
        item["entity_name"] = _get_entity_name(db, item["entity_type"], item["entity_id"])
        item["action_label"] = ACTION_LABELS.get(item["action"], item["action"])
        item["entity_label"] = ENTITY_LABELS.get(item["entity_type"], item["entity_type"])
    
    return data


@router.get("/summary")
def get_audit_summary(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    """Получить сводку по журналу аудита."""
    from src.infrastructure.db.models.audit_log import AuditLog

    # Общее количество записей
    total = db.query(AuditLog).count()

    # По действиям
    from sqlalchemy import func

    actions = (
        db.query(AuditLog.action, func.count(AuditLog.id))
        .group_by(AuditLog.action)
        .all()
    )
    actions_summary = {action: count for action, count in actions}

    # По типам сущностей
    entity_types = (
        db.query(AuditLog.entity_type, func.count(AuditLog.id))
        .group_by(AuditLog.entity_type)
        .all()
    )
    entity_types_summary = {et: count for et, count in entity_types}

    # Последние действия
    last_entries = (
        db.query(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .limit(10)
        .all()
    )
    last_entries_list = [
        {
            "id": e.id,
            "created_at": str(e.created_at) if e.created_at is not None else None,  # type: ignore[union-attr]
            "user_name": e.user.username if e.user else None,
            "entity_type": e.entity_type,
            "entity_id": e.entity_id,
            "action": e.action,
            "diff_summary": e.diff_summary,
        }
        for e in last_entries
    ]

    return {
        "total": total,
        "by_action": actions_summary,
        "by_entity_type": entity_types_summary,
        "last_entries": last_entries_list,
    }


@router.get("/{entity_type}/{entity_id}/history")
def get_entity_history(
    entity_type: str,
    entity_id: int,
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200, description="Количество записей"),
    offset: int = Query(0, ge=0, description="Смещение"),
    current_user=Depends(get_current_user),
):
    """Получить историю изменений конкретной сущности."""
    service = AuditService(db)
    return service.get_history(
        entity_type=entity_type,
        entity_id=entity_id,
        limit=limit,
        offset=offset,
    )


@router.get("/stats/overview")
def get_stats_overview(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    """Общая статистика аудита за последние периоды."""
    from src.infrastructure.db.models.audit_log import AuditLog
    from sqlalchemy import func
    from datetime import datetime, timedelta

    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    # За периоды
    today_count = db.query(func.count(AuditLog.id)).filter(
        AuditLog.created_at >= today_start
    ).scalar() or 0

    week_count = db.query(func.count(AuditLog.id)).filter(
        AuditLog.created_at >= week_ago
    ).scalar() or 0

    month_count = db.query(func.count(AuditLog.id)).filter(
        AuditLog.created_at >= month_ago
    ).scalar() or 0

    # Активные пользователи (за сегодня)
    active_users = (
        db.query(AuditLog.user_id, func.count(AuditLog.user_id).label("actions"))
        .filter(AuditLog.created_at >= today_start)
        .group_by(AuditLog.user_id)
        .order_by(AuditLog.user_id.desc())
        .all()
    )

    top_users = [
        {"user_id": uid, "actions": count} for uid, count in active_users[:10]
    ]

    return {
        "today": today_count,
        "last_7_days": week_count,
        "last_30_days": month_count,
        "top_active_users_today": top_users,
    }
