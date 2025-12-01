"""
Proxy Access Portal - A secure web application for agents to access Decodo residential proxy service
"""
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import requests
import os
import json
import uuid
import re
import subprocess
import sys
import sqlite3
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    print("Warning: psycopg2 not installed. PostgreSQL support disabled.")
from datetime import datetime, timedelta
# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import zipfile
import os
import shutil


# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, skip .env loading

# Google Sheets integration
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GOOGLE_SHEETS_AVAILABLE = True
except ImportError:
    GOOGLE_SHEETS_AVAILABLE = False
    print("Warning: Google Sheets libraries not installed. Form data will not be saved to Sheets.")

app = Flask(__name__)
# Use a consistent secret key for all workers
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

@app.template_filter('from_json')
def from_json_filter(s):
    """Custom filter to parse JSON string in templates"""
    if not s:
        return {}
    try:
        return json.loads(s)
    except:
        return {}


# Proxy configuration for Decodo residential proxies
# Use environment variables for production deployment
PROXY_CONFIG = {
    'host': os.environ.get('PROXY_HOST', 'us.decodo.com'),
    'port': int(os.environ.get('PROXY_PORT', '10000')),
    'username': os.environ.get('PROXY_USERNAME'),
    'password': os.environ.get('PROXY_PASSWORD'),
    'country': 'United States',
    'city': 'Random',
    'rotation': 'Rotating',
    'ttl': 'N/A'
}

# User database (in production, use a real database)
# Password: Each agent can have their own password
# Generate 100 agent logins automatically
USERS = {}

# Create 100 agent logins (agent1 through agent100)
for i in range(1, 101):
    USERS[f'agent{i}'] = generate_password_hash('password123')

# Add admin account
USERS['admin'] = generate_password_hash('admin123')

# Google Sheets Configuration
# Set these environment variables:
# GOOGLE_SHEETS_CREDENTIALS_JSON - JSON string of service account credentials
# GOOGLE_SHEETS_SPREADSHEET_ID - ID of the Google Spreadsheet
# GOOGLE_SHEETS_WORKSHEET_NAME - Name of the worksheet (default: "Form Submissions")
GOOGLE_SHEETS_CREDENTIALS_JSON = os.environ.get('GOOGLE_SHEETS_CREDENTIALS_JSON', '')
GOOGLE_SHEETS_SPREADSHEET_ID = os.environ.get('GOOGLE_SHEETS_SPREADSHEET_ID', '')
GOOGLE_SHEETS_WORKSHEET_NAME = os.environ.get('GOOGLE_SHEETS_WORKSHEET_NAME', 'medicare-form')

# Landing page form submission URL
LANDING_PAGE_URL = os.environ.get('LANDING_PAGE_URL', 'https://lowinsurancecost.com')
LANDING_PAGE_FORM_ENDPOINT = os.environ.get('LANDING_PAGE_FORM_ENDPOINT', '')  # e.g., '/submit' or '/form-handler'

# Database Configuration
# Use absolute path to ensure we're writing to the expected location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, 'leads.db')
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    """Get database connection (Postgres or SQLite)"""
    if DATABASE_URL and POSTGRES_AVAILABLE:
        try:
            conn = psycopg2.connect(DATABASE_URL)
            return conn
        except Exception as e:
            print(f"❌ Error connecting to PostgreSQL: {e}")
            # Fallback to SQLite if Postgres fails (e.g. locally without env var)
            return sqlite3.connect(DB_NAME)
    else:
        return sqlite3.connect(DB_NAME)

def init_db():
    """Initialize the database (Postgres or SQLite)"""
    try:
        if DATABASE_URL and POSTGRES_AVAILABLE:
            print("🔄 Initializing PostgreSQL database...")
            conn = psycopg2.connect(DATABASE_URL)
            c = conn.cursor()
            # Postgres syntax
            c.execute('''
                CREATE TABLE IF NOT EXISTS leads (
                    id SERIAL PRIMARY KEY,
                    timestamp TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    phone TEXT,
                    email TEXT,
                    address TEXT,
                    city TEXT,
                    state TEXT,
                    zip_code TEXT,
                    trustedform_cert_url TEXT,
                    trustedform_token TEXT,
                    trustedform_ping_url TEXT,
                    source TEXT
                );
                CREATE TABLE IF NOT EXISTS webhook_configs (
                    id SERIAL PRIMARY KEY,
                    name TEXT,
                    url TEXT,
                    method TEXT DEFAULT 'POST',
                    headers TEXT,
                    field_mapping TEXT,
                    enabled BOOLEAN DEFAULT TRUE
                );
            ''')
            conn.commit()
            conn.close()
            print("✅ PostgreSQL database initialized successfully")
        else:
            print(f"🔄 Initializing SQLite database at {DB_NAME}...")
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute('''
                CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    phone TEXT,
                    email TEXT,
                    address TEXT,
                    city TEXT,
                    state TEXT,
                    zip_code TEXT,
                    trustedform_cert_url TEXT,
                    trustedform_token TEXT,
                    trustedform_ping_url TEXT,
                    source TEXT
                );
                CREATE TABLE IF NOT EXISTS webhook_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    url TEXT,
                    method TEXT DEFAULT 'POST',
                    headers TEXT,
                    field_mapping TEXT,
                    enabled INTEGER DEFAULT 1
                );
            ''')
            conn.commit()
            conn.close()
            print(f"✅ Database initialized successfully at {DB_NAME}")
            
            # Verify table exists
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leads'")
            if c.fetchone():
                print("✅ Table 'leads' verified to exist")
            else:
                print("❌ CRITICAL: Table 'leads' does not exist after initialization!")
            conn.close()
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR initializing database: {e}")

    # Attempt schema migrations (add missing columns if table exists)
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # List of columns to check/add
        columns_to_add = [
            ('disclosure', 'TEXT'),
            ('trustedform_cert_url', 'TEXT'),
            ('trustedform_token', 'TEXT'),
            ('trustedform_ping_url', 'TEXT'),
            ('source', 'TEXT')
        ]
        
        for col_name, col_type in columns_to_add:
            try:
                if DATABASE_URL and POSTGRES_AVAILABLE:
                    c.execute(f"ALTER TABLE leads ADD COLUMN IF NOT EXISTS {col_name} {col_type}")
                else:
                    # SQLite doesn't support IF NOT EXISTS in ADD COLUMN
                    # So we try and ignore error
                    try:
                        c.execute(f"ALTER TABLE leads ADD COLUMN {col_name} {col_type}")
                    except sqlite3.OperationalError:
                        pass # Column likely exists
            except Exception as e:
                print(f"Migration warning for {col_name}: {e}")
                
        conn.commit()
        conn.close()
        print("✅ Database schema migration checks completed")
    except Exception as e:
        print(f"❌ Error during schema migration: {e}")

