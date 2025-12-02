import sqlite3
import os

DB_NAME = 'leads.db'

def fix_schema():
    print(f"🔧 Fixing database schema for {DB_NAME}...")
    
    if not os.path.exists(DB_NAME):
        print("Database file not found. It will be created.")
        
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        # Create webhook_configs table
        print("Creating webhook_configs table...")
        c.execute('''
            CREATE TABLE IF NOT EXISTS webhook_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                url TEXT,
                method TEXT DEFAULT 'POST',
                headers TEXT,
                field_mapping TEXT,
                enabled INTEGER DEFAULT 1
            )
        ''')
        
        # Verify
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='webhook_configs'")
        if c.fetchone():
            print("✅ Table 'webhook_configs' created successfully.")
        else:
            print("❌ Failed to create table.")
            
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    fix_schema()
