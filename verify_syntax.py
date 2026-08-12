import sys

filepath = sys.argv[1]
with open(filepath, 'rb') as f:
    data = f.read()

null_count = data.count(b'\x00')
if null_count > 0:
    clean = data.replace(b'\x00', b'')
    with open(filepath, 'wb') as f:
        f.write(clean)
    print(f"Removed {null_count} null bytes")
else:
    print("No null bytes found")

# Verify syntax
import ast
with open(filepath, 'r', encoding='utf-8') as f:
    ast.parse(f.read())
print("Syntax OK")
