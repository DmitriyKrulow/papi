import pandas as pd
import glob
import os

# Find the uploaded file
files = glob.glob('uploads/inventory/inventory_*.xlsx')
if not files:
    print("No uploaded files found")
    exit(1)

f = sorted(files)[-1]
print(f"File: {f}")
df = pd.read_excel(f)
print(f"Shape: {df.shape}")
print(f"Columns count: {len(df.columns)}")
print()

# Show column names
print("=== Column names (first 25) ===")
for i in range(min(25, len(df.columns))):
    print(f"  [{i}] {df.columns[i]}")
print()

# Show rows 39-45 (data area)
print("=== Rows 39-45 (data area) ===")
for i in range(39, min(46, len(df))):
    print(f"\nRow {i}:")
    for col in df.columns:
        val = df.iloc[i].get(col)
        if pd.notna(val):
            s = str(val)[:60]
            print(f"  {col}: {s}")

print("\n=== Detailed columns 0-3, rows 40-46 ===")
for i in range(40, min(47, len(df))):
    row = df.iloc[i]
    print(f"Row {i}:")
    for c in range(4):
        if c < len(df.columns):
            val = row.get(df.columns[c])
            print(f"  col[{c}] = '{str(val)[:50]}'")
