import os
import sys
from urllib.parse import quote_plus
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

DATABASE_URL_RAW = os.getenv("DATABASE_URL")
if not DATABASE_URL_RAW:
    print("❌ FATAL: DATABASE_URL environment variable is not set!", file=sys.stderr)
    print("   Create a .env file with: DATABASE_URL=postgresql://user:pass@host:port/dbname", file=sys.stderr)
    sys.exit(1)

if not DATABASE_URL_RAW.startswith("postgresql"):
    print("❌ FATAL: DATABASE_URL must be a PostgreSQL connection string!", file=sys.stderr)
    sys.exit(1)

# URL-encode password to handle special characters (e.g. non-ASCII bytes)
# Format: postgresql://user:pass@host:port/db
if '@' in DATABASE_URL_RAW:
    proto_and_creds, rest = DATABASE_URL_RAW.split('@', 1)
    if '//' in proto_and_creds:
        proto, creds = proto_and_creds.split('//', 1)
        if ':' in creds:
            user, password = creds.split(':', 1)
            encoded_password = quote_plus(password, safe='')
            DATABASE_URL = f"{proto}//{user}:{encoded_password}@{rest}"
        else:
            DATABASE_URL = DATABASE_URL_RAW
    else:
        DATABASE_URL = DATABASE_URL_RAW
else:
    DATABASE_URL = DATABASE_URL_RAW

print(f"🔗 Connected to PostgreSQL: {DATABASE_URL.split('@')[-1]}")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
