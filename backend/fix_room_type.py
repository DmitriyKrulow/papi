import sys
sys.path.insert(0, '/app')

from src.infrastructure.db.init_db import engine
from sqlalchemy import text

with engine.connect() as conn:
    conn.execute(text("ALTER TABLE rooms ADD COLUMN IF NOT EXISTS room_type VARCHAR(20) NOT NULL DEFAULT 'room'"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_rooms_room_type ON rooms(room_type)"))
    conn.commit()
    print('Added room_type column')
    
    result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'rooms' AND column_name = 'room_type'"))
    print(f'Found {len(result.fetchall())} rows')
