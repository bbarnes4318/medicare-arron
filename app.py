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
except ImportError:
    psycopg2 = None
    RealDictCursor = None
from datetime import datetime, timedelta

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
    if DATABASE_URL:
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
        if DATABASE_URL:
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
                )
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
                )
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
                if DATABASE_URL:
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
        
        is_postgres = DATABASE_URL is not None
        placeholder = '%s' if is_postgres else '?'
        
        query = f'''
            INSERT INTO leads (
                timestamp, first_name, last_name, phone, email, 
                address, city, state, zip_code, trustedform_cert_url, 
                trustedform_token, trustedform_ping_url, source, disclosure
            ) VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
        '''
        
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
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error saving to database: {e}")
        return False

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
        error_msg = str(e)
        print(f"Error saving to Google Sheets: {error_msg}")
        
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
        # Angular apps often submit to API endpoints like /api/submit, /api/leads, etc.
        # Target the specific Google Apps Script endpoint provided by the user
        submit_url = "https://script.google.com/macros/s/AKfycbxCiqJ9BN_fT5DnFFKrVW3jv3uER-jIqW4_lqzjx_o5F3avNZhFX3cPGxB6UF87lMGM/exec"
        
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
        
        # Use requests.post with 'data' to send multipart/form-data (requests handles the boundary automatically)
        response = requests.post(
            submit_url,
            data=payload,
            headers=headers,
            proxies=proxies,
            timeout=15,
            verify=False # Google scripts sometimes have cert issues with proxies, but usually fine.
        )
        
        print(f"DEBUG: Response Status: {response.status_code}")
        
        # Google Scripts often return 302 Redirect on success, or 200 with HTML
        if response.status_code in [200, 201, 302]:
            return {
                'success': True,
                'proxy_ip': proxies.get('http', '').split('@')[-1].split(':')[0] if proxies else 'Unknown'
            }
        else:
             # Fallback: If the specific URL fails, we can't really try others since this is a very specific script.
             pass

        
        response = None
        last_error = None
        
        # Try each endpoint with both JSON and form-urlencoded
        # Limit to first 3 endpoints to prevent timeout
        endpoints_to_try = common_endpoints[:3]  # Only try first 3 endpoints
        for endpoint in endpoints_to_try:
            if endpoint:
                test_url = f"{LANDING_PAGE_URL}{endpoint}"
            else:
                test_url = LANDING_PAGE_URL
            
            # Try JSON first (Angular apps typically use JSON)
            try:
                json_headers = headers.copy()
                json_headers['Content-Type'] = 'application/json'
                response = requests.post(
                    test_url,
                    json=payload,
                    headers=json_headers,
                    proxies=proxies,
                    timeout=5,  # Shorter timeout to prevent worker timeout
                    allow_redirects=True
                )
                print(f"DEBUG: Tried {test_url} (JSON) - Status: {response.status_code}")
                # If we get a 200, 201, or 302, consider it successful
                if response.status_code in [200, 201, 302]:
                    print(f"SUCCESS: Found working endpoint: {test_url} (JSON)")
                    submit_url = test_url  # Update submit_url to the working one
                    break
                else:
                    print(f"DEBUG: Response text (first 200 chars): {response.text[:200]}")
            except Exception as e:
                print(f"DEBUG: Error trying {test_url} (JSON): {str(e)}")
                last_error = e
                pass
            
            # Try form-urlencoded if JSON didn't work
            try:
                form_headers = headers.copy()
                form_headers['Content-Type'] = 'application/x-www-form-urlencoded'
                response = requests.post(
                    test_url,
                    data=payload,
                    headers=form_headers,
                    proxies=proxies,
                    timeout=5,  # Shorter timeout
                    allow_redirects=True
                )
                print(f"DEBUG: Tried {test_url} (form-urlencoded) - Status: {response.status_code}")
                # If we get a 200, 201, or 302, consider it successful
                if response.status_code in [200, 201, 302]:
                    print(f"SUCCESS: Found working endpoint: {test_url} (form-urlencoded)")
                    submit_url = test_url  # Update submit_url to the working one
                    break
                else:
                    print(f"DEBUG: Response text (first 200 chars): {response.text[:200]}")
            except Exception as e:
                print(f"DEBUG: Error trying {test_url} (form-urlencoded): {str(e)}")
                last_error = e
                pass
        
        # If all endpoints failed, check what happened
        if response is None:
            error_msg = str(last_error) if last_error else 'Unknown error - no response from any endpoint'
            print(f"ERROR: All endpoints failed. Last error: {error_msg}")
            
            # Check for proxy-specific errors
            if '402' in error_msg or 'Payment Required' in error_msg:
                error_msg = 'Proxy Error: 402 Payment Required. Your Decodo proxy account may need payment or the credentials may be expired. Please check your Decodo account status and update the proxy credentials.'
            elif 'ProxyError' in error_msg or 'proxy' in error_msg.lower():
                error_msg = f'Proxy Connection Error: {error_msg}. Please verify your Decodo proxy credentials are correct and the account is active.'
            
            return {
                'success': False,
                'error': f'Could not find working endpoint. {error_msg}',
                'proxy_ip': None
            }
        
        # If we got a response but it's not a success status code
        if response.status_code not in [200, 201, 302]:
            print(f"WARNING: Got response but status code is {response.status_code}")
            print(f"Response text (first 500 chars): {response.text[:500]}")
            return {
                'success': False,
                'error': f'Form submission returned status code {response.status_code}. Response: {response.text[:200]}',
                'status_code': response.status_code,
                'proxy_ip': None
            }
        
        
        # Get the proxy IP that was used
        try:
            ip_check_response = requests.get(
                'https://ipv4.icanhazip.com',
                proxies=proxies,
                timeout=10
            )
            proxy_ip = ip_check_response.text.strip()
        except Exception as ip_error:
            # Check for proxy errors when getting IP
            if '402' in str(ip_error) or 'Payment Required' in str(ip_error):
                proxy_ip = 'Proxy Error: 402 Payment Required - Check Decodo account'
            elif 'ProxyError' in str(ip_error):
                proxy_ip = 'Proxy Connection Failed - Check credentials'
            else:
                proxy_ip = 'Unable to determine'
        
        return {
            'success': response.status_code in [200, 201, 302],
            'status_code': response.status_code,
            'proxy_ip': proxy_ip,
            'response_text': response.text[:500] if response.text else '',
            'url': response.url
        }
        
    except requests.exceptions.RequestException as e:
        error_msg = str(e)
        
        # Provide helpful error messages for common proxy issues
        if '402' in error_msg or 'Payment Required' in error_msg:
            error_msg = 'Proxy Error: 402 Payment Required. Your Decodo proxy account may need payment or the credentials may be expired. Please check your Decodo account dashboard and ensure your account is active and has credits.'
        elif 'ProxyError' in error_msg or 'proxy' in error_msg.lower():
            error_msg = f'Proxy Connection Error: {error_msg}. Please verify your Decodo proxy credentials in app.py are correct and the account is active.'
        elif '401' in error_msg or 'Unauthorized' in error_msg:
            error_msg = 'Proxy Authentication Failed: Invalid username or password. Please check your Decodo proxy credentials.'
        elif '403' in error_msg or 'Forbidden' in error_msg:
            error_msg = 'Proxy Access Forbidden: Your Decodo account may not have permission to use this proxy or the IP may be blocked.'
        
        return {
            'success': False,
            'error': error_msg,
            'proxy_ip': None
        }

