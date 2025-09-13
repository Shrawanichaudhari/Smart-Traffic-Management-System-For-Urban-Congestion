@echo off
echo Starting Traffic Analytics Backend...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Install dependencies
echo Installing dependencies...
pip install fastapi uvicorn

REM Start the server
echo.
echo Starting server on http://localhost:8000
echo Press Ctrl+C to stop the server
echo.
python simple_main.py

pause