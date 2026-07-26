import sys
sys.path.insert(0, 'backend')

print("Importing main module...")

# Эмуляция поведения start.py
from src.infrastructure.main import app, register_routers

print(f"Before register_routers: {len(app.routes)} routes")

register_routers()

print(f"After register_routers: {len(app.routes)} routes")

repair_routes = []
for r in app.routes:
    path = getattr(r, 'path', 'no path')
    if 'repair' in str(path).lower():
        repair_routes.append(path)

print(f"Repair routes: {len(repair_routes)}")
for r in repair_routes:
    print(f"  {r}")
