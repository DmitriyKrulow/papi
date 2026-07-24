from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from src.infrastructure.db.init_db import get_db
from src.core.value_objects.password_hash import PasswordHash
from src.infrastructure.db.models.user import User
from ..schemas.auth import UserLogin as LoginRequest, UserCreate as RegisterRequest
from ..schemas.auth import UserToken, UserResponse
from ..dependencies.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


@router.post("/register")
def register(user: RegisterRequest, db: Session = Depends(get_db)):
    from src.infrastructure.db.models.user import User
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
        is_active=True,
        department_id=user.department,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"id": new_user.id, "username": new_user.username, "email": new_user.email}


@router.post("/login", response_model=UserToken)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    from src.infrastructure.db.models.user import User
    try:
        user = db.query(User).filter(User.username == credentials.username).first()
        if not user:
            raise HTTPException(status_code=400, detail="Incorrect username or password")
        
        if not user.password_hash:
            raise HTTPException(status_code=400, detail="Password not set for user")
        
        password_hash = PasswordHash.from_hash_string(user.password_hash)
        if not password_hash.verify(credentials.password):
            raise HTTPException(status_code=400, detail="Incorrect username or password")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authentication error: {str(e)}")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires,
    )
    return UserToken(access_token=access_token, token_type="bearer")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/refresh", response_model=UserToken)
def refresh_token(refresh_token: str):
    pass


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
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
