import sys
sys.path.insert(0, '/app')
from sqlalchemy import text
from src.infrastructure.db.session import SessionLocal

db = SessionLocal()
result = db.execute(text('SELECT column_name FROM information_schema.columns WHERE table_name = \'rooms\' ORDER BY ordinal_position'))
columns = result.fetchall()
print('Rooms columns:')
for col in columns:
    print(f'  - {col[0]}')
db.close()
