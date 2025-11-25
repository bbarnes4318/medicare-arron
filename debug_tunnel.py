import socket
import base64
import sys
import time

# Configuration
LOCAL_PROXY_HOST = "127.0.0.1"
LOCAL_PROXY_PORT = 8888

TARGETS = [
    ("api.ipify.org", 443),
    ("api.trustedform.com", 443),
    ("script.google.com", 443)
]

def test_target(host, port):
    print(f"\n🧪 Testing tunnel to {host}:{port}...")
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(10)
        s.connect((LOCAL_PROXY_HOST, LOCAL_PROXY_PORT))
        
        connect_req = f"CONNECT {host}:{port} HTTP/1.1\r\n"
        connect_req += f"Host: {host}:{port}\r\n"
        connect_req += "\r\n"
        
        s.sendall(connect_req.encode())
        
        response = s.recv(4096).decode('latin-1', errors='ignore')
        print(f"📥 Response: {response.splitlines()[0]}")
        
        if "200" in response:
            print(f"✅ Success: Tunnel established to {host}")
            return True
        else:
            print(f"❌ Failed: Proxy returned {response.splitlines()[0]}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        s.close()

if __name__ == "__main__":
    print("Running connectivity tests...")
    success_count = 0
    for host, port in TARGETS:
        if test_target(host, port):
            success_count += 1
            
    print(f"\nSummary: {success_count}/{len(TARGETS)} tests passed.")
