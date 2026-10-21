"""
Database initialization module for PAPI.

This module provides utilities for database initialization and admin user management.
For schema changes, use Alembic migrations instead of manual ALTER TABLE statements.

Usage:
    # Initialize database (creates tables if they don't exist)
    python -c "from src.infrastructure.db.init_db import init_db; init_db()"
    
    # Create admin user
    python -c "from src.infrastructure.db.init_db import get_or_create_admin; print(get_or_create_admin())"
    
    # Generate migration
    python scripts/generate_migration.py "Add new column to assets"
"""
from datetime import datetime
from typing import Generator, Optional
import os
import sys
import logging

from sqlalchemy.orm import Session

from src.infrastructure.db.models.user import User
from src.infrastructure.db.models import Base
from src.infrastructure.db.session import SessionLocal, engine
from src.core.value_objects.password_hash import PasswordHash
from src.infrastructure.db.models.asset_type_config import seed_asset_types

logger = logging.getLogger(__name__)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def run_migrations():
    """
    Применяет все доступные миграции Alembic до последнего коммита.
    Запускается при старте приложения как защитный механизм:
    если на сервере не был выполнен `alembic upgrade head`,
    колонки не будут найдены и запросы упадут с 500.

    Ошибки не выбрасываются — только логируются, чтобы не ломать старт приложения.
    """
    try:
        from alembic.config import Config
        from alembic import command

        # Определяем путь к alembic.ini относительно корня проекта (backend/).
        # Файл init_db.py лежит в src/infrastructure/db/, поэтому поднимаемся на 4 уровня:
        #   хост:      f:/Code/papi/backend/src/infrastructure/db/...  -> backend/
        #   контейнер: /app/src/infrastructure/db/...                  -> /app/
        this_file = os.path.abspath(__file__)
        candidates = [
            # backend/ (4 уровня вверх от src/infrastructure/db/init_db.py)
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(this_file)))), "alembic.ini"),
            # запасной вариант на случай иной структуры каталогов
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(this_file))), "alembic.ini"),
            "/app/alembic.ini",
        ]
        alembic_cfg_path = next((p for p in candidates if os.path.exists(p)), None)

        if not alembic_cfg_path:
            logger.warning("Alembic config not found (tried %s) — пропускаем миграции", candidates)
            return

        alembic_cfg = Config(alembic_cfg_path)
        # env.py уже переопределяет sqlalchemy.url из DATABASE_URL,
        # но убедимся что это работает и здесь:
        alembic_cfg.set_main_option("sqlalchemy.url", str(engine.url))

        logger.info("Running alembic migrations...")
        command.upgrade(alembic_cfg, "head")
        logger.info("Alembic migrations applied successfully")
    except Exception as e:
        logger.error("Failed to run alembic migrations: %s", e, exc_info=True)


def init_db():
    """
    Initialize database tables.
    
    NOTE: This should only be used for initial setup. For schema changes,
    use Alembic migrations:
        python scripts/generate_migration.py "Your migration message"
        alembic upgrade head
    """
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified via Alembic-compatible init")


def get_or_create_admin() -> User:
    """
    Create or return existing admin user.
    
    Default admin credentials:
        username: admin
        email: admin@papi.local
        password: admin123
    """
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.role == "admin").first()
        if admin:
            logger.info(f"Admin user already exists: {admin.username}")
            return admin
        
        admin = User(
            username="admin",
            email="admin@papi.local",
            full_name="Administrator",
            role="admin",
            is_active=True,
            password_hash=PasswordHash.hash("admin123"),
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        logger.info("Admin user created successfully")
        return admin
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create admin user: {e}")
        raise
    finally:
        db.close()


