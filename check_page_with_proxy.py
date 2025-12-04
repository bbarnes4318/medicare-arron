import requests
import os
from dotenv import load_dotenv

load_dotenv()

PROXY_HOST = os.getenv('IPROYAL_HOST')
PROXY_PORT = os.getenv('IPROYAL_PORT')
PROXY_USER = os.getenv('IPROYAL_USER')
PROXY_PASS = os.getenv('IPROYAL_PASS')

def check_page():
    if not PROXY_HOST or not PROXY_USER:
        print("Proxy credentials missing in .env")
        return

    proxy_url = f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"
    proxies = {
        "http": proxy_url,
        "https": proxy_url
    }

    url = "https://buyertrend.org"
    print(f"Fetching {url} via proxy...")
    
    try:
        response = requests.get(url, proxies=proxies, timeout=30, verify=False)
        print(f"Status Code: {response.status_code}")
        
        content = response.text
        print(f"Content Length: {len(content)}")
        
        if "<form" in content.lower():
            print("FORM FOUND!")
            # Extract form action
            import re
            forms = re.findall(r'<form[^>]*>', content, re.IGNORECASE)
            for form in forms:
                print(f"   Form Tag: {form}")
        else:
            print("NO FORM FOUND in HTML.")
            print("   First 500 chars:")
            print(content[:500])
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_page()
