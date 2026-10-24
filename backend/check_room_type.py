import sys
sys.path.insert(0, '/app')

from src.infrastructure.db.init_db import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'rooms' AND column_name = 'room_type'"))
    rows = result.fetchall()
    print(f'Found {len(rows)} rows')
    for row in rows:
        print(f'  Column: {row[0]}')
