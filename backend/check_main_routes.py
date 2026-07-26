import sys
sys.path.insert(0, 'backend')

from src.infrastructure.main import app

print(f"Total routes: {len(app.routes)}")

repair_routes = []
for r in app.routes:
    path = getattr(r, 'path', 'no path')
    if 'repair' in str(path).lower():
        repair_routes.append(path)
        print(f"  {path}")

print(f"\nRepair routes found: {len(repair_routes)}")
