#!/bin/bash
# ========================================================================
# Sign Language to Text Converter - Linux/Mac Setup & Run Script
# ========================================================================
# This script automatically:
# 1. Installs Python dependencies
# 2. Starts the Flask application
# 3. Opens the browser (on Mac)
# ========================================================================

echo ""
echo "========================================================================"
echo "Sign Language to Text Converter - Startup Script"
echo "========================================================================"
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed"
    echo "Please install Python 3 from: https://www.python.org/"
    exit 1
fi

echo "[OK] Python found!"
python3 --version
echo ""

# Install dependencies
echo "[INSTALL] Installing required packages..."
echo "Installing: Flask, OpenCV, MediaPipe, Numpy..."
echo ""

pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to install dependencies"
    exit 1
fi

echo ""
echo "[OK] All dependencies installed successfully!"
echo ""

# Start the Flask application
echo "[START] Starting Flask application..."
echo ""
echo "========================================================================"
echo "Server is starting..."
echo "Open your browser and go to: http://localhost:5000"
echo "Press CTRL+C to stop the server"
echo "========================================================================"
echo ""

python3 app.py
