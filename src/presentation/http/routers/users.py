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

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
def get_current_user(uow: UnitOfWork = Depends()):
    user = uow.user_repository.get_by_id(1)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/me", response_model=UserResponse)
def update_current_user(user: UserUpdate, uow: UnitOfWork = Depends()):
    try:
        uow.user_repository.save(user)
        uow.commit()
        return uow.user_repository.get_by_id(1)
    except Exception as e:
        uow.rollback()
        raise HTTPException(status_code=400, detail=str(e))
