@echo off
echo 🚦 SIH Traffic Dashboard - Real-time Test Simulator
echo ====================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Python is not installed or not in PATH
    echo 💡 Please install Python from https://python.org/
    pause
    exit /b 1
)

REM Install required packages
echo 📦 Installing required packages...
pip install requests >nul 2>&1

REM Check if backend is running
echo 🔍 Checking if backend is running...
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo.
    echo ❌ Backend is not running!
    echo 💡 Please start your backend first:
    echo    1. Open another terminal
    echo    2. cd "Traffic Backend"
    echo    3. python fastapi_main.py
    echo.
    pause
    exit /b 1
)

echo ✅ Backend is running!
echo.

REM Start the simulator
echo 🚀 Starting Real-time Data Simulator...
echo 💡 Your dashboard should be at: http://localhost:5173
echo ⏰ Data will update every 2 seconds
echo 🛑 Press Ctrl+C to stop
echo.
python test_realtime_data.py

pause