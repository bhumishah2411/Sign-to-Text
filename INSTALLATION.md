# Installation & Setup Guide

## 📋 Prerequisites

- Windows 10/11, Mac, or Linux
- Python 3.7+ installed
- Webcam connected
- 2GB free RAM minimum
- Browser (Chrome, Firefox, Safari, Edge)

---

## 🔧 Installation Steps

### Step 1: Install Python (If Not Already Installed)

**Windows:**
1. Go to https://www.python.org/downloads/
2. Click "Download Python 3.x.x"
3. Run installer
4. ✅ CHECK: "Add Python to PATH"
5. Click Install Now

**Mac:**
```bash
# Using Homebrew (install if needed: /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)")
brew install python3
```

**Linux:**
```bash
sudo apt-get update
sudo apt-get install python3 python3-pip
```

### Step 2: Verify Python Installation

```bash
# Open Terminal/Command Prompt and run:
python --version
# or
python3 --version

# Should show: Python 3.x.x
```

### Step 3: Navigate to Project Folder

```bash
# Windows:
cd C:\signToText\sign_language_converter

# Mac/Linux:
cd ~/sign_language_converter
```

### Step 4: Install Python Dependencies

```bash
# Install all required packages
pip install -r requirements.txt

# This installs:
# - Flask (web framework)
# - OpenCV (computer vision)
# - MediaPipe (hand detection)
# - Numpy (numerical computing)
```

**Expected output:**
```
Successfully installed Flask-2.3.3 opencv-python-4.8.1.78 ...
```

---

## 🚀 Running the Application

### Option 1: Using Startup Script (Easiest)

**Windows:**
```bash
# Double-click: RUN.bat
# Or in Command Prompt:
RUN.bat
```

**Mac/Linux:**
```bash
# In Terminal:
bash run.sh
```

### Option 2: Manual Start

```bash
python app.py
```

**Expected output:**
```
============================================================
Sign Language to Text Converter - Flask App
============================================================
Starting server...
Open browser and go to: http://localhost:5000
Press CTRL+C to stop the server
============================================================
```

### Step 5: Open in Browser

1. Open your web browser (Chrome, Firefox, etc.)
2. Go to: **http://localhost:5000**
3. You should see the Sign Language Converter interface

---

## ✅ Verification Checklist

After installation, check:

- [ ] Python installed: `python --version`
- [ ] Dependencies installed: No errors during pip install
- [ ] Flask app runs: `python app.py` - no errors
- [ ] Browser loads: http://localhost:5000 - page displays
- [ ] Buttons visible: "Start Camera" and "Stop Camera"
- [ ] No console errors: Open F12 in browser

---

## 🎮 First Time Setup

1. **Start the application**
   ```bash
   python app.py
   ```

2. **Open browser**
   - Go to http://localhost:5000

3. **Allow camera access**
   - Browser will ask for camera permission
   - Click "Allow"

4. **Test camera**
   - Click "Start Camera" button
   - You should see live video feed
   - Make a thumbs-up gesture
   - Should appear in "Detected Signs" list

5. **Stop when done**
   - Click "Stop Camera"
   - Close browser
   - Press CTRL+C in terminal

---

## 🐛 Troubleshooting Installation

### Python Not Found

**Problem:**
```
'python' is not recognized as an internal or external command
```

**Solution:**
1. Python not in PATH
2. Add to PATH: https://stackoverflow.com/a/37800912
3. Restart computer and try again
4. Use `python3` instead of `python`

### pip Not Found

**Problem:**
```
'pip' is not recognized
```

**Solution:**
```bash
# Use Python module to run pip:
python -m pip install -r requirements.txt
```

### Port 5000 Already in Use

**Problem:**
```
Address already in use
```

**Solution 1: Find and close the process**
```bash
# Windows:
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Mac/Linux:
lsof -i :5000
kill -9 <PID>
```

**Solution 2: Change port in app.py**
```python
# Line at bottom of app.py:
app.run(host='0.0.0.0', port=5001, debug=True)  # Changed 5000 to 5001
```
Then go to: http://localhost:5001

### Camera Permission Denied

**Windows:**
- Settings → Privacy & Security → Camera → Allow apps to access camera

**Mac:**
- System Preferences → Security & Privacy → Camera → Allow Chrome/Firefox

**Linux:**
- Check /dev/video0 permissions: `ls -la /dev/video0`

### Out of Memory / Slow Performance

