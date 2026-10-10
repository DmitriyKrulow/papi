# backend/src/presentation/http/routers/inventory_schedule.py
"""Расписание проверок — помещения, активы, безопасность, СИЗ, учения"""
import logging
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from src.infrastructure.db.init_db import get_db
from src.infrastructure.db.models.inventory_schedule import InventorySchedule, ReconciliationRecord
from src.infrastructure.db.models.inventory_check import InventoryCheck
from src.infrastructure.db.models.department import Room
from src.infrastructure.db.models.user import User
from src.presentation.http.dependencies.auth import get_current_user, get_current_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/inventory-schedule", tags=["inventory-schedule"])

# ======================== Pydantic models ========================

class ScheduleCreate(BaseModel):
    name: str
    check_category: str = "room"
    check_type: str = "room"
    target_id: Optional[int] = None
    target_type: Optional[str] = "room"
    target_name: Optional[str] = None
    scheduled_date: str
    responsible_id: Optional[int] = None
    comment: str = ""

class ScheduleUpdate(BaseModel):
    scheduled_date: Optional[str] = None
    status: Optional[str] = None
    comment: Optional[str] = None
    responsible_id: Optional[int] = None

class ScheduleBulkUpdate(BaseModel):
    schedule_ids: List[int]
    new_date: str  # ISO format

class AutoGenerateRequest(BaseModel):
    category: str = "room"
    check_type: str = "room"
    target_type: str = "room"
    months: int = 6  # Распределять на N месяцев
    start_date: Optional[str] = None  # ISO format, по умолчанию сегодня

CHECK_TYPE_LABELS = {
    "room": "Проверка помещения",
    "flash_drive": "Проверка флеш-накопителей",
    "token": "Проверка электронных токенов",
    "signature": "Проверка электронных подписей (ЭЦП)",
    "seal_stamp": "Проверка печатей и штампов",
    "vehicle": "Проверка автомобилей",
    "fire_extinguisher": "Проверка огнетушителей",
    "ppe": "Проверка СИЗ",
    "security_drill": "Учения по ИБ",
    "fire_safety": "Учения по пожарной безопасности",
    "employee_appearance": "Проверка внешнего вида сотрудников",
}

# Mapping category -> default check_type for auto-generation
AUTO_GEN_CATEGORIES = [
    {"id": "room", "name": "Помещения", "check_type": "room", "target_type": "room"},
    {"id": "flash_drive", "name": "Флеш-накопители", "check_type": "flash_drive", "target_type": "room"},
    {"id": "token", "name": "Электронные токены", "check_type": "token", "target_type": "room"},
    {"id": "signature", "name": "Электронные подписи (ЭЦП)", "check_type": "signature", "target_type": "room"},
    {"id": "seal_stamp", "name": "Печати и штампы", "check_type": "seal_stamp", "target_type": "room"},
    {"id": "fire_extinguisher", "name": "Огнетушители", "check_type": "fire_extinguisher", "target_type": "room"},
    {"id": "ppe", "name": "СИЗ", "check_type": "ppe", "target_type": "room"},
    {"id": "security_drill", "name": "Учения по ИБ", "check_type": "security_drill", "target_type": "room"},
    {"id": "fire_safety", "name": "Учения по пожарной безопасности", "check_type": "fire_safety", "target_type": "room"},
]

# ======================== Endpoints ========================