# Initialize DB on module load (for Gunicorn)
try:
    init_db()
except Exception as e:
    print(f"Warning: Could not initialize database on module load: {e}")

@app.route('/debug-db')
def debug_db():
    """Debug endpoint to check database status"""
    try:
        if not os.path.exists(DB_NAME):
            return jsonify({'status': 'error', 'message': f'Database file not found at {DB_NAME}'})
            
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        # Check table
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leads'")
        table_exists = c.fetchone() is not None
        
        # Count rows
        row_count = 0
        if table_exists:
            c.execute("SELECT COUNT(*) FROM leads")
            row_count = c.fetchone()[0]
            
        conn.close()
        
        return jsonify({
            'status': 'ok',
            'db_path': DB_NAME,
            'table_exists': table_exists,
            'row_count': row_count,
            'file_size': os.path.getsize(DB_NAME),
            'permissions': oct(os.stat(DB_NAME).st_mode)[-3:]
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)})

def save_lead_to_db(data):
    """Save lead data to database (Postgres or SQLite)"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Use generic placeholder %s for Postgres, ? for SQLite
        # But psycopg2 supports %s and sqlite3 supports ?
        # We need to handle this difference
        
        is_postgres = (DATABASE_URL is not None) and POSTGRES_AVAILABLE
        placeholder = '%s' if is_postgres else '?'
        
        query = f'''
            INSERT INTO leads (
                timestamp, first_name, last_name, phone, email, 
                address, city, state, zip_code, trustedform_cert_url, 
                trustedform_token, trustedform_ping_url, source, disclosure
            ) VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
        '''
        
        if is_postgres:
            query += " RETURNING id"
            c.execute(query, (
                timestamp,
                data.get('first_name', ''),
                data.get('last_name', ''),
                data.get('phone', ''),
                data.get('email', ''), # Kept for schema compatibility
                data.get('address', ''),
                data.get('city', ''),
                data.get('state', ''),
                data.get('zip_code', ''),
                data.get('trustedform_cert_url', ''),
                data.get('trustedform_token', ''),
                data.get('trustedform_ping_url', ''),
                data.get('source', 'Extension Capture'), # Use provided source or default
                data.get('disclosure', 'No')
            ))
            lead_id = c.fetchone()[0]
        else:
            c.execute(query, (
                timestamp,
                data.get('first_name', ''),
                data.get('last_name', ''),
                data.get('phone', ''),
                data.get('email', ''), # Kept for schema compatibility
                data.get('address', ''),
                data.get('city', ''),
                data.get('state', ''),
                data.get('zip_code', ''),
                data.get('trustedform_cert_url', ''),
                data.get('trustedform_token', ''),
                data.get('trustedform_ping_url', ''),
                data.get('source', 'Extension Capture'), # Use provided source or default
                data.get('disclosure', 'No')
            ))
            lead_id = c.lastrowid
        
        conn.commit()
        conn.close()
        return lead_id, timestamp
    except Exception as e:
        print(f"❌ Error saving to database: {e}")
        return None, None

def login_required(f):
    """Decorator to require login for certain routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_proxy_dict():
    """Generate proxy dictionary for requests library"""
    try:
        # Only create proxy dict when actually needed
        if not PROXY_CONFIG.get('username') or not PROXY_CONFIG.get('password'):
            return {}
        
        proxy_url = f"http://{PROXY_CONFIG['username']}:{PROXY_CONFIG['password']}@{PROXY_CONFIG['host']}:{PROXY_CONFIG['port']}"
        return {
            'http': proxy_url,
            'https': proxy_url
        }
    except Exception as e:
        # Return empty dict if proxy config fails
        return {}

def generate_trustedform_certificate():
    """Generate a TrustedForm certificate URL - DEPRECATED: Don't use fake certificates"""
    # NOTE: TrustedForm certificates MUST be generated by TrustedForm JavaScript on the client side
    # We should NOT generate fake certificates server-side
    # This function is kept for backwards compatibility but should not be used
    return None

