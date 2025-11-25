import sqlite3
import os

DB_NAME = 'leads.db'

if not os.path.exists(DB_NAME):
    print(f"❌ Database {DB_NAME} does not exist!")
    exit(1)

try:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leads'")
    table = cursor.fetchone()
    if table:
        print("✅ Table 'leads' exists!")
    else:
        print("❌ Table 'leads' NOT found!")
    conn.close()
except Exception as e:
    print(f"❌ Error checking database: {e}")
