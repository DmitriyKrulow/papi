import json
import urllib.request

BASE = "http://127.0.0.1:8888"

# 1. Health
r = urllib.request.urlopen(BASE + "/api/reports/health", timeout=5)
print("1. health:", r.read()[:80])

# 2. Login
data = json.dumps({"username": "admin", "password": "admin123"}).encode()
req = urllib.request.Request(BASE + "/api/auth/login", data=data,
                             headers={"Content-Type": "application/json"})
r = urllib.request.urlopen(req, timeout=10)
tok = json.loads(r.read())["access_token"]
print("2. login: OK, token", tok[:25] + "...")

# 3. Authenticated request (users list)
req = urllib.request.Request(BASE + "/api/auth/users",
                             headers={"Authorization": "Bearer " + tok})
r = urllib.request.urlopen(req, timeout=5)
users = json.loads(r.read())
print("3. users:", len(users), "->", users[0]["username"])

# 4. Frontend via nginx
r = urllib.request.urlopen("http://127.0.0.1:80/", timeout=5)
html = r.read()
print("4. frontend:", r.status, "HTML", len(html), "bytes, root div:", b'id="root"' in html)

print("\nALL CHECKS PASSED")
