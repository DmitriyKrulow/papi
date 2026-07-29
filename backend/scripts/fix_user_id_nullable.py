import psycopg2

conn = psycopg2.connect("postgresql://postgres:!6101987Sonya@localhost:5432/papiDB")
cur = conn.cursor()
cur.execute("ALTER TABLE employees ALTER COLUMN user_id DROP NOT NULL")
conn.commit()
cur.execute("SELECT column_name, is_nullable FROM information_schema.columns WHERE table_name = 'employees' AND column_name = 'user_id'")
print(cur.fetchone())
cur.close()
conn.close()
print("Done: user_id is now nullable")
