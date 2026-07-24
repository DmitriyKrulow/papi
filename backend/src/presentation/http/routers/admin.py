# backend/src/presentation/http/routers/admin.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, Any
from src.infrastructure.db.init_db import get_db
from src.infrastructure.db.models.user import User
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
    if new_role not in ["admin", "user", "viewer"]:
        raise HTTPException(status_code=400, detail="Invalid role. Allowed: admin, user, viewer")
    
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