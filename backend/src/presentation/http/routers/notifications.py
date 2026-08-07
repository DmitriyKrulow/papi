# backend/src/presentation/http/routers/notifications.py
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, joinedload

from src.infrastructure.db.init_db import get_db
from src.infrastructure.db.models.notification import Notification
from src.infrastructure.db.models.user import User
from src.presentation.http.dependencies.auth import get_current_user

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("")
async def list_notifications(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    type: Optional[str] = Query(None, description="Filter by type"),
    unread_only: bool = Query(False, description="Show only unread"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить список уведомлений пользователя"""
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
    
    return JSONResponse(content=[{
        "id": n.id,
        "type": n.type,
        "title": n.title,
        "message": n.message,
        "is_read": n.is_read,
        "reference_type": n.reference_type,
        "reference_id": n.reference_id,
        "email_sent": n.email_sent,
        "max_sent": n.max_sent,
        "created_at": n.created_at.isoformat() if n.created_at else None,
    } for n in notifications])


@router.get("/unread-count")
async def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить количество непрочитанных уведомлений"""
    count = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()
    
    return JSONResponse(content={"count": count})


@router.post("/{notification_id:int}/read")
async def mark_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Отметить уведомление как прочитанное"""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Уведомление не найдено")
    
    notification.is_read = True
    notification.read_at = datetime.now()
    db.commit()
    
    return JSONResponse(content={"message": "Уведомление отмечено как прочитанное"})


@router.post("/read-all")
async def mark_all_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Отметить все уведомления как прочитанные"""
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).update({
        "is_read": True,
        "read_at": datetime.now()
    })
    db.commit()
    
    return JSONResponse(content={"message": "Все уведомления отмечены как прочитанные"})
