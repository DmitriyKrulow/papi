"""
Скрипт для генерации миграции Alembic из текущих SQLAlchemy моделей.

Использование:
    python scripts/generate_migration.py "Описание изменений"

Создаёт новую миграцию на основе различий между моделями и текущей БД.
"""
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alembic.config import Config
from alembic.command import revision


def generate_migration(message: str = "migration"):
    """Generate a new Alembic migration from model changes."""
    alembic_cfg = Config(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "alembic.ini"))
    
    print(f"🔍 Generating migration: {message}")
    print(f"📝 This will compare current models with the database schema...")
    
    revision_id = revision(
        config=alembic_cfg,
        message=message,
        autogenerate=True,
        populate_options=True,
    )
    
    print(f"✅ Migration created: {revision_id}")
    print(f"📂 Location: alembic/versions/")
    print(f"📋 Next steps:")
    print(f"   1. Review the generated migration file")
    print(f"   2. Test it: alembic upgrade head")
    print(f"   3. Test rollback: alembic downgrade -1")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        message = " ".join(sys.argv[1:])
    else:
        message = "migration"
    
    generate_migration(message)
