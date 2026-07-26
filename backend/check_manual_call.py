import sys
sys.path.insert(0, 'backend')

print("Checking if register_routers is called...")

# Добавим отладку
import src.infrastructure.main as main_module

# Проверим app
app = main_module.app

print(f"App: {app}")
print(f"Routes: {len(app.routes)}")

# Вызовем register_routers вручную
print("\nCalling register_routers manually...")
main_module.register_routers()
print(f"Routes after call: {len(app.routes)}")

for r in app.routes:
    path = getattr(r, 'path', 'no path')
    if 'repair' in str(path).lower():
        print(f"  REPAIR: {path}")
