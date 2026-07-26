import sys
sys.path.insert(0, 'backend')

# Запустим uvicorn в фоне
import uvicorn
from threading import Thread
import time

def run_server():
    uvicorn.run(
        "src.infrastructure.main:app",
        host="0.0.0.0",
        port=8001,
        reload=False,
        log_level="error"
    )

# Запускаем сервер в отдельном потоке
server_thread = Thread(target=run_server, daemon=True)
server_thread.start()

# Ждем инициализации
time.sleep(2)

# Проверяем маршруты через HTTP
import requests
try:
    response = requests.get("http://localhost:8001/openapi.json", timeout=5)
    openapi = response.json()
    
    paths = openapi.get('paths', {})
    repair_paths = [p for p in paths.keys() if 'repair' in p.lower()]
    
    print(f"Total paths: {len(paths)}")
    print(f"Repair paths: {len(repair_paths)}")
    for p in repair_paths:
        print(f"  {p}")
        
except Exception as e:
    print(f"Error: {e}")
