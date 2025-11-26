import sqlite3

def check_db():
    try:
        conn = sqlite3.connect('leads.db')
        c = conn.cursor()
        c.execute('SELECT * FROM leads ORDER BY id DESC LIMIT 5')
        leads = c.fetchall()
        conn.close()
        
        print(f"Found {len(leads)} leads:")
        for lead in leads:
            print(lead)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_db()
