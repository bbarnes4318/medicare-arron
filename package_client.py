import os
import zipfile
import shutil

def create_client_package():
    package_name = "proxy_browser_client.zip"
    files_to_include = [
        "launch_browser.py",
        "proxy_server.py",
        "requirements.txt",
        ".env.example"
    ]
    dirs_to_include = [
        "extension"
    ]

    print(f"📦 Creating {package_name}...")

    with zipfile.ZipFile(package_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add files
        for file in files_to_include:
            if os.path.exists(file):
                print(f"  Adding {file}")
                zipf.write(file)
            else:
                print(f"  ⚠️ Warning: {file} not found!")

        # Add directories
        for directory in dirs_to_include:
            if os.path.exists(directory):
                print(f"  Adding {directory}/")
                for root, dirs, files in os.walk(directory):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, os.getcwd())
                        print(f"    Adding {arcname}")
                        zipf.write(file_path, arcname)
            else:
                print(f"  ⚠️ Warning: {directory}/ not found!")

        # Create a simple start script for the client
        start_script = """@echo off
echo ==========================================
echo INSTALLING DEPENDENCIES...
echo ==========================================
pip install -r requirements.txt

echo.
echo ==========================================
echo STARTING PROXY BROWSER...
echo ==========================================
python launch_browser.py
pause
"""
        zipf.writestr("start_client.bat", start_script)
        print("  Adding start_client.bat")

    print(f"\n✅ Package created: {package_name}")

if __name__ == "__main__":
    create_client_package()
