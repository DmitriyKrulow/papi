import sys
sys.path.insert(0, 'backend')

from fastapi import FastAPI
from src.infrastructure.main import app

print(f"Total routes: {len(app.routes)}")

for r in app.routes:
    print(f"  {r.path} - {type(r).__name__}")
