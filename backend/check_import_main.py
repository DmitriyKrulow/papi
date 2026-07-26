import sys
sys.path.insert(0, 'backend')

# Добавим отладку
print("Before import")

import src.infrastructure.main as main_module

print("After import")
print(f"Module: {main_module}")
print(f"Module file: {main_module.__file__}")

# Проверим app
app = main_module.app
print(f"App routes: {len(app.routes)}")

# Проверим, что register_routers существует
print(f"register_routers exists: {hasattr(main_module, 'register_routers')}")
