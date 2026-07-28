import sys
sys.path.insert(0, 'backend')

from src.infrastructure.main import app

# Проверка всех endpoints
from fastapi.testclient import TestClient

client = TestClient(app)

# Проверка root
response = client.get("/")
print(f"Root: {response.status_code}")

# Проверка db-check
response = client.get("/api/db-check")
print(f"DB Check: {response.status_code}, body: {response.json()}")

# Проверка repair endpoints
endpoints = [
    ("GET", "/api/repairs/"),
    ("GET", "/api/repairs/1"),
    ("POST", "/api/repairs/", {"asset_id": 1, "title": "Test", "description": "Test", "priority": "medium"}),
    ("PUT", "/api/repairs/1", {"title": "Updated"}),
    ("PATCH", "/api/repairs/1/status", {"status": "approved"}),
    ("PATCH", "/api/repairs/1/priority", {"priority": "high"}),
    ("DELETE", "/api/repairs/1"),
    ("GET", "/api/repairs/templates/"),
    ("GET", "/api/repairs/templates/1"),
    ("POST", "/api/repairs/templates/", {"name": "Test", "description": "Test"}),
    ("PUT", "/api/repairs/templates/1", {"name": "Updated"}),
    ("DELETE", "/api/repairs/templates/1"),
    ("POST", "/api/repairs/templates/1/apply", {"asset_id": 1}),
    ("GET", "/api/repairs/1/print"),
    ("GET", "/api/repairs/stats"),
    ("POST", "/api/repairs/1/print/pdf"),
]

print("\nTesting endpoints:")
for method, path, *data in endpoints:
    try:
        if data:
            response = client.request(method, path, json=data[0])
        else:
            response = client.request(method, path)
        print(f"  {method} {path}: {response.status_code}")
    except Exception as e:
        print(f"  {method} {path}: ERROR - {e}")
