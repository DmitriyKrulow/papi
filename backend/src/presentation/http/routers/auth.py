from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status, Depends, Header

from backend.src.presentation.http.schemas.auth import (
    UserCreate, UserResponse, UserLogin, UserToken,
    ProfileUpdate, ChangePasswordRequest
)
from backend.src.presentation.http.schemas.users import UserResponse as UserResponseBase
from backend.src.core.security.jwt_handler import create_access_token, verify_token
from backend.src.use_cases.auth.register_user import register_user
from backend.src.use_cases.auth.login_user import login_user

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    try:
        new_user = await register_user(user.model_dump())
        return UserResponse(
            id=new_user.id,
            created_at=new_user.created_at,
            updated_at=new_user.updated_at,
            username=new_user.username,
            email=str(new_user.email),
            full_name=new_user.full_name,
            phone=str(new_user.phone) if new_user.phone else None,
            department=None,
            role=new_user.role,
            is_active=new_user.is_active,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=UserToken)
async def login(user: UserLogin):
    try:
        authenticated_user = await login_user(user.username, user.password)
        
        if not authenticated_user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        
        access_token = create_access_token(
            data={"sub": authenticated_user.username, "role": authenticated_user.role},
            expires_delta=timedelta(days=1)
        )
        
        return UserToken(access_token=access_token, token_type="bearer")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.get("/me", response_model=UserResponseBase)
async def get_me(authorization: Optional[str] = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token format")
    
    token = authorization[7:]
    token_data = verify_token(token)
    
    if not token_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    from backend.src.infrastructure.db.repositories.user_repository import InMemoryUserRepository
    user_repo = InMemoryUserRepository()
    user = await user_repo.get_by_username(token_data.username)
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not active")
    
    return UserResponseBase(
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


@router.put("/profile", response_model=UserResponseBase)
async def update_profile(
    profile: ProfileUpdate,
    authorization: Optional[str] = Header(default=None)
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token format")
    
    token = authorization[7:]
    token_data = verify_token(token)
    
    if not token_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    from backend.src.infrastructure.db.repositories.user_repository import InMemoryUserRepository
    from backend.src.core.value_objects.email import Email
    user_repo = InMemoryUserRepository()
    user = await user_repo.get_by_username(token_data.username)
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    if profile.username is not None:
        user.username = profile.username
    if profile.email is not None:
        user.change_email(Email(profile.email))
    if profile.full_name is not None:
        user.full_name = profile.full_name
    if profile.phone is not None:
        from backend.src.core.value_objects.phone import Phone
        user.phone = Phone(profile.phone)
    
    await user_repo.update(user)
    
    return UserResponseBase(
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


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    authorization: Optional[str] = Header(default=None)
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token format")
    
    token = authorization[7:]
    token_data = verify_token(token)
    
    if not token_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    from backend.src.infrastructure.db.repositories.user_repository import InMemoryUserRepository
    from backend.src.core.value_objects.password_hash import PasswordHash
    user_repo = InMemoryUserRepository()
    user = await user_repo.get_by_username(token_data.username)
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    if not user.verify_password(request.old_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid old password")
    
    new_password_hash = PasswordHash.from_plain_password(request.new_password)
    user.change_password(new_password_hash)
    await user_repo.update(user)
    
    return {"message": "Password changed successfully"}
