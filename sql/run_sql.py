"""
Mamaearth Returns & Growth Intelligence Pipeline
Part 1 -- SQL layer runner

Builds mamaearth.db from schema.sql + seed_data.sql, then runs the report
queries in reports.sql against it. Uses Python's built-in sqlite3 module,
so no separate SQLite install is needed.

Run with:  python sql/run_sql.py
"""

import os
import sqlite3

SQL_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(SQL_DIR, "..", "mamaearth.db")

conn = sqlite3.connect(DB_PATH)

with open(os.path.join(SQL_DIR, "schema.sql")) as f:
    conn.executescript(f.read())
print("Schema created.")

with open(os.path.join(SQL_DIR, "seed_data.sql")) as f:
    conn.executescript(f.read())
conn.commit()
print("Seed data loaded.")

cur = conn.cursor()
for tbl in ["customers", "products", "orders"]:
    cur.execute(f"SELECT COUNT(*) FROM {tbl}")
    print(f"  {tbl}: {cur.fetchone()[0]} rows")

print("\nRunning reports.sql ...\n")
with open(os.path.join(SQL_DIR, "reports.sql")) as f:
    conn.executescript(f.read())
conn.commit()
print("Reports executed. Database saved to:", os.path.abspath(DB_PATH))

conn.close()
