import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./papi.db")

if DATABASE_URL.startswith("postgresql"):
    import psycopg2
    conn = psycopg2.connect(DATABASE_URL.replace("postgresql://", "postgresql://", 1))
    cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE assets ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_assets_is_active ON assets(is_active)")
        conn.commit()
        print("OK: is_active column added to assets table (PostgreSQL)")
    except Exception as e:
        conn.rollback()
        print(f"ERROR: {e}")
    finally:
        cur.close()
        conn.close()
else:
    db_path = DATABASE_URL.replace("sqlite:///", "")
    if not os.path.exists(db_path):
        print(f"DB not found: {db_path}")
        exit(1)
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    try:
        cur.execute("PRAGMA table_info(assets)")
        columns = [row[1] for row in cur.fetchall()]
        
        if 'is_active' not in columns:
            cur.execute("ALTER TABLE assets ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT 1")
            cur.execute("CREATE INDEX idx_assets_is_active ON assets(is_active)")
            conn.commit()
            print("OK: is_active column added to assets table (SQLite)")
        else:
            print("OK: is_active column already exists")
    except Exception as e:
        conn.rollback()
        print(f"ERROR: {e}")
    finally:
        conn.close()
