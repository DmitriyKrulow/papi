import re
import subprocess

# Read the password that the backend currently expects from .env
text = open('.env', encoding='utf-8').read()
pw = re.search(r'^POSTGRES_PASSWORD=(.*)$', text, re.M).group(1).strip()
user = re.search(r'^POSTGRES_USER=(.*)$', text, re.M).group(1).strip()

# Local socket inside the container uses trust auth, so this works regardless
# of the password stored in the existing volume.
sql = f"ALTER USER \"{user}\" WITH PASSWORD '{pw.replace(chr(39), chr(39)*2)}';"
res = subprocess.run(
    ['docker', 'compose', 'exec', '-T', 'db', 'psql', '-U', user, '-d', 'postgres', '-c', sql],
    capture_output=True, text=True,
)
print("returncode:", res.returncode)
print("stdout:", res.stdout.strip())
print("stderr:", res.stderr.strip()[:300])
print("user:", user, "password length:", len(pw))
