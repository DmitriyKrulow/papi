# backend/src/presentation/http/routers/rfid_keys.py
"""Управление RFID API-ключами — административный интерфейс"""
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.infrastructure.db.init_db import get_db
from src.infrastructure.db.models.rfid_api_key import RfidApiKey
from src.infrastructure.db.models.user import User
from src.presentation.http.dependencies.auth import get_current_admin
from src.presentation.http.dependencies.rfid_auth import _hash_key

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/rfid-keys", tags=["rfid-keys"])


@router.get("")
async def list_rfid_keys(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Получить список всех RFID API-ключей"""
    keys = db.query(RfidApiKey).order_by(RfidApiKey.created_at.desc()).all()
    
    result = []
    for key in keys:
        result.append({
            "id": key.id,
            "name": key.name,
            "key_prefix": key.key_prefix,
            "is_active": bool(key.is_active),
            "created_by": key.created_by,
            "created_at": key.created_at.isoformat() if key.created_at else None,
            "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None,
        })
    
    return {"keys": result, "count": len(result)}


@router.post("")
async def create_rfid_key(
    name: str = Query(..., description="Название ключа (напр. 'Сканер цех 1')"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Создать новый RFID API-ключ.
    
    Возвращает полный ключ ОДИН РАЗ — его нужно сохранить!
    """
    # Генерируем ключ
    plain_key = RfidApiKey.generate_key()
    key_hash = _hash_key(plain_key)
    key_prefix = plain_key[:8]
    
    # Создаём запись
    new_key = RfidApiKey(
        name=name,
        key_hash=key_hash,
        key_prefix=key_prefix,
        is_active=True,
        created_by=current_user.id,
    )
    
    db.add(new_key)
    db.commit()
    db.refresh(new_key)
    
    return {
        "message": "API-ключ создан. СОХРАНИТЕ ЕГО — показать больше не сможем!",
        "id": new_key.id,
        "name": new_key.name,
        "api_key": plain_key,  # Показываем ОДИН РАЗ
        "key_prefix": new_key.key_prefix,
        "warning": "Этот ключ больше нигде не отображается. Сохраните его сейчас."
    }


@router.post("/{key_id}/deactivate")
async def deactivate_rfid_key(
    key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Деактивировать RFID API-ключ"""
    key = db.query(RfidApiKey).filter(RfidApiKey.id == key_id).first()
    
    if not key:
        raise HTTPException(status_code=404, detail="API-ключ не найден")
    
    key.is_active = False
    db.commit()
    
    return {"message": f"Ключ '{key.name}' деактивирован"}


@router.delete("/{key_id}")
async def delete_rfid_key(
    key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Удалить RFID API-ключ"""
    key = db.query(RfidApiKey).filter(RfidApiKey.id == key_id).first()
    
    if not key:
        raise HTTPException(status_code=404, detail="API-ключ не найден")
    
    db.delete(key)
    db.commit()
    
    return {"message": f"Ключ '{key.name}' удалён"}


@router.get("/stats")
async def get_rfid_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Статистика по RFID-сканерам"""
    total_keys = db.query(RfidApiKey).count()
    active_keys = db.query(RfidApiKey).filter(RfidApiKey.is_active == True).count()
    
    # Ключи, использовавшиеся за последние 24 часа
    from datetime import timedelta
    yesterday = datetime.now() - timedelta(days=1)
    recently_used = db.query(RfidApiKey).filter(
        RfidApiKey.is_active == True,
        RfidApiKey.last_used_at >= yesterday
    ).count()
    
    return {
        "total_keys": total_keys,
        "active_keys": active_keys,
        "recently_used": recently_used,
        "inactive_keys": total_keys - active_keys
    }
