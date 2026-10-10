# backend/src/presentation/http/dependencies/rfid_auth.py
"""Зависимость для аутентификации RFID-сканера по API-ключу"""
import hashlib
import logging
from typing import Optional

from fastapi import Depends, HTTPException, Header, Request
from sqlalchemy.orm import Session

from src.infrastructure.db.models.rfid_api_key import RfidApiKey
from src.infrastructure.db.session import SessionLocal

logger = logging.getLogger(__name__)


def get_db():
    """Получить сессию БД"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _hash_key(api_key: str) -> str:
    """Хеширует API-ключ для сравнения с хранимым хешем"""
    return hashlib.sha256(api_key.encode()).hexdigest()


async def get_rfid_scanner(
    x_api_key: str = Header(..., alias="X-API-Key", description="API-ключ RFID-сканера"),
    db: Session = Depends(get_db),
) -> dict:
    """
    Зависимость для валидации RFID-сканера.
    
    Ожидаемый заголовок: X-API-Key: rfid_abc123...
    
    Возвращает dict с ключом и информацией о сканере.
    """
    if not x_api_key or not x_api_key.startswith("rfid_"):
        raise HTTPException(
            status_code=401,
            detail="Недействительный API-ключ. Ключ должен начинаться с 'rfid_'"
        )
    
    # Сначала хешируем переданный ключ
    key_hash = _hash_key(x_api_key)
    
    # Ищем ключ по хешу (а не первый попавшийся активный)
    api_key_record = db.query(RfidApiKey).filter(
        RfidApiKey.key_hash == key_hash,
        RfidApiKey.is_active == True
    ).first()
    
    if not api_key_record:
        # Проверяем, существует ли ключ вообще (активный или нет)
        existing_record = db.query(RfidApiKey).filter(
            RfidApiKey.key_hash == key_hash
        ).first()
        
        if existing_record:
            raise HTTPException(
                status_code=401,
                detail="API-ключ деактивирован. Обратитесь к администратору."
            )
        
        raise HTTPException(
            status_code=401,
            detail="API-ключ не найден или неактивен"
        )
    
    # Обновляем время последнего использования
    from datetime import datetime
    api_key_record.last_used_at = datetime.now()
    db.commit()
    
    return {
        "id": api_key_record.id,
        "name": api_key_record.name,
        "key_prefix": api_key_record.key_prefix,
    }
