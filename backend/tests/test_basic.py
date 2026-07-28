import sys
sys.path.insert(0, 'backend')

from src.infrastructure.main import app

# Проверка всех endpoints
from fastapi.testclient import TestClient

client = TestClient(app)

print("Testing endpoints:")
print(f"  GET /: {client.get('/').status_code}")
print(f"  GET /api/db-check: {client.get('/api/db-check').status_code}")
print(f"  GET /api/repairs/: {client.get('/api/repairs/').status_code}")
print(f"  GET /api/repairs/stats: {client.get('/api/repairs/stats').status_code}")
print(f"  GET /api/repairs/templates/: {client.get('/api/repairs/templates/').status_code}")

# Попробуем создать repair без asset_id (должен вернуть 422 или 400)
response = client.post('/api/repairs/', json={"asset_id": 1, "title": "Test", "description": "Test"})
print(f"  POST /api/repairs/ (asset_id=1): {response.status_code}, body: {response.json()}")

# Попробуем создать template без данных
response = client.post('/api/repairs/templates/', json={"name": "Test"})
print(f"  POST /api/repairs/templates/ (partial): {response.status_code}, body: {response.json()}")
