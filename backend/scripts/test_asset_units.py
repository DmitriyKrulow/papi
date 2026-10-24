import urllib.request
import json

# Test asset units API
url = 'http://localhost:8000/api/asset-units/'
req = urllib.request.Request(url)
try:
    r = urllib.request.urlopen(req)
    data = json.loads(r.read().decode())
    print(f'Status: {r.status}')
    print(f'Total units: {data["total"]}')
    if data["units"]:
        print(f'First unit: {json.dumps(data["units"][0], indent=2, ensure_ascii=False)}')
    else:
        print('No units found')
except Exception as e:
    print(f'Error: {e}')
