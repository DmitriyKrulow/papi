# src/presentation/http/routers/users.py
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.infrastructure.db.init_db import get_db
from src.infrastructure.db.models.user import User
from src.core.value_objects.password_hash import PasswordHash
from ..schemas.users import UserCreate, UserResponse, UserUpdate
from ..dependencies.auth import get_current_admin

router = APIRouter(prefix="/users", tags=["users"])
logger = logging.getLogger(__name__)


@router.get("/", response_model=list[UserResponse])
def list_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_admin)):
    """Получает список всех пользователей (только админ)."""
    users = db.query(User).order_by(User.created_at.desc()).all()
    return [
        UserResponse(
            id=u.id,
            username=u.username,
            email=u.email,
            full_name=u.full_name,
            phone=u.phone,
            department=u.department,
            role=u.role,
            is_active=u.is_active,
            allowed_ips=u.allowed_ips,
            created_at=u.created_at,
            updated_at=u.updated_at,
        )
        for u in users
    ]


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin)):
    """Получает пользователя по ID (только админ)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        department=user.department,
        role=user.role,
        is_active=user.is_active,
        allowed_ips=user.allowed_ips,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.post("/", response_model=UserResponse, status_code=201)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Создаёт нового пользователя (только админ)."""
    # Проверяем уникальность
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Создаём пользователя
    password_hash = PasswordHash.from_plain_password(user_data.password or "ChangeMe123!")
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        phone=user_data.phone,
        department=user_data.department,
        role=user_data.role,
        is_active=user_data.is_active,
        allowed_ips=user_data.allowed_ips,
        password_hash=str(password_hash),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logger.info(f"Admin {current_user.username} created user {new_user.username}")

    return UserResponse(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        full_name=new_user.full_name,
        phone=new_user.phone,
        department=new_user.department,
        role=new_user.role,
        is_active=new_user.is_active,
        allowed_ips=new_user.allowed_ips,
        created_at=new_user.created_at,
        updated_at=new_user.updated_at,
    )


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Обновляет данные пользователя (только админ)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Проверяем уникальность username/email при изменении
    if user_data.username and user_data.username != user.username:
        if db.query(User).filter(User.username == user_data.username).first():
            raise HTTPException(status_code=400, detail="Username already taken")
        user.username = user_data.username

    if user_data.email and user_data.email != user.email:
        if db.query(User).filter(User.email == user_data.email).first():
            raise HTTPException(status_code=400, detail="Email already registered")
        user.email = user_data.email

    # Обновляем поля
    if user_data.full_name is not None:
        user.full_name = user_data.full_name
    if user_data.phone is not None:
        user.phone = user_data.phone
    if user_data.department is not None:
        user.department = user_data.department
    if user_data.role is not None:
        user.role = user_data.role
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    if user_data.allowed_ips is not None:
        user.allowed_ips = user_data.allowed_ips

    user.updated_at = datetime.now()
    db.commit()
    db.refresh(user)

    logger.info(f"Admin {current_user.username} updated user {user.username}")

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        department=user.department,
        role=user.role,
        is_active=user.is_active,
        allowed_ips=user.allowed_ips,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Удаляет пользователя (только админ, нельзя удалить себя)."""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    username = user.username
    db.delete(user)
    db.commit()

    logger.info(f"Admin {current_user.username} deleted user {username}")

    return {"message": f"User {username} deleted"}
