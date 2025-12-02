import sqlite3
import json
import requests
import os

DB_NAME = 'leads.db'

def debug_webhooks():
    print(f"🔍 Checking database: {DB_NAME}")
    
    if not os.path.exists(DB_NAME):
        print(f"❌ Database file {DB_NAME} not found!")
        return

    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Check table existence
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='webhook_configs'")
        if not c.fetchone():
            print("❌ Table 'webhook_configs' does not exist!")
            return
            
        # Check webhooks
        print("📋 Listing Webhooks:")
        c.execute('SELECT * FROM webhook_configs')
        webhooks = c.fetchall()
        
        if not webhooks:
            print("⚠️ No webhooks found in database.")
        
        for w in webhooks:
            print(f"\nID: {w['id']}")
            print(f"Name: {w['name']}")
            print(f"URL: {w['url']}")
            print(f"Enabled: {w['enabled']}")
            print(f"Mapping: {w['field_mapping']}")
            
            # Simulate Trigger
            print(f"🚀 Simulating trigger for {w['name']}...")
            
            dummy_data = {
                'first_name': 'Test',
                'last_name': 'User',
                'phone': '5551234567',
                'email': 'test@example.com',
                'state': 'FL',
                'zip_code': '33101',
                'trustedform_cert_url': 'https://cert.trustedform.com/sample',
                'trustedform_token': 'sample_token',
                'ip': '1.2.3.4'
            }
            
            try:
                mapping = json.loads(w['field_mapping']) if w['field_mapping'] else {}
                payload = {}
                
                for app_field, target_field in mapping.items():
                    if not target_field: continue
                    val = dummy_data.get(app_field, '')
                    payload[target_field] = val
                    print(f"   Mapping {app_field} -> {target_field}: {val}")
                
                print(f"   Payload: {json.dumps(payload, indent=2)}")
                
                # Send Request
                print(f"   Sending POST to {w['url']}...")
                try:
                    resp = requests.post(
                        w['url'],
                        json=payload,
                        headers={'Content-Type': 'application/json'},
                        timeout=10
                    )
                    print(f"   ✅ Response Status: {resp.status_code}")
                    print(f"   Response Body: {resp.text[:500]}")
                except Exception as e:
                    print(f"   ❌ Request Failed: {e}")
                    
            except json.JSONDecodeError:
                print("   ❌ Invalid JSON in field_mapping")
            except Exception as e:
                print(f"   ❌ Error preparing payload: {e}")

        conn.close()
        
    except Exception as e:
        print(f"❌ Database Error: {e}")

if __name__ == "__main__":
    debug_webhooks()
