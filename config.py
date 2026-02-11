# ============================================================================
# PROJECT: Sign Language to Text Converter (Web-based)
# MODULE: Configuration Settings
# PURPOSE: Centralized configuration for the Flask application
# EXPLANATION: This file stores all constant values used throughout the app
#              so they can be easily modified without changing core logic.
# ============================================================================

import os

# Get the base directory of the project
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# ======================== FLASK CONFIGURATION =============================
# Flask settings for the web application
DEBUG = True  # Enable debug mode for development (shows errors clearly)
SECRET_KEY = 'sign_language_converter_secret_key_2024'  # Used for session security

# ======================== DATABASE CONFIGURATION =============================
# SQLite database settings
DATABASE_PATH = os.path.join(BASE_DIR, 'sign_language_database.db')
# SQLite is lightweight and doesn't need a server - perfect for college projects

# ======================== UPLOAD FOLDER CONFIGURATION =============================
# Folder where captured frames will be stored (optional)
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ======================== GESTURE RECOGNITION CONFIGURATION =============================
# Gesture detection settings
MIN_DETECTION_CONFIDENCE = 0.65  # Reduced from 0.7 for faster processing (still accurate)
MIN_TRACKING_CONFIDENCE = 0.45   # Reduced from 0.5 for better tracking consistency

# Gesture list - Indian Sign Language (ISL) Signs
# Following ISL conventions, not ASL
GESTURE_LIST = [
    'YES',           # ISL fist-based sign (closed fist)
    'NO',            # ISL pinched-finger sign
    'GOOD',          # Thumbs up gesture
    'BAD',           # Thumbs down gesture
    'OK',            # Index and thumb circle, other fingers open
    'HELLO',         # Open palm raised
    'STOP',          # One vertical hand blocking horizontal hand
    'HELP',          # Thumbs-up on open palm
    'THANK YOU',     # Flat hand near chin
    'PLEASE'         # Flat hand on chest
]

# ======================== VIDEO CONFIGURATION =============================
# Webcam and video settings
WEBCAM_WIDTH = 640   # Resolution width
WEBCAM_HEIGHT = 480  # Resolution height
WEBCAM_FPS = 30      # Frames per second
