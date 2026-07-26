import sys
sys.path.insert(0, 'backend')

print("Importing main module...")

# Импорт вызовет register_routers()
import src.infrastructure.main as main_module

app = main_module.app

print(f"Routes in app: {len(app.routes)}")

# Попробуем добавить вручную
from src.presentation.http.routers.repairs import router
print(f"Adding router manually...")
app.include_router(router, prefix="/api")
print(f"Routes after manual add: {len(app.routes)}")

for r in app.routes:
    path = getattr(r, 'path', 'no path')
    if 'repair' in str(path).lower() or 'repairs' in str(path).lower():
        print(f"  REPAIR: {path}")
