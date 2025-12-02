import sqlite3

DB_NAME = 'leads.db'

def remove_test_webhook():
    print(f"➖ Removing test webhook from {DB_NAME}...")
    
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        c.execute("DELETE FROM webhook_configs WHERE name = 'Test Ringba'")
        
        conn.commit()
        conn.close()
        print("✅ Test webhook removed.")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    remove_test_webhook()
