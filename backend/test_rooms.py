import sys
sys.path.insert(0, '/app')

from src.infrastructure.db.init_db import SessionLocal
from src.infrastructure.db.models.department import Room

db = SessionLocal()
rooms = db.query(Room).filter(Room.is_active == True).all()
print(f'Active rooms: {len(rooms)}')
for r in rooms:
    print(f'  id={r.id}: {r.name} | type={r.room_type}')
db.close()
