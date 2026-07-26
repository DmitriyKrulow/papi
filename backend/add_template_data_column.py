import sqlite3

conn = sqlite3.connect("papi.db")
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE repair_requests ADD COLUMN template_data TEXT")
    conn.commit()
    print("Column template_data added successfully")
except sqlite3.OperationalError as e:
    print(f"Column may already exist: {e}")
finally:
    conn.close()
