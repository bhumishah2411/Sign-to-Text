@echo off
REM ========================================================================
REM Sign Language to Text Converter - Windows Setup & Run Script
REM ========================================================================
REM This batch file automatically:
REM 1. Installs Python dependencies
REM 2. Starts the Flask application
REM 3. Opens the browser
REM ========================================================================

echo.
echo ========================================================================
echo Sign Language to Text Converter - Startup Script
echo ========================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python from: https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo [OK] Python found!
python --version
echo.

REM Install dependencies
echo [INSTALL] Installing required packages...
echo Installing: Flask, OpenCV, MediaPipe, Numpy...
echo.

pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [OK] All dependencies installed successfully!
echo.

REM Start the Flask application
echo [START] Starting Flask application...
echo.
echo ========================================================================
echo Server is starting...
echo Open your browser and go to: http://localhost:5000
echo Press CTRL+C in this window to stop the server
echo ========================================================================
echo.

python app.py

pause
