import requests
import os
import re
from dotenv import load_dotenv

load_dotenv()

PROXY_HOST = os.getenv('IPROYAL_HOST')
PROXY_PORT = os.getenv('IPROYAL_PORT')
PROXY_USER = os.getenv('IPROYAL_USER')
PROXY_PASS = os.getenv('IPROYAL_PASS')

def find_endpoints():
    if not PROXY_HOST or not PROXY_USER:
        print("Proxy credentials missing")
        return

    proxy_url = f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"
    proxies = {"http": proxy_url, "https": proxy_url}

    # URL found in form.txt
    js_url = "https://lowinsurancecost.com/main.9eb5095a96d947f8.js"
    print(f"Fetching {js_url}...")
    
    try:
        response = requests.get(js_url, proxies=proxies, timeout=30, verify=False)
        content = response.text
        print(f"JS Length: {len(content)}")
        
        # Search for common API patterns
        patterns = [
            r'api/[a-zA-Z0-9_\-/]+',
            r'submit[a-zA-Z0-9_\-/]*',
            r'leads?[a-zA-Z0-9_\-/]*',
            r'https?://[^\s"\']+'
        ]
        
        found = set()
        for p in patterns:
            matches = re.findall(p, content)
            for m in matches:
                # Filter out noise
                if len(m) < 50 and not m.startswith('http'):
                    found.add(m)
                elif m.startswith('http') and 'lowinsurancecost' in m:
                    found.add(m)
                    
        print("\nPossible Endpoints Found:")
        for f in sorted(found):
            print(f" - {f}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_endpoints()
