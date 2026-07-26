import sys
sys.path.insert(0, 'backend')

print("Starting check...")

# Прочитаем файл и добавим print
with open("backend/src/infrastructure/main.py", "r", encoding="utf-8") as f:
    content = f.read()

# Добавим print перед register_routers
modified = content.replace("register_routers()", "print('About to call register_routers()'); register_routers(); print('register_routers() called')")

with open("backend/src/infrastructure/main_debug.py", "w", encoding="utf-8") as f:
    f.write(modified)

# Импортируем
import src.infrastructure.main_debug as main_debug

print(f"Routes: {len(main_debug.app.routes)}")
