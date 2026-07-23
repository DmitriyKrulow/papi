from typing import List

from fastapi import APIRouter, HTTPException, Depends
from src.presentation.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserLogin,
    UserToken,
)
from src.infrastructure.db.unit_of_work import UnitOfWork

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
def register_user(user: UserCreate, uow: UnitOfWork = Depends()):
    try:
        uow.user_repository.save(user)
        uow.commit()
        return uow.user_repository.get_by_email(user.email)
    except Exception as e:
        uow.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=UserToken)
def login_user(login: UserLogin, uow: UnitOfWork = Depends()):
    user = uow.user_repository.get_by_username(login.username)
    if not user or not user.verify_password(login.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"access_token": "fake-jwt-token", "token_type": "bearer"}
