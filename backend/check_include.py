import sys
sys.path.insert(0, 'backend')

print("Importing main module...")

import src.infrastructure.main as main_module

print(f"app routes after import: {len(main_module.app.routes)}")
print(f"register_routers called: {main_module.register_routers.__name__}")

# Проверим вручную
from src.presentation.http.routers.repairs import router

print(f"Router prefix: {router.prefix}")
print(f"Router routes count: {len(router.routes)}")

main_module.app.include_router(router, prefix="/api")

print(f"After include_router: {len(main_module.app.routes)}")

for r in main_module.app.routes:
    path = getattr(r, 'path', 'no path')
    if 'repair' in str(path).lower():
        print(f"  {path}")
