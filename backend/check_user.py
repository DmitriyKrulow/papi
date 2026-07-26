from sqlalchemy import create_engine, text

engine = create_engine("sqlite:///./papi.db")
conn = engine.connect()
result = conn.execute(text("SELECT id, username, email, password_hash, role FROM users WHERE username = 'admin'"))
rows = result.fetchall()
conn.close()
print(rows)
