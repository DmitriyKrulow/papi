# backend/src/presentation/http/routers/notification_settings.py
"""Настройки уведомлений и массовая рассылка"""
import logging
import os
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.infrastructure.db.init_db import get_db
from src.infrastructure.db.models.user import User
from src.infrastructure.db.models.notification import Notification
from src.infrastructure.db.models.notification_settings import NotificationSettings
from src.infrastructure.db.models.notification_template import NotificationTemplate
from src.presentation.http.dependencies.auth import get_current_user, get_current_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notification-settings", tags=["notification-settings"])


@router.get("/config")
async def get_notification_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить настройки уведомлений"""
    settings = db.query(NotificationSettings).first()
    
    if not settings:
        # Создаём настройки по умолчанию
        settings = NotificationSettings()
        db.add(settings)
        db.commit()
        db.refresh(settings)
    
    return {
        "smtp_host": settings.smtp_host or os.getenv("SMTP_HOST", ""),
        "smtp_port": settings.smtp_port or int(os.getenv("SMTP_PORT", "587")),
        "smtp_user": settings.smtp_user or os.getenv("SMTP_USER", ""),
        "sender_email": settings.sender_email or os.getenv("SENDER_EMAIL", ""),
        "max_api_url": settings.max_api_url or os.getenv("MAX_API_URL", ""),
        "enable_email": bool(settings.enable_email),
        "enable_max": bool(settings.enable_max),
    }


@router.post("/config")
async def save_notification_config(
    config: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Сохранить настройки уведомлений"""
    settings = db.query(NotificationSettings).first()
    
    if not settings:
        settings = NotificationSettings()
        db.add(settings)
    
    settings.smtp_host = config.get("smtp_host")
    settings.smtp_port = config.get("smtp_port", 587)
    settings.smtp_user = config.get("smtp_user")
    settings.smtp_password = config.get("smtp_password")  # Сохраняем пароль
    settings.sender_email = config.get("sender_email")
    settings.max_api_url = config.get("max_api_url")
    settings.max_api_token = config.get("max_api_token")  # Сохраняем токен
    settings.enable_email = 1 if config.get("enable_email") else 0
    settings.enable_max = 1 if config.get("enable_max") else 0
    
    db.commit()
    db.refresh(settings)
    
    return {"message": "Настройки сохранены", "id": settings.id}


@router.get("/templates")
async def get_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить все шаблоны уведомлений"""
    templates = db.query(NotificationTemplate).all()
    return [
        {
            "id": t.id,
            "key": t.key,
            "name": t.name,
            "title_template": t.title_template,
            "message_template": t.message_template,
            "type": t.type,
            "is_active": bool(t.is_active),
        }
        for t in templates
    ]


@router.post("/templates")
async def save_template(
    template: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Сохранить шаблон уведомления"""
    existing = db.query(NotificationTemplate).filter(
        NotificationTemplate.key == template["key"]
    ).first()
    
    if existing:
        existing.name = template["name"]
        existing.title_template = template["title_template"]
        existing.message_template = template["message_template"]
        existing.type = template.get("type", "general")
        existing.is_active = 1 if template.get("is_active", True) else 0
    else:
        existing = NotificationTemplate(
            key=template["key"],
            name=template["name"],
            title_template=template["title_template"],
            message_template=template["message_template"],
            type=template.get("type", "general"),
            is_active=1 if template.get("is_active", True) else 0,
        )
        db.add(existing)
    
    db.commit()
    db.refresh(existing)
    
    return {"message": "Шаблон сохранён", "id": existing.id}


@router.post("/send")
async def send_notification(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Отправить уведомление выбранным пользователям
    payload: {
        "user_ids": [1, 2, 3],  # Список ID пользователей (пусто = всем)
        "title": "Заголовок",
        "message": "Текст сообщения",
        "type": "general"
    }
    """
    from src.core.services.notification_service import NotificationService
    
    user_ids = payload.get("user_ids", [])
    title = payload.get("title", "")
    message = payload.get("message", "")
    notif_type = payload.get("type", "general")
    
    if not title or not message:
        raise HTTPException(status_code=400, detail="Заголовок и текст обязательны")
    
    # Получаем пользователей
    if user_ids:
        users = db.query(User).filter(User.id.in_(user_ids)).all()
    else:
        users = db.query(User).filter(User.is_active == True).all()
    
    if not users:
        raise HTTPException(status_code=400, detail="Пользователи не найдены")
    
    # Отправляем уведомления
    service = NotificationService()
    sent_count = 0
    failed_count = 0
    
    for user in users:
        try:
            # Сохраняем в БД
            notification = Notification(
                user_id=user.id,
                type=notif_type,
                title=title,
                message=message,
                reference_type="manual",
            )
            db.add(notification)
            db.commit()
            
            # Отправляем email
            if user.email:
                service.send_email(user.email, title, message)
            
            # Отправляем через MAX (если есть max_user_id)
            if user.max_user_id:
                service.send_max_notification(user.max_user_id, title, message)
            
            sent_count += 1
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to send notification to user {user.id}: {str(e)}")
            failed_count += 1
    
    return {
        "message": f"Уведомления отправлены: {sent_count} успешно, {failed_count} ошибок",
        "sent": sent_count,
        "failed": failed_count,
    }


@router.get("/users")
async def get_active_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить список активных пользователей (для массовой рассылки)"""
    users = db.query(User).filter(User.is_active == True).order_by(User.username).all()
    
    return [
        {
            "id": u.id,
            "username": u.username,
            "full_name": u.full_name,
            "email": u.email,
            "max_user_id": u.max_user_id,
            "role": u.role,
        }
        for u in users
    ]
