import socket
import base64
import sys
import time

# Configuration
LOCAL_PROXY_HOST = "127.0.0.1"
LOCAL_PROXY_PORT = 8888
TARGET_HOST = "api.ipify.org"
TARGET_PORT = 443

def test_proxy_tunnel():
    print(f"🧪 Testing proxy tunnel to {TARGET_HOST}:{TARGET_PORT} via {LOCAL_PROXY_HOST}:{LOCAL_PROXY_PORT}...")
    
    try:
        # Connect to local proxy
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(10)
        s.connect((LOCAL_PROXY_HOST, LOCAL_PROXY_PORT))
        print("✅ Connected to local proxy")
        
        # Send CONNECT request
        connect_req = f"CONNECT {TARGET_HOST}:{TARGET_PORT} HTTP/1.1\r\n"
        connect_req += f"Host: {TARGET_HOST}:{TARGET_PORT}\r\n"
        connect_req += "\r\n"
        
        print("📤 Sending CONNECT request...")
        s.sendall(connect_req.encode())
        
        # Read response
        response = s.recv(4096).decode('utf-8', errors='ignore')
        print(f"📥 Received response:\n{'-'*40}\n{response}\n{'-'*40}")
        
        if "200 Connection established" in response:
            print("✅ Tunnel established successfully!")
            return True
        else:
            print("❌ Tunnel failed!")
            return False
            
    except ConnectionRefusedError:
        print("❌ Connection refused! Is the local proxy server running?")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        s.close()

if __name__ == "__main__":
    test_proxy_tunnel()
