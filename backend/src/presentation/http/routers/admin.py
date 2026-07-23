from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status, Depends, Header

from backend.src.presentation.http.schemas.auth import (
    UserLogin, UserToken
)
from backend.src.core.security.jwt_handler import verify_token
from backend.src.infrastructure.db.repositories.user_repository import InMemoryUserRepository

router = APIRouter()


@router.get("/admin/users", response_model=List[dict], status_code=status.HTTP_200_OK)
async def get_all_users_admin(authorization: Optional[str] = Header(default=None)):
    """Админ-эндпоинт: получить всех пользователей"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token format")
    
    token = authorization[7:]
    token_data = verify_token(token)
    
    if not token_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    if token_data.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    
    user_repo = InMemoryUserRepository()
    users = user_repo.get_all()
    
    return [
        {
            "id": user.id,
            "username": user.username,
            "email": str(user.email),
            "full_name": user.full_name,
            "phone": str(user.phone) if user.phone else None,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }
        for user in users
    ]


@router.delete("/admin/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_admin(user_id: int, authorization: Optional[str] = Header(default=None)):
    """Админ-эндпоинт: удалить пользователя"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token format")
    
    token = authorization[7:]
    token_data = verify_token(token)
    
    if not token_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    if token_data.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    
    user_repo = InMemoryUserRepository()
    await user_repo.delete(user_id)
    return None


@router.put("/admin/users/{user_id}/role", response_model=dict, status_code=status.HTTP_200_OK)
async def update_user_role(
    user_id: int,
    role: str,
    authorization: Optional[str] = Header(default=None)
):
    """Админ-эндпоинт: изменить роль пользователя"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token format")
    
    token = authorization[7:]
    token_data = verify_token(token)
    
    if not token_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    if token_data.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    
    user_repo = InMemoryUserRepository()
    user = await user_repo.get_by_id(user_id)
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    user.role = role
    await user_repo.update(user)
    
    return {
        "message": "Role updated successfully",
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
    }
