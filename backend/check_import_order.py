import sys
sys.path.insert(0, 'backend')

print("Importing main module...")

# Импорт вызовет register_routers()
import src.infrastructure.main as main_module

app = main_module.app

print(f"Routes in app: {len(app.routes)}")

for r in app.routes:
    path = getattr(r, 'path', 'no path')
    if 'repair' in str(path).lower() or 'repairs' in str(path).lower():
        print(f"  REPAIR: {path}")