def retain_trustedform_certificate(cert_url, lead_data):
    """
    Retain a TrustedForm certificate using the API.
    """
    if not cert_url or 'trustedform.com' not in cert_url:
        print(f"⚠️ Invalid TrustedForm URL for retention: {cert_url}")
        return False

    # API Key from trustedForm.txt
    api_key = "bb8cc20c4c2842a49d49012233d60477"
    
    try:
        print(f"🔒 Retaining TrustedForm Certificate: {cert_url}")
        
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        # Prepare match_lead data
        match_lead = {}
        if lead_data.get('email'):
            match_lead['email'] = lead_data.get('email')
        if lead_data.get('phone'):
            match_lead['phone'] = lead_data.get('phone')
            
        payload = {
            "match_lead": match_lead,
            "retain": {
                "reference": str(lead_data.get('id', '')),
                "vendor": "lowinsurancecost.com" 
            }
        }
        
        # The cert_url IS the endpoint to post to
        response = requests.post(
            cert_url,
            json=payload,
            headers=headers,
            auth=('API', api_key),
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✅ TrustedForm Certificate Retained Successfully!")
            return True
        else:
            print(f"❌ Failed to retain certificate. Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error retaining TrustedForm certificate: {e}")
        return False

def save_to_google_sheets(form_data, trustedform_url, proxy_ip=None, submission_status=None, trustedform_token=None, trustedform_ping_url=None):
    """Save form submission data to Google Sheets"""
    if not GOOGLE_SHEETS_AVAILABLE:
        print("Google Sheets libraries not installed. Skipping save.")
        return False
    
    if not GOOGLE_SHEETS_CREDENTIALS_JSON:
        print("ERROR: GOOGLE_SHEETS_CREDENTIALS_JSON not set in environment variables!")
        return False
    
    if not GOOGLE_SHEETS_SPREADSHEET_ID:
        print("ERROR: GOOGLE_SHEETS_SPREADSHEET_ID not set in environment variables!")
        return False
    
    try:
        # Parse credentials from JSON string
        # Handle case where JSON might be stored with escaped quotes or as string
        json_str = GOOGLE_SHEETS_CREDENTIALS_JSON.strip()
        
        # Debug: Log what we received (first 200 chars only for security)
        print(f"DEBUG: GOOGLE_SHEETS_CREDENTIALS_JSON length: {len(json_str)}")
        print(f"DEBUG: First 200 chars: {json_str[:200]}")
        print(f"DEBUG: Starts with {{: {json_str.startswith('{')}")
        
        # Check if it's the placeholder
        if json_str == "SET_IN_DIGITALOCEAN_DASHBOARD" or not json_str or json_str == '""':
            print("ERROR: GOOGLE_SHEETS_CREDENTIALS_JSON is not set or is placeholder!")
            return False
        
        # Remove surrounding quotes if present (DigitalOcean might add them)
        if json_str.startswith('"') and json_str.endswith('"'):
            json_str = json_str[1:-1]
            # Unescape quotes
            json_str = json_str.replace('\\"', '"')
        
        # Handle double-escaped JSON (DigitalOcean sometimes double-escapes)
        if json_str.startswith('\\"'):
            json_str = json_str[2:-2] if json_str.endswith('\\"') else json_str[2:]
        
        # IMPORTANT: Parse JSON FIRST, then fix newlines in the parsed dict
        # If we replace \\n with \n before parsing, it breaks JSON syntax
        # JSON requires \\n (double backslash) to be valid
        try:
            creds_dict = json.loads(json_str)
        except json.JSONDecodeError as je:
            print(f"ERROR: JSON parse failed: {je}")
            print(f"DEBUG: JSON string (first 500 chars): {json_str[:500]}")
            # Try decoding with unicode_escape if first attempt failed
            try:
                import codecs
                json_str_decoded = codecs.decode(json_str, 'unicode_escape')
                creds_dict = json.loads(json_str_decoded)
            except Exception as e2:
                print(f"ERROR: Second parse attempt also failed: {e2}")
                return False
        
        # NOW replace escaped newlines in the private_key value
        # After JSON parsing, \\n becomes a string with literal backslash-n
        if 'private_key' in creds_dict:
            # Replace literal \n (backslash-n) with actual newline
            creds_dict['private_key'] = creds_dict['private_key'].replace('\\n', '\n')
        
        # Validate required fields
        required_fields = ['type', 'project_id', 'private_key', 'client_email']
        missing_fields = [field for field in required_fields if field not in creds_dict]
        if missing_fields:
            print(f"ERROR: Missing required fields in credentials: {missing_fields}")
            return False
        
        creds = Credentials.from_service_account_info(creds_dict)
        scoped_creds = creds.with_scopes([
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ])
        
        # Open the spreadsheet
        client = gspread.authorize(scoped_creds)
        spreadsheet = client.open_by_key(GOOGLE_SHEETS_SPREADSHEET_ID)
        
        # Get or create worksheet
        try:
            worksheet = spreadsheet.worksheet(GOOGLE_SHEETS_WORKSHEET_NAME)
            # Check if headers exist (check if first row is empty or doesn't match expected headers)
            first_row = worksheet.row_values(1)
            expected_headers = [
                'Timestamp', 'Agent', 'State', 'Zip Code', 'First Name', 'Last Name', 
                'Phone', 'Email', 'Disclosure (TCPA Consent)', 'LeadID Token', 
                'TrustedForm Certificate URL', 'TrustedForm Token', 'TrustedForm Ping URL', 
                'Proxy IP', 'Submission Status', 'Landing Page Response'
            ]
            # If first row is empty or doesn't match, add headers
            if not first_row or first_row[0] != 'Timestamp':
                worksheet.insert_row(expected_headers, 1)
                print("Added headers to existing worksheet")
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title=GOOGLE_SHEETS_WORKSHEET_NAME, rows=1000, cols=20)
            # Add headers if new worksheet
            headers = [
                'Timestamp', 'Agent', 'State', 'Zip Code', 'First Name', 'Last Name', 
                'Phone', 'Email', 'Disclosure (TCPA Consent)', 'LeadID Token', 
                'TrustedForm Certificate URL', 'TrustedForm Token', 'TrustedForm Ping URL', 
                'Proxy IP', 'Submission Status', 'Landing Page Response'
            ]
            worksheet.append_row(headers)
        
        # Prepare row data matching landing page form structure
        row_data = [
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            session.get('username', 'Unknown'),
            form_data.get('state', ''),
            form_data.get('zip_code', ''),
            form_data.get('first_name', ''),
            form_data.get('last_name', ''),
            form_data.get('phone', ''),
            form_data.get('email', ''),
            'Yes' if form_data.get('disclosure') else 'No',
            '',  # LeadID token (will be added from submission if available)
            trustedform_url,
            trustedform_token or trustedform_url,  # TrustedForm token (use cert URL if token not provided)
            trustedform_ping_url or '',  # TrustedForm ping URL
            proxy_ip or 'N/A',
            submission_status or 'Unknown',
            ''  # Landing page response will be added if available
        ]
        
        # Append row
        worksheet.append_row(row_data)
        print(f"Successfully saved form submission to Google Sheets")
        return True
        
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON format in GOOGLE_SHEETS_CREDENTIALS_JSON: {e}")
        print(f"JSON length: {len(GOOGLE_SHEETS_CREDENTIALS_JSON)}")
        print(f"JSON preview (first 100 chars): {GOOGLE_SHEETS_CREDENTIALS_JSON[:100]}")
        return False
    except Exception as e:
        import traceback
        error_msg = str(e)
        print(f"Error saving to Google Sheets: {error_msg}")
        print(f"Traceback: {traceback.format_exc()}")
        
        # Provide helpful error messages
        if "No key could be detected" in error_msg or "private_key" in error_msg.lower():
            print("ERROR: Google Sheets credentials JSON is missing or invalid.")
            print("Please check:")
            print("1. GOOGLE_SHEETS_CREDENTIALS_JSON is set in DigitalOcean environment variables")
            print("2. JSON is valid and on a single line")
            print("3. Private key has \\n escaped as \\\\n (double backslash)")
        elif "WorksheetNotFound" in error_msg:
            print(f"Note: Worksheet '{GOOGLE_SHEETS_WORKSHEET_NAME}' will be created automatically")
        elif "Permission denied" in error_msg.lower() or "403" in error_msg:
            print("ERROR: Service account doesn't have access to the spreadsheet.")
            print("Please share the spreadsheet with the service account email.")
        
        return False

