"""
Alembic environment configuration for PAPI backend.

This script configures Alembic to work with the PAPI SQLAlchemy models.
It reads the DATABASE_URL from environment variables and sets up the
migration context with proper model imports.
"""
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Add backend directory to path so we can import src modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import SQLAlchemy engine and session
from src.infrastructure.db.session import engine as sqlalchemy_engine
# Import all models to ensure they're registered with Base.metadata
from src.infrastructure.db.models import Base  # noqa: F401

# Alembic Config object
config = context.config

# Override sqlalchemy.url from environment variable if set
db_url = os.getenv("DATABASE_URL")
if db_url:
    config.set_main_option("sqlalchemy.url", db_url)

# Configure logging if alembic.ini has loggers configured
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set metadata for autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() this method will return previously
    generated migrations but now without the actual database connection.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,  # Enables batch mode for SQLite-like operations
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    connectable = sqlalchemy_engine

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,  # Enables batch mode for SQLite-like operations
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
