from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from src.infrastructure.auth.jwt import get_jwt_manager, JWTManager
from src.infrastructure.db.unit_of_work import UnitOfWork
from src.presentation.schemas.user import UserResponse
from src.core.domain.roles import UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    uow: UnitOfWork = Depends(),
    jwt_manager: JWTManager = Depends(get_jwt_manager),
) -> UserResponse:
    payload = jwt_manager.verify_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = uow.user_repository.get_by_id(int(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


async def get_current_admin_user(
    current_user: UserResponse = Depends(get_current_active_user),
) -> UserResponse:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


async def get_current_active_user(
    current_user: UserResponse = Depends(get_current_user),
) -> UserResponse:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