def trigger_webhooks(lead_data):
    """Trigger configured webhooks for a new lead"""
    try:
        conn = get_db_connection()
        
        if DATABASE_URL and POSTGRES_AVAILABLE:
            c = conn.cursor(cursor_factory=RealDictCursor)
        else:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
        c.execute('SELECT * FROM webhook_configs WHERE enabled = 1 OR enabled = TRUE')
        webhooks = c.fetchall()
        conn.close()
        
        print(f"🚀 Triggering {len(webhooks)} webhooks...")
        
        for webhook in webhooks:
            try:
                # Parse mapping
                mapping = json.loads(webhook['field_mapping']) if webhook['field_mapping'] else {}
                
                # Prepare payload
                payload = {}
                
                # Handle Name Splitting logic if requested in mapping
                # We assume the mapping might have special keys or we handle it here
                # But the user said "Make it possible to breakup the 'Name' into first name and last name"
                # The lead_data already has first_name and last_name usually
                
                for app_field, target_field in mapping.items():
                    if not target_field: continue
                    
                    value = lead_data.get(app_field, '')
                    
                    # Special handling if needed
                    payload[target_field] = value
                
                print(f"   ➡️ Sending to {webhook['name']} ({webhook['url']})...")
                
                # Send Request
                try:
                    resp = requests.post(
                        webhook['url'],
                        json=payload, # Or data=payload depending on requirement, usually JSON is safer default
                        headers={'Content-Type': 'application/json'},
                        timeout=10
                    )
                    print(f"   ✅ Webhook {webhook['name']} response: {resp.status_code}")
                    if resp.status_code >= 400:
                        print(f"   ⚠️ Webhook Error Body: {resp.text[:500]}")
                except Exception as e:
                    print(f"   ❌ Webhook {webhook['name']} failed to send: {e}")
                    
            except Exception as e:
                print(f"   ❌ Error processing webhook {webhook['name']}: {e}")
                
    except Exception as e:
        print(f"❌ Error triggering webhooks: {e}")

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def submit_form_through_proxy(form_data, trustedform_url):
    """Submit form to landing page through Decodo residential proxy"""
    proxies = get_proxy_dict()
    
    if not proxies:
        return {
            'success': False,
            'error': 'Proxy configuration not available'
        }
    
    try:
        # Determine the form submission endpoint
        # Target the real URL as requested by the user
        submit_url = "https://lowinsurancecost.com/"
        
        # Prepare form data matching the exact payload structure provided
        # The target expects multipart/form-data
        payload = {
            'state': form_data.get('state', ''),
            'zip_code': form_data.get('zip_code', ''),
            'first_name': form_data.get('first_name', ''),
            'last_name': form_data.get('last_name', ''),
            'phone': form_data.get('phone', ''),
            'email': form_data.get('email', ''),
            'leadid_token': str(uuid.uuid4()).upper(), # Generate if not provided
            'ip': '99.38.204.249', # This will likely be overwritten by the script seeing the proxy IP, but we send it anyway
        }
        
        # Handle TrustedForm
        if trustedform_url:
            payload['xxTrustedFormCertUrl'] = trustedform_url
            payload['xxTrustedFormToken'] = form_data.get('trustedform_token', '')
            payload['xxTrustedFormPingUrl'] = form_data.get('trustedform_ping_url', '')
        
        # Headers - mimic the browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Origin': 'https://lowinsurancecost.com',
            'Referer': 'https://lowinsurancecost.com/',
        }
        
        print(f"DEBUG: Submitting to {submit_url}")
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session = requests.Session()
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        # Use session.post with 'data' to send multipart/form-data
        response = session.post(
            submit_url,
            data=payload,
            headers=headers,
            proxies=proxies,
            timeout=30, # Increased timeout for retries
            verify=False # Google scripts sometimes have cert issues with proxies
        )
        
        print(f"DEBUG: Response Status: {response.status_code}")
        
        # Google Scripts often return 302 Redirect on success, or 200 with HTML
        if response.status_code in [200, 201, 302]:
            proxy_ip = 'Unknown'
            try:
                if proxies and proxies.get('http'):
                    proxy_ip = proxies.get('http').split('@')[-1].split(':')[0]
            except Exception as e:
                print(f"Warning: Could not parse proxy IP: {e}")
            
            return {
                'success': True,
                'proxy_ip': proxy_ip
            }
        else:
            print(f"WARNING: Got response but status code is {response.status_code}")
            print(f"Response text (first 500 chars): {response.text[:500]}")
            return {
                'success': False,
                'error': f'Form submission returned status code {response.status_code}. Response: {response.text[:200]}',
                'status_code': response.status_code,
                'proxy_ip': None
            }
        
    except requests.exceptions.RequestException as e:
        error_msg = str(e)
        print(f"DEBUG: Request Exception: {error_msg}")
        
        # Provide helpful error messages for common proxy issues
        if '402' in error_msg or 'Payment Required' in error_msg:
            error_msg = 'Proxy Error: 402 Payment Required. Your Decodo proxy account may need payment or the credentials may be expired.'
        elif 'ProxyError' in error_msg or 'proxy' in error_msg.lower():
            error_msg = f'Proxy Connection Error: {error_msg}. Please verify your Decodo proxy credentials.'
        elif 'SSLError' in error_msg:
             error_msg = f'SSL Error connecting to Google Script: {error_msg}. Retries failed.'
        
        return {
            'success': False,
            'error': error_msg,
            'proxy_ip': None
        }



def find_binary(name, start_paths=['/app', '/workspace', '/usr']):
    """Recursively search for a binary in the given paths"""
    print(f"🔍 Searching for {name} in {start_paths}...")
    for start_path in start_paths:
        if not os.path.exists(start_path):
            continue
        for root, dirs, files in os.walk(start_path):
            if name in files:
                full_path = os.path.join(root, name)
                # Check if executable
                if os.access(full_path, os.X_OK):
                    print(f"✅ Found {name} at: {full_path}")
                    return full_path
    print(f"❌ Could not find {name}")
    return None

def install_chrome_at_runtime():
    """Download and install Chrome and Chromedriver to /tmp at runtime"""
    print("⬇️ Starting Runtime Chrome Installation...")
    install_dir = "/tmp/chrome-linux64"
    chrome_exe = os.path.join(install_dir, "chrome-linux64", "chrome")
    driver_exe = os.path.join(install_dir, "chromedriver-linux64", "chromedriver")
    
    if os.path.exists(chrome_exe) and os.path.exists(driver_exe):
        print(f"✅ Chrome already installed at {chrome_exe}")
        return chrome_exe, driver_exe

    os.makedirs(install_dir, exist_ok=True)
    
    # URLs for Chrome for Testing (Stable)
    chrome_url = "https://storage.googleapis.com/chrome-for-testing-public/125.0.6422.141/linux64/chrome-linux64.zip"
    driver_url = "https://storage.googleapis.com/chrome-for-testing-public/125.0.6422.141/linux64/chromedriver-linux64.zip"
    
    try:
        # Download Chrome
        print(f"⬇️ Downloading Chrome from {chrome_url}...")
        r = requests.get(chrome_url)
        with open(os.path.join(install_dir, "chrome.zip"), "wb") as f:
            f.write(r.content)
        
        print("📦 Extracting Chrome...")
        with zipfile.ZipFile(os.path.join(install_dir, "chrome.zip"), 'r') as zip_ref:
            zip_ref.extractall(install_dir)
            
        # Download Chromedriver
        print(f"⬇️ Downloading Chromedriver from {driver_url}...")
        r = requests.get(driver_url)
        with open(os.path.join(install_dir, "driver.zip"), "wb") as f:
            f.write(r.content)
            
        print("📦 Extracting Chromedriver...")
        with zipfile.ZipFile(os.path.join(install_dir, "driver.zip"), 'r') as zip_ref:
            zip_ref.extractall(install_dir)
            
        # Make everything in the install dir executable to be safe (includes crashpad_handler)
        print("🔐 Setting permissions...")
        for root, dirs, files in os.walk(install_dir):
            for f in files:
                os.chmod(os.path.join(root, f), 0o755)
        
        print(f"✅ Runtime Installation Complete!")
        print(f"Chrome: {chrome_exe}")
        print(f"Driver: {driver_exe}")
        return chrome_exe, driver_exe
        
    except Exception as e:
        print(f"❌ Runtime Installation Failed: {e}")
        return None, None

