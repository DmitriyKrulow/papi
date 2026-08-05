# backend/src/presentation/http/routers/admin.py
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, Any
from datetime import datetime, timedelta
from src.infrastructure.db.init_db import get_db
from src.infrastructure.db.models.user import User
from src.infrastructure.db.models.brute_force_log import BruteForceLog
from src.core.value_objects.password_hash import PasswordHash
from src.presentation.http.dependencies.auth import get_current_admin

router = APIRouter(prefix="/admin", tags=["admin"])


def safe_isoformat(value: Optional[Any]) -> Optional[str]:
    """Безопасно преобразует дату в ISO формат"""
    if value is None:
        return None
    try:
        if hasattr(value, 'isoformat') and callable(getattr(value, 'isoformat')):
            return value.isoformat()
        return str(value)
    except (AttributeError, ValueError):
        return None


def safe_str(value: Optional[Any], default: str = "") -> str:
    """Безопасно преобразует в строку"""
    if value is None:
        return default
    try:
        return str(value)
    except (TypeError, ValueError):
        return default


@router.get("/users")
async def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Получить список всех пользователей (только для админов)"""
    users = db.query(User).all()
    return [
        {
            "id": getattr(u, 'id', None),
            "username": safe_str(getattr(u, 'username', None)),
            "email": safe_str(getattr(u, 'email', None)),
            "full_name": safe_str(getattr(u, 'full_name', None)),
            "phone": safe_str(getattr(u, 'phone', None)),
            "role": safe_str(getattr(u, 'role', None)),
            "is_active": getattr(u, 'is_active', False),
            "allowed_ips": json.loads(u.allowed_ips) if u.allowed_ips else None,
            "created_at": safe_isoformat(getattr(u, 'created_at', None)),
        }
        for u in users
    ]


@router.get("/users/{user_id}")
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Получить пользователя по ID (только для админов)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": getattr(user, 'id', None),
        "username": safe_str(getattr(user, 'username', None)),
        "email": safe_str(getattr(user, 'email', None)),
        "full_name": safe_str(getattr(user, 'full_name', None)),
        "phone": safe_str(getattr(user, 'phone', None)),
        "role": safe_str(getattr(user, 'role', None)),
        "is_active": getattr(user, 'is_active', False),
        "allowed_ips": json.loads(user.allowed_ips) if user.allowed_ips else None,
        "created_at": safe_isoformat(getattr(user, 'created_at', None)),
    }


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Удалить пользователя (только для админов)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Не даем удалить себя - получаем ID через getattr
    user_id_val = getattr(user, 'id', None)
    current_user_id_val = getattr(current_user, 'id', None)
    if user_id_val is not None and current_user_id_val is not None and user_id_val == current_user_id_val:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}


@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    user_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Обновить данные пользователя (только для админов)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user_id != current_user.id:
        if "is_active" in user_data:
            user.is_active = bool(user_data["is_active"])
        if "username" in user_data:
            existing = db.query(User).filter(User.username == user_data["username"], User.id != user_id).first()
            if existing:
                raise HTTPException(status_code=400, detail="Username already taken")
            user.username = user_data["username"]
        if "email" in user_data:
            existing = db.query(User).filter(User.email == user_data["email"], User.id != user_id).first()
            if existing:
                raise HTTPException(status_code=400, detail="Email already taken")
            user.email = user_data["email"]
        if "full_name" in user_data:
            user.full_name = user_data["full_name"]
        if "phone" in user_data:
            user.phone = user_data["phone"]
        if "role" in user_data:
            if user_data["role"] not in ["admin", "user", "responsible"]:
                raise HTTPException(status_code=400, detail="Invalid role")
            user.role = user_data["role"]
        if "allowed_ips" in user_data:
            ips = user_data["allowed_ips"]
            if ips is not None:
                if not isinstance(ips, list):
                    raise HTTPException(status_code=400, detail="allowed_ips must be a list or null")
                for ip in ips:
                    if not isinstance(ip, str) or not ip.strip():
                        raise HTTPException(status_code=400, detail=f"Invalid IP address: {ip}")
                user.allowed_ips = json.dumps(ips, ensure_ascii=False)
            else:
                user.allowed_ips = None
    
    user.updated_at = datetime.now()
    db.commit()
    db.refresh(user)
    
    return {
        "id": getattr(user, 'id', None),
        "username": safe_str(getattr(user, 'username', None)),
        "email": safe_str(getattr(user, 'email', None)),
        "full_name": safe_str(getattr(user, 'full_name', None)),
        "phone": safe_str(getattr(user, 'phone', None)),
        "role": safe_str(getattr(user, 'role', None)),
        "is_active": getattr(user, 'is_active', False),
        "allowed_ips": json.loads(user.allowed_ips) if user.allowed_ips else None,
        "created_at": safe_isoformat(getattr(user, 'created_at', None)),
        "updated_at": safe_isoformat(getattr(user, 'updated_at', None)),
    }


@router.put("/users/{user_id}/password")
async def reset_user_password(
    user_id: int,
    password_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Сбросить пароль пользователя (только для админов)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    new_password = password_data.get("password")
    if not new_password or len(new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    password_hash = PasswordHash.from_plain_password(new_password)
    user.password_hash = str(password_hash)
    user.updated_at = datetime.now()
    db.commit()
    db.refresh(user)
    
    return {
        "message": "Password updated successfully",
        "user_id": getattr(user, 'id', None),
        "username": safe_str(getattr(user, 'username', None)),
    }


@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    role_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Обновить роль пользователя (только для админов)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    new_role = role_data.get("role")
    if new_role not in ["admin", "user", "responsible"]:
        raise HTTPException(status_code=400, detail="Invalid role. Allowed: admin, user, responsible")
    
    user.role = new_role  # type: ignore
    db.commit()
    db.refresh(user)
    
    return {
        "id": getattr(user, 'id', None),
        "username": safe_str(getattr(user, 'username', None)),
        "role": safe_str(getattr(user, 'role', None)),
    }


@router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: int,
    status_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Активировать/деактивировать пользователя (только для админов)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Не даем деактивировать себя
    user_id_val = getattr(user, 'id', None)
    current_user_id_val = getattr(current_user, 'id', None)
    if user_id_val is not None and current_user_id_val is not None and user_id_val == current_user_id_val:
        raise HTTPException(status_code=400, detail="Cannot change your own status")
    
    is_active = status_data.get("is_active")
    if is_active is None:
        raise HTTPException(status_code=400, detail="is_active is required")
    
    user.is_active = bool(is_active)  # type: ignore
    db.commit()
    db.refresh(user)
    
    return {
        "id": getattr(user, 'id', None),
        "username": safe_str(getattr(user, 'username', None)),
        "is_active": getattr(user, 'is_active', False),
    }


# ==================== Brute Force Protection Endpoints ====================


@router.put("/users/{user_id}/allowed-ips")
async def set_user_allowed_ips(
    user_id: int,
    ips_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Установить whitelist IP адресов для пользователя (только администраторы).
    При вводе null или пустого списка — whitelist отключается.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    ips = ips_data.get("ips")  # list of strings or null/empty

    if ips is not None and not isinstance(ips, list):
        raise HTTPException(status_code=400, detail="ips must be a list or null")

    if ips is not None and len(ips) > 0:
        for ip in ips:
            if not isinstance(ip, str) or not ip.strip():
                raise HTTPException(status_code=400, detail=f"Invalid IP address: {ip}")

    # Сохраняем как JSON-строку
    user.allowed_ips = json.dumps(ips, ensure_ascii=False) if ips else None  # type: ignore
    user.updated_at = datetime.now()
    db.commit()
    db.refresh(user)

    return {
        "message": "Allowed IPs updated successfully",
        "user_id": getattr(user, "id", None),
        "username": safe_str(getattr(user, "username", None)),
        "allowed_ips": user.allowed_ips,
    }


@router.get("/brute-force/logs")
async def get_brute_force_logs(
    username: Optional[str] = None,
    ip_address: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Просмотр логов попыток входа (только для админов).
    """
    query = db.query(BruteForceLog)

    if username:
        query = query.filter(BruteForceLog.username == username)
    if ip_address:
        query = query.filter(BruteForceLog.ip_address == ip_address)

    total = query.count()
    logs = (
        query.order_by(BruteForceLog.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "logs": [
            {
                "id": log.id,
                "username": log.username,
                "ip_address": log.ip_address,
                "is_success": bool(log.is_success),
                "created_at": safe_isoformat(log.created_at),
            }
            for log in logs
        ],
    }


@router.get("/brute-force/stats")
async def get_brute_force_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Статистика попыток входа: пользователи с наибольшим числом неудач.
    """
    # Топ-20 пользователей с наибольшим числом неудачных попыток
    stats = (
        db.query(
            BruteForceLog.username,
            func.count("*").label("total_failures"),
            func.max(BruteForceLog.created_at).label("last_failure"),
        )
        .filter(BruteForceLog.is_success == 0)
        .group_by(BruteForceLog.username)
        .order_by(func.count("*").desc())
        .limit(20)
        .all()
    )

    return {
        "top_failures": [
            {
                "username": s.username,
                "total_failures": s.total_failures,
                "last_failure": safe_isoformat(s.last_failure),
            }
            for s in stats
        ],
    }


@router.post("/brute-force/clear-logs")
async def clear_brute_force_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Очистить все логи попыток входа (сбросить счётчики брутфорса).
    Полезно после проверки безопасности.
    """
    db.query(BruteForceLog).delete()
    db.commit()
    return {"message": "Brute force logs cleared successfully"}


@router.post("/users/{user_id}/unlock")
async def unlock_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Разблокировать пользователя: удалить логи брутфорса для данного пользователя.
    Сбрасывает счётчики попыток и lockout-периоды.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    deleted = (
        db.query(BruteForceLog)
        .filter(BruteForceLog.username == user.username)
        .delete()
    )
    db.commit()

    return {
        "message": f"User '{user.username}' unlocked. {deleted} brute force logs cleared.",
        "user_id": getattr(user, "id", None),
        "username": safe_str(getattr(user, "username", None)),
        "deleted_logs": deleted,
    }