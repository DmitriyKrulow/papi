import sys
sys.path.insert(0, 'backend')

from src.infrastructure.main import app, register_routers

register_routers()

for r in app.routes:
    path = getattr(r, 'path', 'no path')
    print(f"{path}")