**Solution:**
- Close other applications
- Reduce resolution in config.py:
  ```python
  WEBCAM_WIDTH = 480   # Changed from 640
  WEBCAM_HEIGHT = 360  # Changed from 480
  ```

---

## 📦 What Gets Installed

### Python Packages

| Package | Size | Purpose |
|---------|------|---------|
| Flask | 2 MB | Web framework |
| OpenCV | 250 MB | Computer vision |
| MediaPipe | 100 MB | Hand detection |
| Numpy | 50 MB | Numerical computing |
| **Total** | **~400 MB** | |

### Disk Space Required
- Code: ~5 MB
- Dependencies: ~400 MB
- Database (after use): ~1 MB per 1000 predictions
- **Total: ~500 MB minimum**

---

## 🌐 Network/Firewall

### Local Network Access

If you want to access from another computer:

1. Find your computer IP:
   ```bash
   # Windows:
   ipconfig
   
   # Mac/Linux:
   ifconfig
   ```
   Look for IPv4 address (e.g., 192.168.x.x)

2. Access from other computer:
   ```
   http://192.168.x.x:5000
   ```

### Firewall Settings

If it doesn't work, allow Python through firewall:
- Windows Defender Firewall → Allow app → Python
- Or disable firewall temporarily for testing

---

## 🔄 Updating Dependencies

To update packages to latest versions:

```bash
pip install --upgrade -r requirements.txt
```

---

## 🗑️ Uninstalling

To remove all installed packages:

```bash
pip uninstall Flask opencv-python mediapipe numpy Werkzeug -y
```

---

## 📱 System Requirements

### Minimum (Works, but slow)
- CPU: Intel i3 / AMD Ryzen 3
- RAM: 4 GB
- Storage: 500 MB free
- OS: Windows 7+, macOS 10.12+, Ubuntu 16.04+

### Recommended (Good performance)
- CPU: Intel i5 / AMD Ryzen 5
- RAM: 8 GB
- Storage: 1 GB free
- OS: Windows 10+, macOS 10.14+, Ubuntu 18.04+

### Optimal (Excellent performance)
- CPU: Intel i7 / AMD Ryzen 7
- RAM: 16 GB
- Storage: 2 GB free
- OS: Windows 11, macOS 11+, Ubuntu 20.04+

---

## ✨ Optional Enhancements

### Enable GPU Acceleration (If you have NVIDIA GPU)

```bash
# Install CUDA-enabled OpenCV
pip install opencv-contrib-python-headless

# Install TensorFlow GPU (optional)
pip install tensorflow-gpu
```

### Install Development Tools

```bash
# For debugging and development:
pip install flask-debugtoolbar
pip install python-dotenv
```

### Database Tools

```bash
# GUI tool to view SQLite database:
# Download from: https://sqlitebrowser.org/
```

---

## 🎓 For College Lab Setup

### Single Computer Lab:
```bash
# Install once, share with friends via USB or network
```

### Multiple Computers:
```bash
# Each computer:
1. Install Python
2. Extract project folder
3. pip install -r requirements.txt
4. python app.py
```

### Server Setup (Optional):
```bash
# All students access from one server
pip install gunicorn
gunicorn --bind 0.0.0.0:5000 app:app
```

---

## 📞 Support & Help

### Common Commands

```bash
# Check Python version
python --version

# Check pip version
pip --version

# List installed packages
pip list

# Install specific version
pip install Flask==2.3.3

# Check if camera is detected
python -c "import cv2; print(cv2.VideoCapture(0).isOpened())"

# Check MediaPipe
python -c "import mediapipe; print('MediaPipe OK')"
```

### Getting Help

1. **Error in terminal?** - Copy error and read it carefully
2. **Camera issues?** - Test camera with other apps first
3. **Port issues?** - Change port number in app.py
4. **Slow?** - Close background apps
5. **Can't install?** - Try: `python -m pip install -r requirements.txt`

---

## 🚀 You're All Set!

Once installation is complete:

1. ✅ Python installed
2. ✅ Dependencies installed
3. ✅ Code extracted
4. ✅ Camera working
5. ✅ Flask app running
6. ✅ Browser displaying interface

**Ready to start detecting sign language! 🎉**

---

## 📝 Next Steps

1. Read: [README.md](README.md) - Full documentation
2. Learn: [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Architecture and viva prep
3. Reference: [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Quick commands
4. Try: [Code examples in README](README.md) - Extend the project

---

**Happy coding! 🎓**

For issues, check the Troubleshooting section or contact your instructor.
