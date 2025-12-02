import sqlite3
import json

DB_NAME = 'leads.db'

def add_test_webhook():
    print(f"➕ Adding test webhook to {DB_NAME}...")
    
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        # Mapping: Phone -> callerid, First Name -> name
        mapping = json.dumps({
            "phone": "callerid",
            "first_name": "name",
            "email": "email"
        })
        
        c.execute('''
            INSERT INTO webhook_configs (name, url, field_mapping, enabled)
            VALUES (?, ?, ?, 1)
        ''', ('Test Ringba', 'https://httpbin.org/post', mapping))
        
        conn.commit()
        conn.close()
        print("✅ Test webhook added.")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    add_test_webhook()
