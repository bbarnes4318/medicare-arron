import os
import sqlite3
import requests
import json
from app import app, init_db, DB_NAME

def verify_database_schema():
    print("Verifying database schema...")
    # Ensure DB is initialized
    init_db()
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("PRAGMA table_info(leads)")
    columns = [row[1] for row in c.fetchall()]
    conn.close()
    
    if 'dob' not in columns:
        print("✅ 'dob' column correctly ABSENT from 'leads' table.")
    
    if 'state' in columns and 'zip_code' in columns:
         print("✅ 'state' and 'zip_code' columns exist.")
    else:
         print("❌ Missing 'state' or 'zip_code' columns.")
         return False

    return True

def test_routes():
    print("\nTesting Routes...")
    client = app.test_client()
    
    # Test Root URL (should be landing page)
    response = client.get('/')
    if response.status_code == 200 and b"Medicare Coverage That Fits Your Life" in response.data:
        print("✅ Root URL (/) serves Landing Page.")
    else:
        print(f"❌ Root URL failed. Status: {response.status_code}")
        return False
        
    # Test Login URL (should still exist)
    response = client.get('/login')
    if response.status_code == 200:
        print("✅ Login URL (/login) is accessible.")
    else:
        print(f"❌ Login URL failed. Status: {response.status_code}")
        return False
        
    return True

def test_api_endpoint():
    print("\nTesting /api/submit-lead endpoint...")
    client = app.test_client()
    
    payload = {
        "first_name": "Test",
        "last_name": "User",
        "phone": "555-123-4567",
        "email": "test@example.com",
        "state": "FL",
        "zip_code": "12345",
        "consent": True,
        "trustedform_cert_url": "https://cert.trustedform.com/1234567890",
        "trustedform_token": "token123",
        "trustedform_ping_url": "https://ping.trustedform.com/123"
    }
    
    # Mocking request.remote_addr for the test
    environ = {'REMOTE_ADDR': '127.0.0.1'}
    
    response = client.post('/api/submit-lead', 
                           data=json.dumps(payload),
                           content_type='application/json',
                           environ_base=environ)
    
    print(f"Response Status: {response.status_code}")
    print(f"Response Body: {response.get_json()}")
    
    if response.status_code == 200 and response.get_json().get('success'):
        print("✅ API submission successful.")
        return True
    else:
        print("❌ API submission failed.")
        return False

def verify_data_persistence():
    print("\nVerifying data persistence...")
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT first_name, last_name, phone, email, state, zip_code, disclosure FROM leads ORDER BY id DESC LIMIT 1")
    row = c.fetchone()
    conn.close()
    
    if row:
        print(f"Latest Record: {row}")
        if row[0] == "Test" and row[4] == "FL" and row[5] == "12345" and row[6] == "Yes":
            print("✅ Data persisted correctly.")
            return True
        else:
            print("❌ Data mismatch.")
            return False
    else:
        print("❌ No data found in database.")
        return False

if __name__ == "__main__":
    if verify_database_schema():
        if test_routes():
            if test_api_endpoint():
                verify_data_persistence()
