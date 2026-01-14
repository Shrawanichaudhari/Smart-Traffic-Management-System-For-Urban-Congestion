@echo off
echo Starting Traffic Analytics Frontend...
echo.

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo Error: Node.js is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

REM Install dependencies if node_modules doesn't exist
if not exist node_modules (
    echo Installing dependencies...
    npm install
)

REM Start the development server
echo.
echo Starting frontend development server...
echo The app will open in your browser at http://localhost:5173
echo Press Ctrl+C to stop the server
echo.
npm run dev

pause