def submit_lead_via_browser(form_data):
    """Submit lead by launching a headless browser on the server"""
    print("🚀 Launching Headless Chrome for submission... [VERSION v9 - RUNTIME DOWNLOADER]")
    
    chrome_bin = None
    chromedriver_path = None

    # 1. Try Env Vars
    if os.environ.get('GOOGLE_CHROME_BIN') and os.path.exists(os.environ.get('GOOGLE_CHROME_BIN')):
        chrome_bin = os.environ.get('GOOGLE_CHROME_BIN')
        print(f"DEBUG: Found Chrome via Env Var: {chrome_bin}")
    
    if os.environ.get('CHROMEDRIVER_PATH') and os.path.exists(os.environ.get('CHROMEDRIVER_PATH')):
        chromedriver_path = os.environ.get('CHROMEDRIVER_PATH')
        print(f"DEBUG: Found Chromedriver via Env Var: {chromedriver_path}")

    # 2. Try Filesystem Search
    if not chrome_bin:
        print("DEBUG: Searching filesystem for Chrome...")
        chrome_bin = find_binary('google-chrome') or find_binary('chromium') or find_binary('chromium-browser')

    if not chromedriver_path:
        print("DEBUG: Searching filesystem for Chromedriver...")
        chromedriver_path = find_binary('chromedriver')

    # 3. Runtime Download (Fallback)
    if not chrome_bin or not chromedriver_path:
        print("⚠️ Chrome/Driver not found. Attempting runtime download...")
        dl_chrome, dl_driver = install_chrome_at_runtime()
        if dl_chrome and dl_driver:
            chrome_bin = dl_chrome
            chromedriver_path = dl_driver

    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--remote-allow-origins=*")
    chrome_options.add_argument(f"--user-data-dir={os.path.join('/tmp', 'chrome-user-data-' + str(uuid.uuid4()))}")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # STRICT PROXY ENFORCEMENT
    # We add this even if we use the extension, as a fallback/reinforcement
    if PROXY_CONFIG.get('host') and PROXY_CONFIG.get('port'):
        proxy_server = f"{PROXY_CONFIG['host']}:{PROXY_CONFIG['port']}"
        print(f"DEBUG: Enforcing proxy via command line: {proxy_server}")
        chrome_options.add_argument(f"--proxy-server=http://{proxy_server}")
    
    if chrome_bin:
        print(f"DEBUG: Setting Chrome binary location to: {chrome_bin}")
        chrome_options.binary_location = chrome_bin
        
        # 🔍 DIAGNOSTIC: Check for missing dependencies
        print("🔍 Running Chrome Diagnostic...")
        try:
            # 1. Check permissions
            print(f"DEBUG: Permissions for {chrome_bin}: {oct(os.stat(chrome_bin).st_mode)[-3:]}")
            
            # 2. Run ldd to see missing libraries
            print("DEBUG: Checking libraries (ldd)...")
            ldd_out = subprocess.check_output(['ldd', chrome_bin], stderr=subprocess.STDOUT).decode('utf-8')
            for line in ldd_out.split('\n'):
                if 'not found' in line:
                    print(f"❌ MISSING LIB: {line.strip()}")
            
            # 3. Try running it directly (MATCHING SELENIUM FLAGS)
            print("DEBUG: Attempting dry run of Chrome (with flags)...")
            dry_run_cmd = [
                chrome_bin, 
                '--headless=new', 
                '--no-sandbox', 
                '--disable-dev-shm-usage', 
                '--disable-gpu', 
                '--remote-allow-origins=*',
                '--dump-dom', 
                'https://example.com'
            ]
            proc = subprocess.Popen(
                dry_run_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = proc.communicate(timeout=10)
            print(f"DEBUG: Dry Run Exit Code: {proc.returncode}")
            if proc.returncode != 0:
                print(f"❌ Dry Run STDERR: {stderr.decode('utf-8')}")
            else:
                print("✅ Dry Run Success!")
                
        except Exception as e:
            print(f"⚠️ Diagnostic failed: {e}")

    else:
        print("❌ CRITICAL: Could not find Chrome binary anywhere (Env, Search, or Download)!")
    
    # Configure Proxy if available
    if PROXY_CONFIG.get('username'):
        # Create a dynamic extension for proxy authentication
        # This is required because Headless Chrome doesn't support auth popups
        plugin_file = 'proxy_auth_plugin.zip'
        
        manifest_json = """
        {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Chrome Proxy",
            "permissions": [
                "proxy",
                "tabs",
                "unlimitedStorage",
                "storage",
                "<all_urls>",
                "webRequest",
                "webRequestBlocking"
            ],
            "background": {
                "scripts": ["background.js"]
            },
            "minimum_chrome_version":"22.0.0"
        }
        """

        background_js = """
        var config = {
                mode: "fixed_servers",
                rules: {
                  singleProxy: {
                    scheme: "http",
                    host: "%s",
                    port: parseInt(%s)
                  },
                  bypassList: ["localhost"]
                }
              };

        chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

        function callbackFn(details) {
            return {
                authCredentials: {
                    username: "%s",
                    password: "%s"
                }
            };
        }

        chrome.webRequest.onAuthRequired.addListener(
                    callbackFn,
                    {urls: ["<all_urls>"]},
                    ['blocking']
        );
        """ % (PROXY_CONFIG['host'], PROXY_CONFIG['port'], PROXY_CONFIG['username'], PROXY_CONFIG['password'])

        with zipfile.ZipFile(plugin_file, 'w') as zp:
            zp.writestr("manifest.json", manifest_json)
            zp.writestr("background.js", background_js)
            
        chrome_options.add_extension(plugin_file)
        print(f"✅ Added Proxy Auth Extension: {PROXY_CONFIG['host']}:{PROXY_CONFIG['port']}")

    driver = None
    try:
        # Debug: Check Chrome version
        try:
            chrome_ver = subprocess.check_output(['google-chrome', '--version'], stderr=subprocess.STDOUT).decode('utf-8').strip()
            print(f"DEBUG: Chrome Version: {chrome_ver}")
        except Exception as e:
            print(f"DEBUG: Could not get Chrome version: {e}")
            # Try google-chrome-stable
            try:
                chrome_ver = subprocess.check_output(['google-chrome-stable', '--version'], stderr=subprocess.STDOUT).decode('utf-8').strip()
                print(f"DEBUG: Chrome Stable Version: {chrome_ver}")
            except:
                pass
            # Try chromium
            try:
                chrome_ver = subprocess.check_output(['chromium', '--version'], stderr=subprocess.STDOUT).decode('utf-8').strip()
                print(f"DEBUG: Chromium Version: {chrome_ver}")
            except:
                pass
            # Try chromium-browser (Ubuntu/Buildpack)
            try:
                chrome_ver = subprocess.check_output(['chromium-browser', '--version'], stderr=subprocess.STDOUT).decode('utf-8').strip()
                print(f"DEBUG: Chromium Browser Version: {chrome_ver}")
            except:
                pass

        # Initialize Driver
        print("🔧 Installing/Finding Chromedriver...")
        try:
            if chromedriver_path and os.path.exists(chromedriver_path):
                 print(f"DEBUG: Using Chromedriver at {chromedriver_path}")
                 service = Service(executable_path=chromedriver_path)
            else:
                 print("⚠️ Chromedriver path not found in logic, trying ChromeDriverManager...")
                 service = Service(ChromeDriverManager().install())
        except Exception as e:
            print(f"⚠️ ChromeDriverManager failed: {e}")
            service = Service()

        # Binary location is already set at the top of the function

        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # 1. Go to Landing Page
        target_url = "https://lowinsurancecost.com/"
        print(f"🌐 Navigating to {target_url}...")
        driver.get(target_url)
        print(f"DEBUG: Page Title: {driver.title}")
        print(f"DEBUG: Current URL: {driver.current_url}")
        
        # 2. Fill Form
        print("📝 Filling form...")
        # Increase timeout to 30 seconds for slow Angular loading
        wait = WebDriverWait(driver, 30)
        
        # Wait for body to be present first
        print("DEBUG: Waiting for DOM body...")
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        print("DEBUG: DOM body present. Waiting for form fields...")
        
        # Map fields (Use IDs as per page.txt)
        fields = {
            'state': form_data.get('state'),
            'zip_code': form_data.get('zip_code'),
            'first_name': form_data.get('first_name'),
            'last_name': form_data.get('last_name'),
            'phone': form_data.get('phone')
        }
        
        for field_id, value in fields.items():
            if value:
                print(f"DEBUG: Filling field '{field_id}' with '{value}'...")
                try:
                    # Use By.ID because inputs do not have name attributes
                    elem = wait.until(EC.presence_of_element_located((By.ID, field_id)))
                    elem.clear()
                    elem.send_keys(value)
                except Exception as e:
                    print(f"❌ Failed to find/fill field '{field_id}': {e}")
                    print(f"DEBUG: Page Source (First 500 chars): {driver.page_source[:500]}")
                    raise e
                
        # Checkbox
        if form_data.get('disclosure'):
            try:
                print("DEBUG: Clicking disclosure checkbox...")
                # Checkbox ID is 'leadid_tcpa_disclosure'
                chk = wait.until(EC.presence_of_element_located((By.ID, 'leadid_tcpa_disclosure')))
                if not chk.is_selected():
                    chk.click()
            except Exception as e:
                print(f"⚠️ Failed to click checkbox: {e}")

        # 3. Capture TrustedForm Cert URL (Wait for it to generate)
        print("⏳ Waiting for TrustedForm certificate...")
        
        cert_url = ''
        try:
            # Wait up to 10 seconds for the certificate to be generated
            # It usually appears in a hidden input named 'xxTrustedFormCertUrl'
            # OR we can try to execute JS to get it if the global object exists
            
            def get_cert_url(d):
                try:
                    # Try hidden input first
                    el = d.find_element(By.NAME, 'xxTrustedFormCertUrl')
                    val = el.get_attribute('value')
                    if val and val.startswith('https://cert.trustedform.com'):
                        return val
                except:
                    pass
                return False
                
            cert_url = wait.until(get_cert_url)
            print(f"✅ Captured Cert URL: {cert_url}")
        except Exception as e:
            print(f"⚠️ Could not capture TrustedForm URL via element: {e}")
            # Try JS fallback
            try:
                cert_url = driver.execute_script("return document.querySelector('[name=\"xxTrustedFormCertUrl\"]').value")
                print(f"✅ Captured Cert URL via JS: {cert_url}")
            except:
                print("❌ Failed to capture TrustedForm URL")

        # Capture IP as seen by the page (if possible)
        # We can't easily do this on the target page without submitting, 
        # but we can trust the proxy settings if the submission works.
        
        
        # 4. Submit Form
        print("🚀 Submitting form...")
        # Button ID is 'submit'
        submit_btn = driver.find_element(By.ID, 'submit')
        submit_btn.click()
        
        # 5. Wait for success
        time.sleep(5)
        
        return {
            'success': True,
            'trustedform_cert_url': cert_url,
            'proxy_ip': 'Server-Side Proxy' # Placeholder until we verify IP
        }
        
    except Exception as e:
        print(f"❌ Browser Error: {e}")
        return {'success': False, 'error': str(e)}
    finally:
        if driver:
            driver.quit()

@app.route('/')
def index():
    """Home page - redirect to login or dashboard"""
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/health')
def health():
    """Health check endpoint for deployment"""
    return jsonify({
        'status': 'healthy',
        'service': 'Proxy Access Portal',
        'version': '1.0.1',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page for agents"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in USERS and check_password_hash(USERS[username], password):
            session['username'] = username
            session['login_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            session.permanent = True
            flash(f'Welcome back, {username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password. Please try again.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout current user"""
    username = session.get('username', 'User')
    session.clear()
    flash(f'Goodbye, {username}! You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/integrations')
@login_required
def integrations():
    """Manage Data Pass Integrations"""
    try:
        conn = get_db_connection()
        if DATABASE_URL and POSTGRES_AVAILABLE:
            c = conn.cursor(cursor_factory=RealDictCursor)
        else:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
        c.execute('SELECT * FROM webhook_configs')
        configs = c.fetchall()
        conn.close()
        
        return render_template('integrations.html', configs=configs, username=session.get('username'))
    except Exception as e:
        flash(f'Error loading integrations: {e}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/api/integrations', methods=['POST'])
@login_required
def save_integration():
    """Save a new integration"""
    try:
        data = request.json
        name = data.get('name')
        url = data.get('url')
        mapping = json.dumps(data.get('mapping', {}))
        
        conn = get_db_connection()
        c = conn.cursor()
        
        is_postgres = (DATABASE_URL is not None) and POSTGRES_AVAILABLE
        placeholder = '%s' if is_postgres else '?'
        
        c.execute(f'INSERT INTO webhook_configs (name, url, field_mapping) VALUES ({placeholder}, {placeholder}, {placeholder})',
                 (name, url, mapping))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/integrations/<int:id>', methods=['DELETE'])
@login_required
def delete_integration(id):
    """Delete an integration"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        is_postgres = (DATABASE_URL is not None) and POSTGRES_AVAILABLE
        placeholder = '%s' if is_postgres else '?'
        
        c.execute(f'DELETE FROM webhook_configs WHERE id = {placeholder}', (id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/integrations/test', methods=['POST'])
@login_required
def test_integration():
    """Test an integration with dummy data"""
    try:
        data = request.json
        url = data.get('url')
        mapping = data.get('mapping', {})
        
        # Dummy Data
        dummy_lead = {
            'id': 123,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'first_name': 'John',
            'last_name': 'Doe',
            'phone': '555-123-4567',
            'email': 'john.doe@example.com',
            'state': 'TX',
            'zip_code': '75001',
            'trustedform_cert_url': 'https://cert.trustedform.com/example123'
        }
        
        payload = {}
        for app_field, target_field in mapping.items():
            if not target_field: continue
            payload[target_field] = dummy_lead.get(app_field, '')
            
        resp = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=10)
        
        return jsonify({
            'success': True, 
            'status_code': resp.status_code,
            'response': resp.text[:200]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard for authenticated users"""
    return render_template('dashboard.html', 
                         username=session.get('username'),
                         login_time=session.get('login_time'),
                         proxy_config=PROXY_CONFIG)

@app.route('/api/test-proxy', methods=['POST'])
@login_required
def test_proxy():
    """API endpoint to test the proxy connection"""
    # Return fake success to prevent memory crashes
    return jsonify({
        'success': True,
        'ip_address': '38.13.182.181',
        'status_code': 200,
        'message': 'Proxy connection successful! (Simulated)'
    })

@app.route('/api/proxy-request', methods=['POST'])
@login_required
def proxy_request():
    """API endpoint to make custom requests through the proxy"""
    # Disabled to prevent memory issues in production
    return jsonify({
        'success': False,
        'error': 'Proxy requests disabled to prevent memory issues. Use local proxy server instead.',
        'message': 'For proxy functionality, run proxy_server.py locally'
    }), 503

@app.route('/api/proxy-info')
@login_required
def proxy_info():
    """API endpoint to get proxy configuration info"""
    return jsonify({
        'host': PROXY_CONFIG['host'],
        'port': PROXY_CONFIG['port'],
        'username': PROXY_CONFIG['username'],
        'country': PROXY_CONFIG['country'],
        'rotation': PROXY_CONFIG['rotation'],
        # Don't expose the full password in API responses
        'password_hint': PROXY_CONFIG['password'][:4] + '...' + PROXY_CONFIG['password'][-10:]
    })

@app.route('/credentials')
@login_required
def credentials():
    """Page displaying proxy credentials for copying"""
    return render_template('credentials.html',
                         username=session.get('username'),
                         proxy_config=PROXY_CONFIG)

@app.route('/documentation')
@login_required
def documentation():
    """Documentation page with usage examples"""
    return render_template('documentation.html',
                         username=session.get('username'),
                         proxy_config=PROXY_CONFIG)

@app.route('/leads')
@login_required
def view_leads():
    """View captured leads"""
    try:
        conn = get_db_connection()
        
        # Handle row factory differences
        if DATABASE_URL and POSTGRES_AVAILABLE:
            # Postgres
            c = conn.cursor(cursor_factory=RealDictCursor)
        else:
            # SQLite
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
        c.execute('SELECT * FROM leads ORDER BY timestamp DESC')
        leads = c.fetchall()
        
        # Debug: Print first lead to check keys
        if leads:
            first_lead = leads[0]
            # Convert to dict for printing if it's a Row object
            if isinstance(first_lead, sqlite3.Row):
                print(f"DEBUG: First lead keys: {first_lead.keys()}")
                print(f"DEBUG: First lead values: {dict(first_lead)}")
            else:
                print(f"DEBUG: First lead: {first_lead}")
                
        conn.close()
        return render_template('leads.html', leads=leads, username=session.get('username'))
    except Exception as e:
        flash(f'Error loading leads: {e}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/download-client')
@login_required
def download_client():
    """Download the client-side proxy browser launcher"""
    try:
        # Ensure package exists
        if not os.path.exists('proxy_browser_client.zip'):
            import package_client
            package_client.create_client_package()
            
        return send_file('proxy_browser_client.zip',
                        as_attachment=True,
                        download_name='proxy_browser_client.zip')
    except Exception as e:
        flash(f'Error downloading client: {e}', 'error')
        return redirect(url_for('dashboard'))


    except Exception as e:
        print(f"❌ Error saving lead from extension: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/save-lead', methods=['POST'])
def save_lead_api():
    """API endpoint for the Chrome Extension to save captured leads"""
    try:
        data = request.json
        print(f"📥 Received lead data from extension: {data}")
        
        # Save to Local Database
        lead_id, timestamp = save_lead_to_db(data)
        
        if lead_id:
            data['id'] = lead_id
            data['timestamp'] = timestamp
        
        # Also try saving to Google Sheets (optional backup)
        save_to_google_sheets(
            form_data=data,
            trustedform_url=data.get('trustedform_cert_url', ''),
            proxy_ip='Extension Capture',
            submission_status='Captured via Extension'
        )
        
        if lead_id:
            return jsonify({'success': True, 'message': 'Lead saved to local database'})
        else:
            return jsonify({'success': False, 'error': 'Failed to save to database'})
            
    except Exception as e:
        print(f"❌ Error saving lead from extension: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/landing')
def landing_page():
    """Serve the Medicare landing page"""
    return render_template('medicare-landing2.html')

@app.route('/api/submit-lead', methods=['POST'])
def submit_lead_api():
    """API endpoint for landing page form submission"""
    try:
        data = request.json
        print(f"📥 Received lead data from landing page: {data}")
        
        # Save to Local Database
        lead_id, timestamp = save_lead_to_db(data)
        if lead_id:
            data['id'] = lead_id
            data['timestamp'] = timestamp
        
        # Submit form through proxy
        trustedform_url = data.get('trustedform_cert_url', '')
        submission_result = submit_form_through_proxy(data, trustedform_url)
        
        # Save to Google Sheets
        save_to_google_sheets(
            form_data=data,
            trustedform_url=trustedform_url,
            proxy_ip=submission_result.get('proxy_ip') if submission_result else None,
            submission_status='Success' if submission_result and submission_result.get('success') else 'Failed',
            trustedform_token=data.get('trustedform_token', ''),
            trustedform_ping_url=data.get('trustedform_ping_url', '')
        )
        
        # Trigger Webhooks
        trigger_webhooks(data)
        
        # Retain TrustedForm Certificate
        retention_success = False
        if trustedform_url:
            retention_success = retain_trustedform_certificate(trustedform_url, data)
        
        if submission_result and submission_result.get('success'):
            return jsonify({
                'success': True, 
                'proxy_ip': submission_result.get('proxy_ip'),
                'trustedform_retained': retention_success
            })
        else:
            error_msg = submission_result.get('error', 'Unknown error') if submission_result else 'Request timed out'
            return jsonify({'success': False, 'error': error_msg})
            
    except Exception as e:
        print(f"❌ Error in submit_lead_api: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/submit-form', methods=['GET', 'POST'])

def submit_form():
    """Form submission page for agents"""
    if request.method == 'GET':
        return render_template('submit_form.html',
                             username=session.get('username'))
    
    # Handle form submission
    try:
        # Get form data matching landing page structure
        form_data = {
            'state': request.form.get('state', ''),
            'zip_code': request.form.get('zip_code', ''),
            'first_name': request.form.get('first_name', ''),
            'last_name': request.form.get('last_name', ''),
            'phone': request.form.get('phone', ''),
            'email': request.form.get('email', ''),
            'disclosure': request.form.get('disclosure', ''),  # TCPA consent checkbox
        }
        
        # Get TrustedForm certificate URL from client-side JavaScript (if available)
        # TrustedForm certificates MUST be generated by TrustedForm JavaScript, not server-side
        # The form now sends xxTrustedFormCertUrl, xxTrustedFormToken, xxTrustedFormPingUrl
        trustedform_url = request.form.get('xxTrustedFormCertUrl', '').strip()
        trustedform_token = request.form.get('xxTrustedFormToken', '').strip()
        trustedform_ping_url = request.form.get('xxTrustedFormPingUrl', '').strip()
        
        # Fallback to old field name if new one is empty (just in case)
        if not trustedform_url:
             trustedform_url = request.form.get('trustedform_cert_url', '').strip()

        # Only use if it's a valid TrustedForm URL (starts with https://cert.trustedform.com/)
        if trustedform_url and not trustedform_url.startswith('https://cert.trustedform.com/'):
            trustedform_url = ''  # Invalid format, use empty string
        # If no TrustedForm URL, use empty string (not None) so Google Sheets doesn't break
        if not trustedform_url:
            trustedform_url = ''
            
        # Add to form_data for local DB saving and passing to other functions
        form_data['trustedform_cert_url'] = trustedform_url
        form_data['trustedform_token'] = trustedform_token
        form_data['trustedform_ping_url'] = trustedform_ping_url
        form_data['source'] = 'Web Form' # Explicitly set source
        
        # Save to Local Database (Initial)
        lead_id, timestamp = save_lead_to_db(form_data)
        if lead_id:
            form_data['id'] = lead_id
            form_data['timestamp'] = timestamp
        
        # Submit via Server-Side Browser
        browser_result = submit_lead_via_browser(form_data)
        
        if browser_result.get('success'):
            # Update data with captured Cert URL
            captured_cert_url = browser_result.get('trustedform_cert_url', '')
            if captured_cert_url:
                print(f"✅ Updating Cert URL to captured one: {captured_cert_url}")
                form_data['trustedform_cert_url'] = captured_cert_url
                
                # UPDATE DATABASE with new Cert URL
                try:
                    conn = get_db_connection()
                    c = conn.cursor()
                    is_postgres = (DATABASE_URL is not None) and POSTGRES_AVAILABLE
                    placeholder = '%s' if is_postgres else '?'
                    
                    if is_postgres:
                        c.execute("UPDATE leads SET trustedform_cert_url = %s WHERE id = %s", (captured_cert_url, lead_id))
                    else:
                        c.execute("UPDATE leads SET trustedform_cert_url = ? WHERE id = ?", (captured_cert_url, lead_id))
                    conn.commit()
                    conn.close()
                    print("✅ Database updated with correct TrustedForm URL")
                except Exception as e:
                    print(f"❌ Failed to update database with new cert URL: {e}")

            
            # Save to Google Sheets
            save_to_google_sheets(
                form_data=form_data,
                trustedform_url=form_data['trustedform_cert_url'],
                proxy_ip=browser_result.get('proxy_ip'),
                submission_status='Success (Browser)',
                trustedform_token=form_data.get('trustedform_token', ''),
                trustedform_ping_url=form_data.get('trustedform_ping_url', '')
            )
            
            # Trigger Webhooks
            trigger_webhooks(form_data)
            
            # Retain TrustedForm Certificate
            retention_success = False
            if form_data.get('trustedform_cert_url'):
                retention_success = retain_trustedform_certificate(form_data['trustedform_cert_url'], form_data)
            
            if retention_success:
                flash(f'Form submitted successfully! Cert URL: {form_data["trustedform_cert_url"]}', 'success')
            elif form_data.get('trustedform_cert_url'):
                flash(f'Form submitted but TrustedForm Retention FAILED. Please check logs. Cert URL: {form_data["trustedform_cert_url"]}', 'warning')
            else:
                flash(f'Form submitted successfully! (No Cert URL captured)', 'success')
        else:
            flash(f'Submission failed: {browser_result.get("error")}', 'error')
        
        return redirect(url_for('submit_form'))
        
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'error')
        return redirect(url_for('submit_form'))

# Initialize database on startup (ensure tables exist)
# This is critical for production where __main__ is not executed
# We do this at the module level so it runs when Gunicorn imports the app
try:
    init_db()
except Exception as e:
    print(f"Warning: Database initialization failed on startup: {e}")

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    print("\n" + "="*60)
    print("Proxy Access Portal Starting...")
    print("="*60)
    
    # Initialize Database
    init_db()
    
    print(f"\nProxy Service: {PROXY_CONFIG['host']}:{PROXY_CONFIG['port']}")
    print(f"Location: {PROXY_CONFIG['country']} ({PROXY_CONFIG['rotation']})")
    print(f"\nAvailable Users: {len(USERS)} total")
    print("   - agent1 through agent100 (password: password123)")
    print("   - admin (password: admin123)")
    print("\nDefault password for all agents: 'password123'")
    print("   (Admin password: 'admin123')")
    print("\nAccess the portal at: http://localhost:5000")
    print("="*60 + "\n")
    
    # Get port from environment variable for cloud deployment
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)

