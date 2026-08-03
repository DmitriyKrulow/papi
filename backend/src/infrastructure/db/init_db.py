from datetime import datetime
from typing import Optional
import os

from sqlalchemy.orm import Session

from src.infrastructure.db.models.user import User
from src.infrastructure.db.models import Base
from src.infrastructure.db.session import SessionLocal, engine
from src.core.value_objects.password_hash import PasswordHash
from src.infrastructure.db.models.asset_type_config import seed_asset_types


# Удаляем papi.db если он был создан ошибочно
_db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), 'papi.db')
if os.path.exists(_db_path):
    try:
        if os.getenv("DATABASE_URL", "").startswith("postgresql"):
            os.remove(_db_path)
            print(f"Removed erroneous papi.db (using PostgreSQL)")
    except:
        pass


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
    _ensure_photo_category_column()
    _ensure_document_links_table()


def _ensure_photo_category_column():
    """Добавляет колонку photo_category в asset_photos, если её нет"""
    from sqlalchemy import text, inspect
    try:
        inspector = inspect(engine)
        columns = [c['name'] for c in inspector.get_columns('asset_photos')]
        if 'photo_category' not in columns:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE asset_photos ADD COLUMN photo_category VARCHAR(50)"))
                conn.commit()
            print("Added photo_category column to asset_photos table")
    except Exception as e:
        print(f"Could not check/add photo_category column: {e}")


def _ensure_document_links_table():
    """Создаёт таблицу document_links, если её нет"""
    from sqlalchemy import text, inspect
    try:
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        if 'document_links' not in table_names:
            from src.infrastructure.db.models.document_link import DocumentLink
            DocumentLink.__table__.create(engine)
            print("Created document_links table")
    except Exception as e:
        print(f"Could not create document_links table: {e}")


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
        else:
            # Check if password_hash is valid
            if not admin.password_hash:
                password_hash = PasswordHash.from_plain_password("admin123")
                admin.password_hash = str(password_hash)
                db.commit()
            else:
                # Try to verify the password to check if hash is valid
                try:
                    password_hash = PasswordHash.from_hash_string(admin.password_hash)
                    # Test with admin123 - if it fails, reset the password
                    if not password_hash.verify("admin123"):
                        password_hash = PasswordHash.from_plain_password("admin123")
                        admin.password_hash = str(password_hash)
                        db.commit()
                except (ValueError, AttributeError):
                    # Invalid hash, reset password
                    password_hash = PasswordHash.from_plain_password("admin123")
                    admin.password_hash = str(password_hash)
                    db.commit()
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
