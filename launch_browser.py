import os
import sys
import subprocess
import time
import threading
import socket
import shutil
import tempfile

# Configuration
PROXY_HOST = "127.0.0.1"
PROXY_PORT = 8888
TARGET_URL = "https://buyertrend.org"

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def start_proxy_server():
    """Start the proxy server in a separate thread if not already running"""
    if is_port_in_use(PROXY_PORT):
        print(f"✅ Proxy server already running on port {PROXY_PORT}")
        return

    print(f"🚀 Starting local proxy server on port {PROXY_PORT}...")
    try:
        # Import here to avoid circular imports or issues if file missing
        from proxy_server import start_proxy_server as run_server
        
        # Run in a separate thread so we don't block
        proxy_thread = threading.Thread(target=run_server)
        proxy_thread.daemon = True
        proxy_thread.start()
        
        # Wait a bit for it to start
        time.sleep(2)
        print("✅ Proxy server started!")
    except ImportError:
        print("❌ Error: Could not import proxy_server.py. Make sure it exists.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting proxy server: {e}")
        sys.exit(1)

def find_chrome_path():
    """Find Google Chrome executable path"""
    possible_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe", # Fallback to Edge
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return None

def launch_browser():
    """Launch Chrome with proxy settings"""
    chrome_path = find_chrome_path()
    if not chrome_path:
        print("❌ Error: Could not find Google Chrome or Microsoft Edge.")
        print("Please install Chrome to use this feature.")
        input("Press Enter to exit...")
        return

    browser_name = "Edge" if "msedge" in chrome_path.lower() else "Chrome"
    print(f"found {browser_name} at: {chrome_path}")

    # Create a temporary user data directory to ensure a clean session
    # and to avoid conflicts with existing open browser windows
    user_data_dir = os.path.join(tempfile.gettempdir(), "proxy_browser_profile")
    if not os.path.exists(user_data_dir):
        os.makedirs(user_data_dir)
    print(f"🚀 Launching {browser_name} with Residential Proxy...")
    print(f"   - Proxy: {PROXY_HOST}:{PROXY_PORT}")
    print(f"   - Target: {TARGET_URL}")
    print("   - Profile: Isolated (Clean Session)")

    # Path to the extension
    extension_path = os.path.join(os.getcwd(), 'extension')
    
    # Chrome command line arguments
    chrome_args = [
        chrome_path,
        f'--proxy-server=http://{PROXY_HOST}:{PROXY_PORT}',
        f'--user-data-dir={user_data_dir}',
        '--no-first-run',
        '--no-default-browser-check',
        f'--load-extension={extension_path}',  # Load our data capture extension
        TARGET_URL
    ]

    try:
        subprocess.Popen(chrome_args)
        print("\n✅ Browser launched successfully!")
        print("   You are now browsing through the Residential Proxy.")
        print("   The address bar shows the real URL.")
        print("   The site sees the Proxy IP.")
        print("\n⚠️  DO NOT CLOSE THIS WINDOW until you are done browsing.")
    except Exception as e:
        print(f"❌ Error launching browser: {e}")

if __name__ == "__main__":
    print("="*60)
    print("🔒 SECURE PROXY BROWSER LAUNCHER")
    print("="*60)
    
    # 1. Start Proxy
    start_proxy_server()
    
    # 1.5 Configure API URL (for DigitalOcean support)
    config_file = "api_config.txt"
    api_url = "http://localhost:5000"
    
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            api_url = f.read().strip()
            print(f"ℹ️  Using saved API URL: {api_url}")
    else:
        print("\n" + "="*60)
        print("🌐 API CONFIGURATION (First Run Only)")
        print("="*60)
        print("Where is your app hosted?")
        print("1. Localhost (default)")
        print("2. DigitalOcean / Remote Server")
        choice = input("Enter 1 or 2: ").strip()
        
        if choice == "2":
            url = input("Enter your App URL (e.g., https://myapp.ondigitalocean.app): ").strip()
            if url:
                # Remove trailing slash
                if url.endswith('/'):
                    url = url[:-1]
                api_url = url
                with open(config_file, "w") as f:
                    f.write(api_url)
                print("✅ Configuration saved!")
        else:
            print("✅ Using localhost.")
            with open(config_file, "w") as f:
                f.write(api_url)

    # Update extension/content.js with the correct URL
    content_js_path = os.path.join("extension", "content.js")
    if os.path.exists(content_js_path):
        try:
            with open(content_js_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Replace localhost or previous URL with new API URL
            # We look for the fetch call
            import re
            new_content = re.sub(r'fetch\("https?://[^"]+/api/save-lead"', f'fetch("{api_url}/api/save-lead"', content)
            
            with open(content_js_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"✅ Extension configured to send data to: {api_url}")
        except Exception as e:
            print(f"⚠️  Warning: Could not update extension configuration: {e}")

    # 2. Launch Browser
    launch_browser()
    
    # Keep script running to keep proxy thread alive if we started it
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Exiting...")
