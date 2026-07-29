import psycopg2

conn = psycopg2.connect("postgresql://postgres:!6101987Sonya@localhost:5432/papiDB")
c = conn.cursor()

try:
    c.execute("ALTER TABLE assets ADD COLUMN IF NOT EXISTS employee_id INTEGER REFERENCES employees(id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_assets_employee_id ON assets(employee_id)")
    conn.commit()
    print("OK: employee_id column added to assets table")
except Exception as e:
    conn.rollback()
    print(f"ERROR: {e}")
finally:
    conn.close()
