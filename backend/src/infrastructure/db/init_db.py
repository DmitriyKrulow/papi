from datetime import datetime
from typing import Optional
import os
import logging

from sqlalchemy.orm import Session

from src.infrastructure.db.models.user import User
from src.infrastructure.db.models import Base
from src.infrastructure.db.session import SessionLocal, engine
from src.core.value_objects.password_hash import PasswordHash
from src.infrastructure.db.models.asset_type_config import seed_asset_types

logger = logging.getLogger(__name__)


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
    _ensure_inventory_check_columns()
    _ensure_asset_inventory_columns()


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


def _ensure_inventory_check_columns():
    """Добавляет новые колонки в inventory_checks, если их нет"""
    from sqlalchemy import text, inspect
    try:
        inspector = inspect(engine)
        columns = [c['name'] for c in inspector.get_columns('inventory_checks')]
        if 'check_type' not in columns:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE inventory_checks ADD COLUMN check_type VARCHAR(50) NOT NULL DEFAULT 'full'"))
                conn.execute(text("ALTER TABLE inventory_checks ADD COLUMN scope_id INTEGER"))
                conn.execute(text("ALTER TABLE inventory_checks ADD COLUMN scope_name VARCHAR(255)"))
                conn.execute(text("ALTER TABLE inventory_checks ADD COLUMN created_by INTEGER REFERENCES users(id)"))
                conn.execute(text("ALTER TABLE inventory_checks ADD COLUMN started_at TIMESTAMP"))
                conn.commit()
            print("Added columns to inventory_checks table")
        # Создаём таблицу inventory_check_items, если её нет
        table_names = inspector.get_table_names()
        if 'inventory_check_items' not in table_names:
            from src.infrastructure.db.models.inventory_check_item import InventoryCheckItem
            InventoryCheckItem.__table__.create(engine)
            print("Created inventory_check_items table")
    except Exception as e:
        print(f"Could not check/add inventory check columns: {e}")


def _ensure_asset_inventory_columns():
    """Добавляет поля инвентаризации в assets, если их нет"""
    from sqlalchemy import text, inspect
    try:
        inspector = inspect(engine)
        columns = [c['name'] for c in inspector.get_columns('assets')]
        if 'last_inventory_date' not in columns:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE assets ADD COLUMN last_inventory_date TIMESTAMP"))
                conn.execute(text("ALTER TABLE assets ADD COLUMN last_inventory_by_id INTEGER REFERENCES users(id)"))
                conn.execute(text("ALTER TABLE assets ADD COLUMN last_inventory_confirmed BOOLEAN NOT NULL DEFAULT FALSE"))
                conn.commit()
            print("Added inventory columns to assets table")
    except Exception as e:
        print(f"Could not check/add asset inventory columns: {e}")


def get_or_create_admin() -> Optional[User]:
    """Создаёт администратора по умолчанию, если его нет. НЕ изменяет существующий аккаунт."""
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
            logger.info("[InitDB] Created default admin account (username: admin, password: admin123)")
        # Существующий аккаунт администратора НЕ изменяем — пользователь мог сменить пароль
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
