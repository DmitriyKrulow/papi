from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from src.infrastructure.db.models.user import User
from src.infrastructure.db.session import SessionLocal, engine
from src.core.value_objects.password_hash import PasswordHash


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from sqlalchemy import create_engine
    from src.infrastructure.db.models.user import Base

    engine = create_engine("sqlite:///./papi.db", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)


def get_or_create_admin() -> Optional[User]:
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            password_hash = PasswordHash.from_plain_password("admin123")
            admin = User(
                username="admin",
                email="admin@example.com",
                full_name="Администратор",
                phone="+79000000000",
                password_hash=str(password_hash),
                role="admin",
                is_active=True,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
        return admin
    finally:
        db.close()


def create_user(username: str, email: str, password_hash: str, role: str = "user") -> Optional[User]:
    db = SessionLocal()
    try:
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            return None
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            role=role,
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash or ""):
        return None
    return user


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        password_hash = PasswordHash.from_hash_string(hashed_password)
        return password_hash.verify(plain_password)
    except (ValueError, AttributeError):
        return False