@router.get("/calendar")
async def get_calendar(
    month: Optional[int] = Query(None, description="Месяц (1-12)"),
    year: Optional[int] = Query(None, description="Год"),
    check_category: Optional[str] = Query(None, description="Фильтр по категории"),
    check_type: Optional[str] = Query(None, description="Фильтр по типу"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить календарь проверок (доступно всем авторизованным)"""
    query = db.query(InventorySchedule).filter(
        InventorySchedule.status.in_(["scheduled", "in_progress", "overdue"])
    )
    
    if check_category:
        query = query.filter(InventorySchedule.check_category == check_category)
    if check_type:
        query = query.filter(InventorySchedule.check_type == check_type)
    
    if month and year:
        start = datetime(year, month, 1)
        end = datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1)
        query = query.filter(
            InventorySchedule.scheduled_date >= start,
            InventorySchedule.scheduled_date < end,
        )
    elif month:
        current_year = datetime.now().year
        start = datetime(current_year, month, 1)
        end = datetime(current_year + 1, 1, 1) if month == 12 else datetime(current_year, month + 1, 1)
        query = query.filter(
            InventorySchedule.scheduled_date >= start,
            InventorySchedule.scheduled_date < end,
        )
    
    schedules = query.order_by(InventorySchedule.scheduled_date).all()
    
    # Группировка по датам
    calendar = {}
    for s in schedules:
        date_key = s.scheduled_date.strftime("%Y-%m-%d") if s.scheduled_date else "unknown"
        if date_key not in calendar:
            calendar[date_key] = []
        calendar[date_key].append({
            "id": s.id,
            "name": s.name,
            "check_category": s.check_category,
            "check_type": s.check_type,
            "target_type": s.target_type,
            "target_id": s.target_id,
            "target_name": s.target_name,
            "scheduled_date": s.scheduled_date.isoformat() if s.scheduled_date else None,
            "status": s.status,
            "responsible_id": s.responsible_id,
            "responsible_name": f"{s.responsible.full_name}" if s.responsible and s.responsible.full_name else (s.responsible.username if s.responsible else "Не назначен"),
            "comment": s.comment,
        })
    
    return {
        "calendar": calendar,
        "total": len(schedules),
    }


@router.get("/types")
async def get_check_types(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить список всех типов проверок"""
    return {
        "categories": [
            {"id": "room", "name": "Проверка помещений", "types": ["room"]},
            {"id": "it_assets", "name": "IT-активы", "types": ["flash_drive", "token", "signature"]},
            {"id": "security", "name": "Безопасность", "types": ["seal_stamp", "vehicle"]},
            {"id": "safety", "name": "Пожарная безопасность и СИЗ", "types": ["fire_extinguisher", "ppe"]},
            {"id": "training", "name": "Учения и проверки", "types": ["security_drill", "fire_safety", "employee_appearance"]},
        ],
        "type_labels": CHECK_TYPE_LABELS,
    }


@router.post("")
async def create_schedule(
    body: ScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Создать расписание проверки (админ)"""
    try:
        sched_date = datetime.fromisoformat(body.scheduled_date.replace('Z', '+00:00').split('+')[0])
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат даты")
    
    new_schedule = InventorySchedule(
        name=body.name,
        check_category=body.check_category,
        check_type=body.check_type,
        target_id=body.target_id,
        target_type=body.target_type,
        target_name=body.target_name or "",
        scheduled_date=sched_date,
        responsible_id=body.responsible_id,
        comment=body.comment,
    )
    
    db.add(new_schedule)
    db.commit()
    db.refresh(new_schedule)
    
    return {
        "success": True,
        "id": new_schedule.id,
        "name": new_schedule.name,
        "scheduled_date": new_schedule.scheduled_date.isoformat(),
    }


@router.put("/{schedule_id}")
async def update_schedule(
    schedule_id: int,
    body: ScheduleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Обновить расписание (сдвинуть дату, изменить статус)"""
    schedule = db.query(InventorySchedule).filter(
        InventorySchedule.id == schedule_id
    ).first()
    
    if not schedule:
        raise HTTPException(status_code=404, detail="Расписание не найдено")
    
    if body.scheduled_date:
        try:
            schedule.scheduled_date = datetime.fromisoformat(body.scheduled_date.replace('Z', '+00:00').split('+')[0])
        except ValueError:
            raise HTTPException(status_code=400, detail="Неверный формат даты")
    
    if body.status:
        schedule.status = body.status
    
    if body.comment is not None:
        schedule.comment = body.comment
    
    if body.responsible_id is not None:
        schedule.responsible_id = body.responsible_id
    
    db.commit()
    db.refresh(schedule)
    
    return {
        "success": True,
        "id": schedule.id,
        "scheduled_date": schedule.scheduled_date.isoformat(),
        "status": schedule.status,
    }


@router.post("/bulk-update")
async def bulk_update_schedules(
    body: ScheduleBulkUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Массово обновить даты проверок (админ)"""
    try:
        new_date = datetime.fromisoformat(body.new_date.replace('Z', '+00:00').split('+')[0])
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат даты")
    
    updated = 0
    for sched_id in body.schedule_ids:
        schedule = db.query(InventorySchedule).filter(
            InventorySchedule.id == sched_id
        ).first()
        if schedule and schedule.status == "scheduled":
            schedule.scheduled_date = new_date
            updated += 1
    
    db.commit()
    
    return {
        "success": True,
        "updated_count": updated,
        "message": f"Обновлено {updated} проверок",
    }


@router.get("/auto-generate-categories")
async def get_auto_generate_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Получить список категорий для автогенерации (только админ)"""
    return {"categories": AUTO_GEN_CATEGORIES}


@router.post("/auto-generate")
async def auto_generate_schedule(
    body: AutoGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Автоматически сгенерировать график проверок на N месяцев.
    
    Логика:
    - Для категории "room": берёт все помещения и распределяет равномерно
    - Для других категорий: создаёт проверки для всех сотрудников/объектов
    - Пример: 12 помещений за 6 месяцев = 2 помещения в месяц
    """
    # Парсим даты
    start_date = datetime.fromisoformat(body.start_date.replace('Z', '+00:00').split('+')[0]) if body.start_date else datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end_date = start_date + timedelta(days=body.months * 30)
    
    # Определяем целевые объекты
    targets = []
    
    if body.category == "room" or body.check_type == "room":
        # Берём все активные помещения
        rooms = db.query(Room).filter(Room.is_active == True).all()
        targets = [
            {"id": r.id, "name": r.name, "type": "room"}
            for r in rooms
        ]
    else:
        # Для других категорий — проверяем все помещения как объекты
        rooms = db.query(Room).filter(Room.is_active == True).all()
        targets = [
            {"id": r.id, "name": r.name, "type": "room"}
            for r in rooms
        ]
    
    if not targets:
        raise HTTPException(status_code=400, detail="Нет объектов для проверки")
    
    # Проверяем, нет ли уже проверок этого типа
    existing = db.query(InventorySchedule).filter(
        InventorySchedule.check_type == body.check_type,
        InventorySchedule.scheduled_date >= start_date,
    ).all()
    
    if existing:
        # Удаляем старые генерации этого типа
        for ex in existing:
            db.delete(ex)
        db.commit()
    
    # Распределяем цели равномерно по месяцам
    total_months = max(body.months, 1)
    total_targets = len(targets)
    targets_per_month = max(1, total_targets // total_months)
    
    created_count = 0
    current_date = start_date
    
    for month_idx in range(total_months):
        # Определяем границы месяца
        month_start = start_date.replace(month=start_date.month + month_idx) if start_date.month + month_idx <= 12 else start_date.replace(month=start_date.month + month_idx - 12, year=start_date.year + 1)
        month_end = month_start.replace(month=month_start.month + 1) if month_start.month < 12 else month_start.replace(month=1, year=month_start.year + 1)
        
        # Берём порцию целей на этот месяц
        start_idx = month_idx * targets_per_month
        end_idx = min((month_idx + 1) * targets_per_month, total_targets)
        month_targets = targets[start_idx:end_idx]
        
        if not month_targets:
            break
        
        # Распределяем цели по неделям месяца
        days_in_month = (month_end - month_start).days
        days_per_target = max(1, days_in_month // len(month_targets))
        
        for idx, target in enumerate(month_targets):
            sched_date = month_start + timedelta(days=idx * days_per_target + 1)
            
            # Формируем название
            if body.check_type == "room":
                check_name = f"Инвентаризация: {target['name']}"
            else:
                check_name = f"{CHECK_TYPE_LABELS.get(body.check_type, 'Проверка')}: {target['name']}"
            
            new_schedule = InventorySchedule(
                name=check_name,
                check_category=body.category,
                check_type=body.check_type,
                target_id=target["id"],
                target_type=body.target_type,
                target_name=target["name"],
                frequency=body.frequency if hasattr(body, 'frequency') else "semi_annual",
                scheduled_date=sched_date,
                status="scheduled",
                comment=f"Автоматически сгенерировано {datetime.now().strftime('%Y-%m-%d')}",
            )
            
            db.add(new_schedule)
            created_count += 1
    
    db.commit()
    
    return {
        "success": True,
        "created_count": created_count,
        "target_count": total_targets,
        "months": total_months,
        "message": f"Создано {created_count} проверок на {total_months} месяцев",
    }


@router.post("/{schedule_id}/start")
async def start_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Начать проверку по расписанию"""
    schedule = db.query(InventorySchedule).filter(
        InventorySchedule.id == schedule_id,
        InventorySchedule.status == "scheduled"
    ).first()
    
    if not schedule:
        raise HTTPException(status_code=404, detail="Расписание не найдено или уже начато")
    
    schedule.status = "in_progress"
    
    # Создаём инвентаризацию
    inv_check = InventoryCheck(
        name=schedule.name,
        check_date=datetime.now(),
        check_type=schedule.check_type,
        scope_name=schedule.target_name or "",
        status="in_progress",
        total_checked=0,
        found=0,
        missing=0,
        started_at=datetime.now(),
        department_id=schedule.target_id if schedule.target_type == "room" else None,
        creator_id=current_user.id,
        responsible_id=schedule.responsible_id,
    )
    
    db.add(inv_check)
    schedule.inventory_check_id = inv_check.id
    db.commit()
    db.refresh(schedule)
    
    return {
        "success": True,
        "schedule_id": schedule.id,
        "inventory_check_id": inv_check.id,
        "message": f"Проверка '{schedule.name}' начата",
    }


@router.post("/{schedule_id}/complete")
async def complete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Завершить проверку по расписанию"""
    schedule = db.query(InventorySchedule).filter(
        InventorySchedule.id == schedule_id,
        InventorySchedule.status == "in_progress"
    ).first()
    
    if not schedule:
        raise HTTPException(status_code=404, detail="Расписание не найдено или не начато")
    
    schedule.status = "completed"
    schedule.completed_date = datetime.now()
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Проверка '{schedule.name}' завершена",
        "completed_date": schedule.completed_date.isoformat(),
    }


@router.get("/upcoming")
async def get_upcoming(
    days_ahead: int = Query(7, description="Дней вперёд"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить предстоящие проверки"""
    today = datetime.now()
    future = today + timedelta(days=days_ahead)
    
    schedules = db.query(InventorySchedule).filter(
        InventorySchedule.status == "scheduled",
        InventorySchedule.scheduled_date >= today,
        InventorySchedule.scheduled_date <= future,
    ).order_by(InventorySchedule.scheduled_date).all()
    
    return {
        "upcoming": [
            {
                "id": s.id,
                "name": s.name,
                "target_name": s.target_name,
                "scheduled_date": s.scheduled_date.isoformat() if s.scheduled_date else None,
                "days_until": max(0, (s.scheduled_date - today).days),
                "responsible_id": s.responsible_id,
            }
            for s in schedules
        ],
        "total": len(schedules),
    }


@router.get("/stats")
async def get_schedule_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Статистика расписаний"""
    total_scheduled = db.query(func.count(InventorySchedule.id)).filter(
        InventorySchedule.status == "scheduled"
    ).scalar() or 0
    
    total_in_progress = db.query(func.count(InventorySchedule.id)).filter(
        InventorySchedule.status == "in_progress"
    ).scalar() or 0
    
    total_completed = db.query(func.count(InventorySchedule.id)).filter(
        InventorySchedule.status == "completed"
    ).scalar() or 0
    
    total_overdue = db.query(func.count(InventorySchedule.id)).filter(
        InventorySchedule.status == "overdue"
    ).scalar() or 0
    
    # Проверка покрытия помещений за 6 месяцев
    six_months_ago = datetime.now() - timedelta(days=180)
    checked_rooms = db.query(func.count(func.distinct(InventorySchedule.target_id))).filter(
        InventorySchedule.status == "completed",
        InventorySchedule.target_type == "room",
        InventorySchedule.completed_date >= six_months_ago,
    ).scalar() or 0
    
    total_rooms = db.query(func.count(Room.id)).filter(Room.is_active == True).scalar() or 0
    
    return {
        "scheduled": total_scheduled,
        "in_progress": total_in_progress,
        "completed": total_completed,
        "overdue": total_overdue,
        "rooms_checked_last_6_months": checked_rooms,
        "total_rooms": total_rooms,
        "coverage_percent": round(checked_rooms / total_rooms * 100, 1) if total_rooms > 0 else 0,
    }
