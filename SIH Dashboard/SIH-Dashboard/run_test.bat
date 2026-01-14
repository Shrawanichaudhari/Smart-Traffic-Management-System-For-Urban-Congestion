@echo off
echo 🚦 Traffic Dashboard Test Data Sender
echo =====================================
echo.
echo Make sure your FastAPI backend is running on http://localhost:8000
echo Make sure your React frontend is running on http://localhost:3000
echo.

:menu
echo Choose an option:
echo 1. Send single test data
echo 2. Start continuous data stream
echo 3. Exit
echo.
set /p choice="Enter your choice (1-3): "

if "%choice%"=="1" (
    echo.
    echo 🧪 Sending single test data...
    python test_data_sender.py single
    echo.
    pause
    goto menu
) else if "%choice%"=="2" (
    echo.
    echo 🔄 Starting continuous data stream...
    echo Press Ctrl+C to stop
    python test_data_sender.py continuous
    echo.
    pause
    goto menu
) else if "%choice%"=="3" (
    echo 👋 Goodbye!
    exit
) else (
    echo Invalid choice! Please try again.
    echo.
    goto menu
)