import requests
import re

# Configuration
BASE_URL = "http://localhost:5000"
USERNAME = "admin"
PASSWORD = "admin123"

def test_submission():
    session = requests.Session()
    
    # 1. Login
    print(f"🔑 Logging in as {USERNAME}...")
    login_url = f"{BASE_URL}/login"
    response = session.post(login_url, data={
        'username': USERNAME,
        'password': PASSWORD
    })
    
    if "Welcome back" in response.text or response.url == f"{BASE_URL}/dashboard":
        print("✅ Login successful")
    else:
        print("❌ Login failed")
        return

    # 2. Submit Form
    print("\n📝 Submitting form...")
    submit_url = f"{BASE_URL}/submit-form"
    
    # Fake lead data
    form_data = {
        'phone': '(555) 123-4567',
        'disclosure': 'on',
        'trustedform_cert_url': 'https://cert.trustedform.com/0000000000000000000000000000000000000000' # Fake cert
    }
    
    try:
        response = session.post(submit_url, data=form_data)
        
        # Check for success message in the response HTML
        if "Form submitted successfully" in response.text:
            print("✅ Form submission reported SUCCESS by app")
            
            # Extract Proxy IP from message if possible
            match = re.search(r'Proxy IP: ([0-9\.]+)', response.text)
            if match:
                print(f"   Proxy IP used: {match.group(1)}")
        elif "Form submission failed" in response.text:
            print("❌ Form submission reported FAILURE by app")
            # Try to extract error
            match = re.search(r'alert-error">([^<]+)', response.text)
            if match:
                print(f"   Error: {match.group(1).strip()}")
        else:
            print("⚠️  Unknown response status. Check dashboard.")
            
    except Exception as e:
        print(f"❌ Error during submission request: {e}")

if __name__ == "__main__":
    test_submission()
