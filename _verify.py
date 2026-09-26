import json
import re
import subprocess
import urllib.request

APP = "http://127.0.0.1:80"
API = "http://127.0.0.1:8888"

ok = True


def check(name, fn):
    global ok
    try:
        print(f"PASS {name}: {fn()}")
    except Exception as e:  # noqa: BLE001
        ok = False
        print(f"FAIL {name}: {e}")


def raw(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    r = urllib.request.urlopen(req, timeout=25)
    return r.status, dict(r.headers), r.read()


def is_html(body):
    return b'<div id="root">' in body


# Real client-side routes, incl. the ones colliding with the "assets" directory.
ROUTES = ["/", "/assets", "/assets/create", "/assets/7", "/assets/7/edit",
          "/dashboard", "/repairs", "/inventory-mobile", "/admin", "/no-such-route"]


def check_routes():
    bad = []
    for path in ROUTES:
        st, _, body = raw(APP + path)
        if st != 200 or not is_html(body):
            bad.append(f"{path}->{st}/{len(body)}")
    if bad:
        raise RuntimeError("not served by SPA shell: " + ", ".join(bad))
    return f"{len(ROUTES)} routes -> index.html"


check("SPA routes + deep links", check_routes)


def check_hashed_asset():
    _, _, html = raw(APP + "/")
    m = re.search(rb'src="(/assets/[^"]+\.js)"', html)
    if not m:
        raise RuntimeError("no hashed bundle referenced in index.html")
    asset = m.group(1).decode()
    st, hdr, body = raw(APP + asset)
    cc = hdr.get("Cache-Control", "")
    if st != 200 or "immutable" not in cc or len(body) < 1000:
        raise RuntimeError(f"{asset}: {st}, cache={cc!r}, {len(body)}b")
    return f"{asset}: {st}, {len(body)} bytes, Cache-Control={cc}"


check("hashed bundle cached immutable", check_hashed_asset)


def check_shell_not_cached():
    st, hdr, _ = raw(APP + "/")
    cc = hdr.get("Cache-Control", "")
    if st != 200 or "no-cache" not in cc:
        raise RuntimeError(f"index.html cache={cc!r}")
    return f"Cache-Control={cc}"


check("index.html revalidated", check_shell_not_cached)

check("health direct", lambda: raw(API + "/api/db-check")[2][:55].decode())
check("health via nginx", lambda: raw(APP + "/api/db-check")[2][:55].decode())


def login():
    data = json.dumps({"username": "admin", "password": "admin123"}).encode()
    req = urllib.request.Request(APP + "/api/auth/login", data=data,
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=30).read())["access_token"]


check("login", lambda: (lambda t: f"token len={len(t)}")(login()))


def authed(path):
    tok = login()
    r = urllib.request.urlopen(urllib.request.Request(
        APP + path, headers={"Authorization": "Bearer " + tok}), timeout=30)
    return f"{r.status}, {len(r.read())} bytes"


check("authed /api/auth/me", lambda: authed("/api/auth/me"))
check("authed /api/assets/", lambda: authed("/api/assets/"))
check("authed /api/repairs/", lambda: authed("/api/repairs/"))


def uploads_writable():
    res = subprocess.run(
        ["docker", "compose", "exec", "-T", "backend", "python", "-c",
         "import getpass;open('uploads/_probe','w').write('x');print('user='+getpass.getuser()+' writable')"],
        capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError((res.stderr or res.stdout).strip()[:200])
    subprocess.run(["docker", "compose", "exec", "-T", "backend", "rm", "-f", "uploads/_probe"],
                   capture_output=True)
    return res.stdout.strip()


check("uploads volume writable", uploads_writable)

print("\nRESULT:", "ALL CHECKS PASSED" if ok else "SOME CHECKS FAILED")
