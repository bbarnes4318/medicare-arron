"""
Real Proxy Server - Routes all browser traffic through IPRoyal proxy
"""
import socket
import threading
import requests
import base64
import re
import random
import string
from urllib.parse import urlparse
import os
from dotenv import load_dotenv

# Generate a fresh session ID for this run
SESSION_ID = get_random_session_id()
SESSION_ID = get_random_session_id()
# Construct password with session ID if not provided directly
# IPRoyal format: password_country-us_city-lasvegas_session-ID_lifetime-168h
base_pass = os.getenv("IPROYAL_PASS_BASE")
if base_pass:
    PROXY_PASS = f"{base_pass}_country-us_city-lasvegas_session-{SESSION_ID}_lifetime-168h"
else:
    PROXY_PASS = os.getenv("IPROYAL_PASS")

# Local proxy server configuration
LOCAL_PROXY_HOST = "127.0.0.1"
LOCAL_PROXY_PORT = 8888

def handle_client(client_socket):
    """Handle client connection and proxy requests"""
    try:
        # Receive request from client
        # Use latin-1 to avoid decoding errors if binary data is included (e.g. TLS ClientHello)
        raw_data = client_socket.recv(4096)
        if not raw_data:
            return
            
        request = raw_data.decode('latin-1')
        
        # Parse the request
        lines = request.split('\n')
        if not lines:
            return
            
        # Extract method, URL, and version
        first_line = lines[0]
        parts = first_line.split()
        if len(parts) < 3:
            return
            
        method = parts[0]
        url = parts[1]
        
        # Handle CONNECT method (HTTPS) - TUNNEL THROUGH IPROYAL
        if method == "CONNECT":
            handle_https_connect(client_socket, url)
        else:
            handle_http_request(client_socket, request)
            
    except Exception as e:
        print(f"❌ Error handling client: {e}")
    finally:
        client_socket.close()

def handle_https_connect(client_socket, url):
    """Handle HTTPS CONNECT requests - TUNNEL THROUGH IPROYAL"""
    try:
        # Extract host and port from CONNECT request
        host_port = url.split(':')
        host = host_port[0]
        port = int(host_port[1]) if len(host_port) > 1 else 443
        
        print(f"Tunneling HTTPS to {host}:{port} through IPRoyal proxy...")
        
        # Create socket connection to IPRoyal proxy
        proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        proxy_socket.connect((PROXY_HOST, PROXY_PORT))
        
        # Send CONNECT request to IPRoyal proxy
        connect_request = f"CONNECT {host}:{port} HTTP/1.1\r\n"
        connect_request += f"Host: {host}:{port}\r\n"
        connect_request += f"Proxy-Connection: keep-alive\r\n"
        connect_request += f"Proxy-Authorization: Basic {base64.b64encode(f'{PROXY_USER}:{PROXY_PASS}'.encode()).decode()}\r\n"
        connect_request += "\r\n"
        
        proxy_socket.send(connect_request.encode())
        
        # Read response from IPRoyal proxy
        # Use latin-1 to avoid decoding errors
        response = proxy_socket.recv(4096).decode('latin-1')
        
        if "200" in response:
            # Send 200 Connection established to client
            client_socket.send(b"HTTP/1.1 200 Connection established\r\n\r\n")
            
            # Start tunneling data between client and IPRoyal proxy
            def tunnel_data(source, destination):
                try:
                    while True:
                        data = source.recv(4096)
                        if not data:
                            break
                        destination.send(data)
                except:
                    pass
                finally:
                    source.close()
                    destination.close()
            
            # Start tunneling in both directions
            client_to_proxy = threading.Thread(target=tunnel_data, args=(client_socket, proxy_socket))
            proxy_to_client = threading.Thread(target=tunnel_data, args=(proxy_socket, client_socket))
            
            client_to_proxy.daemon = True
            proxy_to_client.daemon = True
            
            client_to_proxy.start()
            proxy_to_client.start()
            
            # Wait for one thread to finish
            client_to_proxy.join()
            proxy_to_client.join()
        else:
            # Send error to client
            print(f"❌ Proxy tunnel failed: {response.splitlines()[0]}")
            client_socket.send(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
            proxy_socket.close()
                
    except Exception as e:
        print(f"❌ HTTPS CONNECT error: {e}")
        try:
            client_socket.send(b"HTTP/1.1 500 Connection failed\r\n\r\n")
        except:
            pass

def handle_http_request(client_socket, request):
    """Handle HTTP requests through IPRoyal proxy"""
    try:
        # Extract URL from request
        lines = request.split('\n')
        first_line = lines[0]
        parts = first_line.split()
        url = parts[1]
        
        # Parse the URL
        if url.startswith('http://'):
            full_url = url
        else:
            # Extract host from Host header
            host = None
            for line in lines[1:]:
                if line.lower().startswith('host:'):
                    host = line.split(':', 1)[1].strip()
                    break
            
            if not host:
                client_socket.send(b"HTTP/1.1 400 Bad Request\r\n\r\n")
                return
                
            full_url = f"http://{host}{url}"
        
        print(f"Making HTTP request to {full_url} through IPRoyal proxy...")
        
        # Create proxy connection
        proxy_url = f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"
        proxies = {'http': proxy_url, 'https': proxy_url}
        
        # Make request through IPRoyal proxy
        response = requests.get(full_url, 
                              proxies=proxies, 
                              timeout=30,
                              headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        
        # Send response back to client
        client_socket.send(f"HTTP/1.1 {response.status_code} OK\r\n".encode())
        for header, value in response.headers.items():
            client_socket.send(f"{header}: {value}\r\n".encode())
        client_socket.send(b"\r\n")
        client_socket.send(response.content)
        
    except Exception as e:
        print(f"❌ HTTP request error: {e}")
        try:
            client_socket.send(b"HTTP/1.1 500 Internal Server Error\r\n\r\n")
        except:
            pass

def start_proxy_server():
    """Start the local proxy server"""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((LOCAL_PROXY_HOST, LOCAL_PROXY_PORT))
    server_socket.listen(5)
    
    print("="*60)
    print("🚀 REAL PROXY SERVER STARTING")
    print("="*60)
    print(f"📡 Local Proxy: {LOCAL_PROXY_HOST}:{LOCAL_PROXY_PORT}")
    print(f"🌐 IPRoyal Proxy: {PROXY_HOST}:{PROXY_PORT}")
    print(f"👤 Username: {PROXY_USER}")
    print(f"🔄 Session ID: {SESSION_ID} (New IP generated)")
    print("="*60)
    print("🔧 CONFIGURE YOUR BROWSER:")
    print(f"   HTTP Proxy: {LOCAL_PROXY_HOST}:{LOCAL_PROXY_PORT}")
    print(f"   HTTPS Proxy: {LOCAL_PROXY_HOST}:{LOCAL_PROXY_PORT}")
    print("="*60)
    print("✅ All traffic will be routed through IPRoyal proxy!")
    print("="*60)
    
    while True:
        try:
            client_socket, addr = server_socket.accept()
            # print(f"📥 New connection from {addr}")
            
            # Handle client in a separate thread
            client_thread = threading.Thread(target=handle_client, args=(client_socket,))
            client_thread.daemon = True
            client_thread.start()
            
        except KeyboardInterrupt:
            print("\n🛑 Shutting down proxy server...")
            break
        except Exception as e:
            print(f"❌ Server error: {e}")
    
    server_socket.close()

if __name__ == "__main__":
    start_proxy_server()