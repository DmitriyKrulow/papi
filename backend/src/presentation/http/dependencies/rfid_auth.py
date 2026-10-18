# backend/src/presentation/http/dependencies/rfid_auth.py
"""Зависимости для аутентификации RFID-сканера по API-ключу и пользователю по JWT"""
import hashlib
import logging
from typing import Optional

from fastapi import Depends, HTTPException, Header, Request
from sqlalchemy.orm import Session

from src.infrastructure.db.models.rfid_api_key import RfidApiKey
from src.infrastructure.db.models.user import User
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


def _get_db():
    """Вспомогательная функция для получения сессии БД из запроса"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_optional_user(
    request: Request,
    db: Session = Depends(_get_db),
) -> Optional[User]:
    """
    Попытка извлечь пользователя из Authorization: Bearer <jwt>.
    Возвращает User если токен валиден, None иначе.
    Используется в RFID-эндпоинтах для записи проверяющего.
    """
    try:
        import os
        from dotenv import load_dotenv

        _env_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))))),
            ".env"
        )
        if os.path.exists(_env_path):
            load_dotenv(_env_path)

        from jose import jwt, JWTError

        secret_key = os.getenv("SECRET_KEY")
        if not secret_key:
            return None

        authorization = request.headers.get("authorization", "")
        if not authorization or not authorization.startswith("Bearer "):
            return None

        token = authorization[7:]  # strip "Bearer "

        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        username = payload.get("sub")
        if not username:
            return None

        user = db.query(User).filter(User.username == username).first()
        return user
    except Exception:
        return None
