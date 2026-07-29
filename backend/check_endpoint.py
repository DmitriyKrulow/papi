import requests
try:
    resp = requests.get('http://localhost:8000/api/admin/placement-assignments/rooms', headers={'Authorization': 'Bearer test'}, timeout=5)
    print(f'Status: {resp.status_code}')
    print(f'Response: {resp.text[:500]}')
except Exception as e:
    print(f'Error: {e}')
