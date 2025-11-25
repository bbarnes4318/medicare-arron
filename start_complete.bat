@echo off
echo ========================================================
echo   STARTING PROXY ACCESS PORTAL & BROWSER
echo ========================================================

echo 1. Starting Flask Backend Server (app.py)...
echo    This will open in a new window. Keep it open!
start "Proxy Portal Backend" cmd /k "python app.py"

echo.
echo 2. Waiting 5 seconds for server to initialize...
timeout /t 5 /nobreak >nul

echo.
echo 3. Launching Proxy Browser...
python launch_browser.py

echo.
echo ========================================================
echo   SESSION COMPLETE
echo ========================================================
pause
