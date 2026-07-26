import sys
sys.path.insert(0, 'backend')

from fastapi import FastAPI
from src.presentation.http.routers.repairs import router

app = FastAPI()

print(f"Before: {len(app.routes)} routes")

app.include_router(router, prefix="/api")

print(f"After: {len(app.routes)} routes")

for r in app.routes:
    path = getattr(r, 'path', 'no path')
    print(f"  {path}")
