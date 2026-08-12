# backend/src/presentation/http/routers/notifications.py
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, joinedload

from src.infrastructure.db.init_db import get_db
from src.infrastructure.db.models.notification import Notification
from src.infrastructure.db.models.user import User
from src.infrastructure.db.models.asset import Asset
from src.infrastructure.db.models.repair_request import RepairRequest
from src.presentation.http.dependencies.auth import get_current_user, get_current_admin

router = APIRouter(prefix="/notifications", tags=["notifications"])

# Словарь для перевода типов уведомлений
NOTIFICATION_TYPE_LABELS = {
    "warranty": "Гарантия",
    "maintenance": "Обслуживание",
    "repair_overdue": "Просроченный ремонт",
    "inventory": "Инвентаризация",
    "status_change": "Смена статуса",
    "manual": "Ручное",
    "general": "Общее",
}

NOTIFICATION_TYPE_ICONS = {
    "warranty": "🔔",
    "maintenance": "🔧",
    "repair_overdue": "🛠️",
    "inventory": "📋",
    "status_change": "🔄",
    "manual": "📩",
    "general": "ℹ️",
}


@router.get("")
@router.get("/")
async def list_notifications(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    type: Optional[str] = Query(None, description="Фильтр по типу"),
    unread_only: bool = Query(False, description="Только непрочитанные"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить список уведомлений пользователя."""
    query = db.query(Notification).filter(
        Notification.user_id == current_user.id
    )
    
    if type:
        query = query.filter(Notification.type == type)
    
    if unread_only:
        query = query.filter(Notification.is_read == False)
    
    notifications = query.order_by(
        Notification.created_at.desc()
    ).offset(offset).limit(limit).all()
    
    items = []
    for n in notifications:
        ref_type = str(n.reference_type) if n.reference_type else None  # type: ignore[union-attr]
        created_at = str(n.created_at) if n.created_at else None  # type: ignore[union-attr]
        read_at = str(n.read_at) if n.read_at else None  # type: ignore[union-attr]
        
        item = {
            "id": n.id,
            "type": n.type,
            "type_label": NOTIFICATION_TYPE_LABELS.get(str(n.type), str(n.type)),
            "type_icon": NOTIFICATION_TYPE_ICONS.get(str(n.type), "ℹ️"),
            "title": n.title,
            "message": n.message,
            "is_read": n.is_read,
            "reference_type": ref_type,
            "reference_id": n.reference_id,
            "created_at": created_at,
            "read_at": read_at,
        }
        
        # Добавляем имя сущности
        entity_name = _get_entity_name(db, ref_type, n.reference_id)  # type: ignore[arg-type]
        if entity_name:
            item["entity_name"] = entity_name
        
        items.append(item)
    
    return JSONResponse(content=items)


@router.get("/unread-count")
async def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить количество непрочитанных уведомлений."""
    count = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()
    
    return JSONResponse(content={"count": count})


@router.get("/summary")
async def get_notification_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить сводку по уведомлениям."""
    total = db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).count()
    
    unread = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()
    
    by_type = {}
    from sqlalchemy import func
    types = (
        db.query(Notification.type, func.count(Notification.id))
        .filter(Notification.user_id == current_user.id)
        .group_by(Notification.type)
        .all()
    )
    
    for t, c in types:
        by_type[str(t)] = {"total": c}
    
    return JSONResponse(content={
        "total": total,
        "unread": unread,
        "read": total - unread,
        "by_type": by_type,
    })


@router.post("/{notification_id:int}/read")
async def mark_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Отметить уведомление как прочитанное."""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Уведомление не найдено")
    
    notification.is_read = True  # type: ignore[assignment]
    notification.read_at = datetime.now()  # type: ignore[assignment]
    db.commit()
    
    return JSONResponse(content={"message": "Уведомление отмечено как прочитанное"})


@router.post("/read-all")
async def mark_all_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Отметить все уведомления как прочитанные."""
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).update({
        "is_read": True,
        "read_at": datetime.now()
    })
    db.commit()
    
    return JSONResponse(content={"message": "Все уведомления отмечены как прочитанные"})


@router.delete("/{notification_id:int}")
async def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Удалить уведомление."""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Уведомление не найдено")
    
    db.delete(notification)
    db.commit()
    
    return JSONResponse(content={"message": "Уведомление удалено"})


@router.post("/delete-all-read")
async def delete_all_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Удалить все прочитанные уведомления."""
    deleted = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == True
    ).delete()
    db.commit()
    
    return JSONResponse(content={"message": f"Удалено {deleted} уведомлений"})


@router.get("/types")
async def get_notification_types(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить список типов уведомлений."""
    return JSONResponse(content={
        "types": [
            {"value": k, "label": v, "icon": NOTIFICATION_TYPE_ICONS.get(k, "ℹ️")}
            for k, v in NOTIFICATION_TYPE_LABELS.items()
        ]
    })


@router.post("/generate-auto")
async def generate_auto_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Запустить генерацию автоматических уведомлений (только админ)."""
    from src.core.services.notification_generator import NotificationGenerator
    
    generator = NotificationGenerator(db)
    results = generator.generate_all()
    
    return JSONResponse(content={
        "message": "Автоматические уведомления сгенерированы",
        "results": results,
    })


def _get_entity_name(db: Session, reference_type: Optional[str], reference_id: Optional[int]) -> str:
    """Получает имя сущности по reference_type и reference_id."""
    if not reference_type or not reference_id:
        return ""
    
    try:
        if reference_type == "asset":
            asset = db.query(Asset).filter(Asset.id == reference_id).first()
            if asset:
                return str(asset.name) + " (" + str(asset.inventory_number) + ")"  # type: ignore[union-attr]
        elif reference_type == "repair_request":
            repair = db.query(RepairRequest).filter(RepairRequest.id == reference_id).first()
            if repair:
                return str(repair.title)  # type: ignore[union-attr]
        elif reference_type == "inventory_check":
            return "Инвентаризация #" + str(reference_id)
    except Exception:
        pass
    
    return ""
