from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from src.infrastructure.db.models.user import User
from src.infrastructure.db.session import SessionLocal

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"[Auth] get_current_user called")
    logger.info(f"[Auth] Token from header: {token[:50]}..." if token else "NO TOKEN")
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token or token == "NO TOKEN":
        logger.error("[Auth] NO TOKEN RECEIVED - This is the root cause!")
        raise credentials_exception
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logger.info(f"[Auth] Payload: {payload}")
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError as e:
        logger.error(f"[Auth] JWTError: {e}")
        raise credentials_exception
    user = db.query(User).filter(User.username == username).first()
    logger.info(f"[Auth] User: {user}")
    if user is None:
        raise credentials_exception
    return user


def get_current_admin(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    user = get_current_user(db, token)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
