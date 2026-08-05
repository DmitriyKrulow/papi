from datetime import datetime, timedelta
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from src.infrastructure.db.init_db import get_db
from src.core.value_objects.password_hash import PasswordHash
from src.infrastructure.db.models.user import User
from ..schemas.auth import UserLogin as LoginRequest, UserCreate as RegisterRequest
from ..schemas.auth import UserToken, UserResponse
from ..dependencies.auth import get_current_user
from src.use_cases.auth.login_user import (
    LoginUser,
    BruteForceException,
    AccountPermanentlyLockedException,
)

router = APIRouter(prefix="/auth", tags=["auth"])

SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def _get_client_ip(request: Request) -> str:
    """Извлекает IP адрес клиента из запроса."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


def _create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Создаёт JWT токен."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/register")
def register(user: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    password_hash = PasswordHash.from_plain_password(user.password)
    new_user = User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        password_hash=str(password_hash),
        role="user",
        is_active=False,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = _create_access_token(
        data={"sub": new_user.username, "role": new_user.role},
        expires_delta=access_token_expires,
    )
    return UserToken(access_token=access_token, token_type="bearer")


@router.post("/login", response_model=UserToken)
def login(
    credentials: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    logger = logging.getLogger(__name__)
    ip_address = _get_client_ip(request)
    logger.info(f"[Auth] Login attempt for username: {credentials.username} from IP: {ip_address}")

    try:
        user = LoginUser()(
            username=credentials.username,
            password=credentials.password,
            db=db,
            ip_address=ip_address,
        )
    except BruteForceException as e:
        logger.warning(
            f"[Auth] BruteForce lockout for user: {credentials.username}, "
            f"IP: {ip_address}, remaining: {e.remaining_seconds}s"
        )
        raise HTTPException(
            status_code=429,
            detail=str(e),
            headers={"Retry-After": str(e.remaining_seconds)},
        )
    except AccountPermanentlyLockedException as e:
        logger.warning(
            f"[Auth] Account permanently locked for user: {credentials.username}, IP: {ip_address}"
        )
        raise HTTPException(status_code=403, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authentication error: {str(e)}")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = _create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires,
    )
    logger.info(f"[Auth] Login successful for user: {user.username}, token: {access_token[:50]}...")
    return UserToken(access_token=access_token, token_type="bearer")


@router.post("/refresh", response_model=UserToken)
def refresh_token(refresh_token: str):
    pass


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"[Auth] get_me called for user: {current_user.username}")
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        phone=current_user.phone,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
    )
