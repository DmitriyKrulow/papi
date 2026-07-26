import sys
sys.path.insert(0, 'backend')

# Перехватим print
original_print = print
def debug_print(*args, **kwargs):
    msg = ' '.join(str(x) for x in args)
    if 'After' in msg or 'register' in msg.lower():
        original_print("DEBUG:", msg)
    return original_print(*args, **kwargs)

# Модифицируем main.py для отладки
import importlib.util
spec = importlib.util.spec_from_file_location("main_debug", "backend/src/infrastructure/main.py")
module = importlib.util.module_from_spec(spec)

print("Loading module...")
spec.loader.exec_module(module)
print("Module loaded")
print(f"Routes: {len(module.app.routes)}")
