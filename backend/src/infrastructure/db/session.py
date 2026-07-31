import os
import sys
from dotenv import load_dotenv

# Загружаем .env из нескольких возможных мест
_env_candidates = [
    # Относительно этого файла: src/infrastructure/db/session.py -> backend/.env
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), '.env'),
    # Относительно текущего рабочего каталога
    os.path.join(os.getcwd(), '.env'),
    # Относительно src/
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env'),
]

_env_loaded = False
for _env_path in _env_candidates:
    if os.path.exists(_env_path):
        load_dotenv(_env_path)
        _env_loaded = True
        break

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ FATAL: DATABASE_URL environment variable is not set!", file=sys.stderr)
    print("   Create a .env file with: DATABASE_URL=postgresql://user:pass@host:port/dbname", file=sys.stderr)
    sys.exit(1)

if not DATABASE_URL.startswith("postgresql"):
    print("❌ FATAL: DATABASE_URL must be a PostgreSQL connection string!", file=sys.stderr)
    sys.exit(1)

print(f"🔗 Connected to PostgreSQL: {DATABASE_URL.split('@')[-1]}")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
