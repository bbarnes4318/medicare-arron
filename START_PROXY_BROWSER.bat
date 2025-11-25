@echo off
title Proxy Browser Launcher
color 0A

echo ========================================================
echo    STARTING PROXY BROWSER
echo ========================================================
echo.
echo This will launch a secure browser session through the
echo Residential Proxy.
echo.

python launch_browser.py

if %errorlevel% neq 0 (
    echo.
    echo ❌ Error occurred. Please check if Python is installed.
    pause
)
