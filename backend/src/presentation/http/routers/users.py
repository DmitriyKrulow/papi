from datetime import datetime
from typing import List, Tuple

from fastapi import APIRouter, HTTPException, status
from pydantic import ValidationError

from backend.src.presentation.http.schemas.users import (
    UserCreate,
    UserResponse,
    UserUpdate,
)
from backend.src.infrastructure.db.repositories.user_repository import InMemoryUserRepository

router = APIRouter()


@router.get("/", response_model=List[UserResponse], status_code=status.HTTP_200_OK)
async def get_all_users():
    user_repo = InMemoryUserRepository()
    users = user_repo.get_all()
    return [
        UserResponse(
            id=user.id,
            created_at=user.created_at,
            updated_at=user.updated_at,
            username=user.username,
            email=str(user.email),
            full_name=user.full_name,
            phone=str(user.phone) if user.phone else None,
            department=None,
            role=user.role,
            is_active=user.is_active,
        )
        for user in users
    ]


@router.get("/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_user(user_id: int):
    user_repo = InMemoryUserRepository()
    user = await user_repo.get_by_id(user_id)
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    return UserResponse(
        id=user.id,
        created_at=user.created_at,
        updated_at=user.updated_at,
        username=user.username,
        email=str(user.email),
        full_name=user.full_name,
        phone=str(user.phone) if user.phone else None,
        department=None,
        role=user.role,
        is_active=user.is_active,
    )


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    user_repo = InMemoryUserRepository()
    
    try:
        from backend.src.core.entities.user import User
        from backend.src.core.value_objects.password_hash import PasswordHash
        from backend.src.core.value_objects.email import Email
        
        password_hash = PasswordHash.from_plain_password(user.password)
        email = Email(user.email)
        
        new_user = User(
            username=user.username,
            email=email,
            full_name=user.full_name,
            phone=None,
            password_hash=password_hash,
            role=user.role,
            is_active=user.is_active,
        )
        
        created_user = await user_repo.create(new_user)
        
        return UserResponse(
            id=created_user.id,
            created_at=created_user.created_at,
            updated_at=created_user.updated_at,
            username=created_user.username,
            email=str(created_user.email),
            full_name=created_user.full_name,
            phone=str(created_user.phone) if created_user.phone else None,
            department=None,
            role=created_user.role,
            is_active=created_user.is_active,
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def update_user(user_id: int, user: UserUpdate):
    user_repo = InMemoryUserRepository()
    existing_user = await user_repo.get_by_id(user_id)
    
    if not existing_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    try:
        if user.username is not None:
            existing_user.username = user.username
        if user.email is not None:
            existing_user.change_email(user.email)
        if user.full_name is not None:
            existing_user.full_name = user.full_name
        if user.role is not None:
            existing_user.role = user.role
        if user.is_active is not None:
            if user.is_active:
                existing_user.activate()
            else:
                existing_user.deactivate()
        
        await user_repo.update(existing_user)
        
        return UserResponse(
            id=existing_user.id,
            created_at=existing_user.created_at,
            updated_at=existing_user.updated_at,
            username=existing_user.username,
            email=str(existing_user.email),
            full_name=existing_user.full_name,
            phone=str(existing_user.phone) if existing_user.phone else None,
            department=None,
            role=existing_user.role,
            is_active=existing_user.is_active,
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int):
    user_repo = InMemoryUserRepository()
    await user_repo.delete(user_id)
    return None
