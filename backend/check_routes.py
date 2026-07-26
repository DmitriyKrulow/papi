import sys
sys.path.insert(0, 'backend')

from src.infrastructure.main import app

routes = []
for r in app.routes:
    if hasattr(r, 'path'):
        routes.append(r.path)

repair_routes = [r for r in routes if '/repairs' in r]
for r in sorted(set(repair_routes)):
    print(r)