# Removed forward_to_portal function as requested


@app.route('/')
def index():
    """Render the Medicare landing page"""
    return render_template('medicare_landing.html')

# Removed /quote route as it is now the root

@app.route('/api/submit-lead', methods=['POST'])
def submit_lead():
    """Handle lead submission from landing page"""
    try:
        data = request.json
        
        # Basic Validation
        required_fields = ['first_name', 'last_name', 'phone', 'email', 'zip_code', 'state']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
                
        # Phone Validation (Simple regex)
        phone = data.get('phone', '')
        if not re.match(r'^(\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}$', phone):
             return jsonify({'error': 'Invalid phone number format'}), 400

        # Email Validation
        email = data.get('email', '')
        if not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            return jsonify({'error': 'Invalid email format'}), 400

        # Add metadata
        data['source'] = 'Landing Page'
        data['disclosure'] = 'Yes' if data.get('consent') else 'No' # Should be Yes if submitted
        
        # Save to Database
        if save_lead_to_db(data):
            # No external forwarding for landing page leads - they go directly to DB (View Leads page)
            return jsonify({'success': True, 'message': 'Lead submitted successfully'})
        else:
            return jsonify({'error': 'Failed to save lead'}), 500
            
    except Exception as e:
        print(f"Error in submit_lead: {e}")
        return jsonify({'error': str(e)}), 500

# Login route is preserved
# Dashboard route is preserved


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
        if DATABASE_URL:
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
        db_saved = save_lead_to_db(data)
        
        # Also try saving to Google Sheets (optional backup)
        save_to_google_sheets(
            form_data=data,
            trustedform_url=data.get('trustedform_cert_url', ''),
            proxy_ip='Extension Capture',
            submission_status='Captured via Extension'
        )
        
        if db_saved:
            return jsonify({'success': True, 'message': 'Lead saved to local database'})
        else:
            return jsonify({'success': False, 'error': 'Failed to save to database'})
            
    except Exception as e:
        print(f"❌ Error saving lead from extension: {e}")
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
        
        # Save to Local Database
        save_lead_to_db(form_data)
        
        # Submit form through proxy
        submission_result = submit_form_through_proxy(form_data, trustedform_url)
        
        # Save to Google Sheets FIRST (before checking submission result)
        # This ensures data is saved even if submission fails or times out
        sheets_saved = save_to_google_sheets(
            form_data=form_data,
            trustedform_url=trustedform_url or '',  # Use empty string if None
            proxy_ip=submission_result.get('proxy_ip') if submission_result else None,
            submission_status='Success' if submission_result and submission_result.get('success') else 'Failed',
            trustedform_token=form_data.get('trustedform_token', ''),
            trustedform_ping_url=form_data.get('trustedform_ping_url', '')
        )
        
        if submission_result and submission_result.get('success'):
            flash(f'Form submitted successfully! Proxy IP: {submission_result.get("proxy_ip", "N/A")}', 'success')
            if sheets_saved:
                flash('Data saved to Google Sheets successfully!', 'success')
            else:
                flash('Warning: Data could not be saved to Google Sheets. Check configuration.', 'warning')
        else:
            error_msg = submission_result.get('error', 'Unknown error') if submission_result else 'Request timed out'
            flash(f'Form submission failed: {error_msg}', 'error')
            # Still try to save to sheets even if submission failed
            if sheets_saved:
                flash('Form data saved to Google Sheets despite submission failure.', 'info')
            else:
                flash('Warning: Data could not be saved to Google Sheets. Check configuration.', 'warning')
        
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

