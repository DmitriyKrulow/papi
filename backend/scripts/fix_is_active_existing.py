import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./papi.db")

if DATABASE_URL.startswith("postgresql"):
    import psycopg2
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    try:
        cur.execute("UPDATE assets SET is_active = TRUE WHERE is_active IS NULL OR is_active = FALSE")
        updated = cur.rowcount
        conn.commit()
        print(f"OK: Updated {updated} assets to is_active=TRUE (PostgreSQL)")
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
        cur.execute("SELECT COUNT(*) FROM assets WHERE is_active IS NULL OR is_active = 0")
        count = cur.fetchone()[0]
        
        cur.execute("UPDATE assets SET is_active = 1 WHERE is_active IS NULL OR is_active = 0")
        updated = cur.rowcount
        conn.commit()
        print(f"OK: Updated {updated} of {count} assets to is_active=1 (SQLite)")
    except Exception as e:
        conn.rollback()
        print(f"ERROR: {e}")
    finally:
        conn.close()
