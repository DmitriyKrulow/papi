import sys
import json
import urllib.request

# Test API directly
try:
    req = urllib.request.Request("http://localhost:8888/api/assets/?limit=5&include_hidden=true")
    with urllib.request.urlopen(req, timeout=5) as resp:
        data = json.loads(resp.read().decode())
        print("Status:", resp.status)
        print("Total:", data.get("total"))
        print("Items count:", len(data.get("items", [])))
        if data.get("items"):
            print("First item:", json.dumps(data["items"][0], ensure_ascii=False, indent=2))
except Exception as e:
    print(f"ERROR: {e}")
