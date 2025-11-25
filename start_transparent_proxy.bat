@echo off
echo ============================================
echo TRANSPARENT PROXY - NO BROWSER CONFIG!
echo ============================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if errorlevel 1 (
    echo WARNING: Not running as administrator
    echo Some features may not work properly
    echo Right-click and 'Run as administrator' for full functionality
    echo.
) else (
    echo Running as administrator - Full functionality enabled
    echo.
)

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
echo Starting Transparent Proxy...
echo This will automatically configure your system proxy!
echo ALL your traffic will be routed through IPRoyal.
echo.
echo Press Ctrl+C to stop and restore original settings
echo.

python transparent_proxy.py

pause
