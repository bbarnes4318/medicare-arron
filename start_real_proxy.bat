@echo off
echo ============================================
echo Starting REAL Proxy Server
echo ============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed
    echo Please install Python from https://www.python.org/
    pause
    exit /b 1
)

REM Install requests if not installed
echo Installing required packages...
pip install requests

echo.
echo Starting Real Proxy Server...
echo.
echo CONFIGURE YOUR BROWSER:
echo   HTTP Proxy: 127.0.0.1:8888
echo   HTTPS Proxy: 127.0.0.1:8888
echo.
echo This will route ALL your browser traffic through IPRoyal!
echo.

python proxy_server.py

pause
