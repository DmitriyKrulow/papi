from sqlalchemy import create_engine, text
import os
url = os.environ['DATABASE_URL']
eng = create_engine(url)
conn = eng.connect()

# Проверяем rack'и
result = conn.execute(text('SELECT id, name, warehouse_location_id FROM storage_addresses WHERE level = \'rack\''))
print('RACKS:')
for r in result.fetchall():
    print(f'  id={r[0]}, name={r[1]}, wl_id={r[2]}')

# Проверяем полки для rack 1970
result = conn.execute(text('SELECT id, name, parent_id, warehouse_location_id FROM storage_addresses WHERE level = \'shelf\' AND parent_id = 1970'))
print('SHELVES for rack 1970:')
for s in result.fetchall():
    print(f'  id={s[0]}, name={s[1]}, parent_id={s[2]}, wl_id={s[3]}')

# Проверяем warehouse_locations
result = conn.execute(text('SELECT id, name FROM warehouse_locations'))
print('WAREHOUSE LOCATIONS:')
for w in result.fetchall():
    print(f'  id={w[0]}, name={w[1]}')

conn.close()
