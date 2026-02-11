# ============================================================================
# PROJECT: Sign Language to Text Converter (Web-based)
# MAIN FILE: Flask Backend Application
# PURPOSE: Main web application that connects all modules together
# EXPLANATION: Flask is used because:
#              1. Lightweight Python web framework (perfect for college)
#              2. Easy to learn and understand
#              3. Routes incoming requests to appropriate handlers
#              4. Renders HTML templates and serves static files
# ============================================================================

from flask import Flask, render_template, Response, jsonify, request
from datetime import datetime
import os
import cv2
import base64
import atexit

# Import our custom modules
from config import DEBUG, SECRET_KEY, GESTURE_LIST
from database import initialize_database, save_prediction, get_all_predictions, get_recent_predictions, get_prediction_statistics, clear_all_predictions
from camera_module import CameraManager
from gesture_model import GestureRecognizer

# ======================== FLASK APP INITIALIZATION =============================

# Create Flask application instance
# __name__ tells Flask where to find templates and static folders
app = Flask(__name__)

# Security and configuration settings
app.config['DEBUG'] = DEBUG
app.config['SECRET_KEY'] = SECRET_KEY

# ======================== GLOBAL VARIABLES =============================

# Initialize camera manager
camera_manager = CameraManager()

# Initialize gesture recognizer
gesture_recognizer = GestureRecognizer()

# Flag to track if camera is running
camera_active = False

# Store last detected gesture to avoid duplicate entries
last_detected_gesture = None
frame_counter = 0
detection_threshold = 2  # Very fast confirmation (just 2 frames)


# ======================== DATABASE AND APP STARTUP =============================

def startup():
    """
    Run once when Flask app starts.
    Initialize database and other resources.
    """
    initialize_database()

# Initialize database once at import/startup (NOT on every request)
startup()


# Initialize on app startup - ensure clean state
print("[INIT] Resetting camera state on startup...")
camera_active = False
if camera_manager:
    camera_manager.is_running = False

# ======================== HOME PAGE ROUTE =============================

@app.route('/')
def index():
    """
    Main page route.
    When user visits http://localhost:5000/ this function runs.
    
    PROCESS:
    1. Render the HTML template (index.html)
    2. Pass gesture list to template (for display)
    3. Send HTML to browser
    
    RETURNS: Rendered HTML page
    """
    # Get statistics to show on dashboard
    stats = get_prediction_statistics()
    
    # Render index.html template and pass data
    return render_template('index.html', 
                         gestures=GESTURE_LIST,
                         stats=stats)


# ======================== DIAGNOSTIC ROUTE =============================

@app.route('/api/camera_status')
def camera_status():
    """
    Diagnostic endpoint to check camera status
    """
    return jsonify({
        'camera_active': camera_active,
        'camera_object_exists': camera_manager.camera is not None,
        'camera_is_running': camera_manager.is_running if camera_manager else False,
        'is_opened': camera_manager.camera.isOpened() if camera_manager and camera_manager.camera else False,
        'camera_index': camera_manager.index if camera_manager else None
    }), 200


@app.route('/api/frame')
def get_current_frame():
    """
    API endpoint to get current camera frame as base64 JPEG.
    Used by JavaScript to continuously update video display.
    
    RETURNS: JSON with base64-encoded JPEG frame and status
    """
    global camera_active

    try:
        # If camera object or running flag is bad, treat as fully stopped
        if (not camera_active or
            not camera_manager.camera or
            not camera_manager.is_running):
            camera_active = False
            return jsonify({'frame': None, 'status': 'no_camera'}), 200
        
        # Get current frame
        frame, gesture = camera_manager.get_frame_with_gesture()
        
        if frame is None:
            # Camera is "on" but not providing frames
            return jsonify({'frame': None, 'status': 'no_frame'}), 200
        
        # Encode frame as JPEG and convert to base64 (reduced quality for speed)
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 65])
        frame_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # Log success once per 10 frames to track activity (not spam)
        if frame_counter % 10 == 0:
            print(f"[FRAME] Successfully encoded frame at {datetime.now().isoformat()}")
        
        return jsonify({
            'frame': frame_base64,
            'status': 'success',
            'gesture': gesture
        }), 200
        
    except Exception as e:
        print(f"[ERROR] Error getting frame: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'frame': None, 'status': 'error', 'message': str(e)}), 200


# ======================== CAMERA CONTROL ROUTES =============================

@app.route('/start_camera', methods=['POST'])
def start_camera_route():
    """
    API endpoint to start the camera.
    Called when user clicks "Start Camera" button.
    
    PROCESS:
    1. If camera already running, just return success (idempotent)
    2. Otherwise, start camera manager
    3. Set flag to active
    4. Return JSON response
    
    RETURNS: JSON with status (always 200 on success)
    """
    global camera_active
    
    try:
        print(f"[START_CAMERA] Request from {request.remote_addr} at {datetime.now().isoformat()}")
        if camera_active:
            # Camera already running - that's OK, just return success
            # This makes the endpoint idempotent (safe to call multiple times)
            print("[START_CAMERA] Camera already active; returning idempotent success")
            return jsonify({'status': 'success', 'message': 'Camera is already running', 'camera_index': camera_manager.index}), 200
        
        # Start the camera
        success = camera_manager.start_camera()
        
        if success:
            camera_active = True
            return jsonify({'status': 'success', 'message': 'Camera started!', 'camera_index': camera_manager.index}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Failed to start camera', 'hint': 'Check if camera is connected or already in use', 'camera_index': camera_manager.index}), 200
            
    except Exception as e:
        print(f"[ERROR] Error starting camera: {e}")
        return jsonify({'status': 'error', 'message': str(e), 'hint': 'Camera error. Try restarting the browser.'}), 200


@app.route('/stop_camera', methods=['POST'])
def stop_camera_route():
    """
    API endpoint to stop the camera.
    Called when user clicks "Stop Camera" button.
    
    PROCESS:
    1. Check if camera is running
    2. Stop camera manager and clean up resources
    3. Set flag to inactive
    4. Return JSON response
    
    RETURNS: JSON with status
    """
    global camera_active
    
    try:
        print(f"[STOP_CAMERA] Request from {request.remote_addr} at {datetime.now().isoformat()}")
        if camera_active:
            print("[STOP_CAMERA] Stopping active camera...")
            camera_manager.stop_camera()
            camera_active = False
            print("[STOP_CAMERA] ✅ Camera stopped successfully")
            return jsonify({
                'status': 'success',
                'message': 'Camera stopped!',
                'timestamp': datetime.now().isoformat()
            }), 200
        else:
            # Camera not running - treat as success (idempotent)
            print("[STOP_CAMERA] Camera already stopped; returning idempotent success")
            return jsonify({
                'status': 'success',
                'message': 'Camera not running (already stopped)',
                'timestamp': datetime.now().isoformat()
            }), 200
            
    except Exception as e:
        print(f"[ERROR] Exception stopping camera: {e}")
        import traceback
        traceback.print_exc()
        # Still return 200 to prevent UI errors
        return jsonify({
            'status': 'success',
            'message': 'Stop request processed',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 200


# ======================== VIDEO STREAMING ROUTE =============================

@app.route('/video_feed')
def video_feed():
    """
    Stream video from camera to web browser.
    This is a continuous video stream endpoint.
    
    HOW STREAMING WORKS:
    1. Browser requests /video_feed
    2. Flask calls generator function (camera_manager.get_frame_stream())
    3. Generator yields frame data one at a time
    4. Browser receives stream of JPEG frames (MJPEG format)
    5. Browser displays frames as video
    
    WHY STREAM?
    - Efficient for large data (video frames)
    - Can handle continuous updates
    - Works with all modern browsers
    
    RETURNS: Stream of video frames in MJPEG format
    """
    if not camera_active:
        print("[VIDEO_FEED] Camera not active, returning error")
        return "Camera not active", 400
    
    # Check if camera manager has valid camera
    if not camera_manager.camera or not camera_manager.is_running:
        print("[VIDEO_FEED] Camera object not available")
        return "Camera not initialized", 400
    
    print("[VIDEO_FEED] Starting video stream...")
    
    # Response with MJPEG format
    return Response(
        camera_manager.get_frame_stream(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


# ======================== GESTURE DETECTION AND STORAGE =============================

@app.route('/api/detect_gesture', methods=['POST'])
def detect_gesture_route():
    """
    API endpoint to capture current frame and detect gesture.
    Called periodically by JavaScript to get detected gesture.
    
    PROCESS:
    1. Skip frames for faster processing (process every Nth frame)
    2. Get current frame from camera
    3. Detect gesture from frame
    4. If gesture detected and confident, save to database
    5. Return gesture data as JSON (ALWAYS returns 200, never 400)
    
    RETURNS: JSON with detected gesture and metadata
    """
    global last_detected_gesture, frame_counter, frame_skip_count
    
    try:
        # Check if camera is active - if not, return safe 200 response
        if not camera_active:
            return jsonify({
                'status': 'success',
                'gesture': None,
                'saved': False,
                'message': 'Camera not active',
                'timestamp': datetime.now().isoformat()
            }), 200

        # Get current frame from server-side camera
        frame, detected_gesture = camera_manager.get_frame_with_gesture()

        # If frame is None (camera not ready), return safe 200 response
        if frame is None:
            return jsonify({
                'status': 'success',
                'gesture': None,
                'saved': False,
                'message': 'No frame available',
                'timestamp': datetime.now().isoformat()
            }), 200
        
        # Confidence system: need multiple consecutive frames with same gesture
        if detected_gesture == last_detected_gesture:
            frame_counter += 1
        else:
            frame_counter = 1
            last_detected_gesture = detected_gesture
        
        # Only save if we're confident (threshold reached) - now 3 instead of 5
        saved = False
        if detected_gesture and frame_counter >= detection_threshold:
            if save_prediction(detected_gesture, confidence=0.9):
                saved = True
                frame_counter = 0  # Reset counter
        
        # ALWAYS return 200 - never return error status for normal operation
        return jsonify({
            'status': 'success',
            'gesture': detected_gesture,
            'saved': saved,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        # Even on error, return 200 with error info - prevents 400 spam
        print(f"[ERROR] Error detecting gesture: {e}")
        return jsonify({
            'status': 'success',
            'gesture': None,
            'saved': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 200


# ======================== DATA RETRIEVAL ROUTES =============================

@app.route('/api/predictions', methods=['GET'])
def get_predictions():
    """
    API endpoint to get all stored predictions.
    Called by JavaScript to display history on webpage.
    
    QUERY PARAMETERS:
    - limit (optional): Number of recent predictions to retrieve
    
    RETURNS: JSON array of predictions
    """
    try:
        # Get limit from query parameters (default = all)
        limit = request.args.get('limit', type=int)
        
        if limit:
            predictions = get_recent_predictions(limit=limit)
        else:
            predictions = get_all_predictions()
        
        return jsonify({
            'status': 'success',
            'predictions': predictions
        }), 200
        
    except Exception as e:
        print(f"[ERROR] Error retrieving predictions: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/statistics', methods=['GET'])
def get_stats():
    """
    API endpoint to get prediction statistics.
    Called by JavaScript to update dashboard.
    
    RETURNS: JSON with statistics (total, unique, most detected)
    """
    try:
        stats = get_prediction_statistics()
        
        return jsonify({
            'status': 'success',
            'statistics': stats
        }), 200
        
    except Exception as e:
        print(f"[ERROR] Error retrieving statistics: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ======================== CLEAR DATA ROUTE =============================

@app.route('/api/clear_data', methods=['POST'])
def clear_data():
    """
    API endpoint to clear all predictions from database.
    Called when user clicks "Clear History" button.
    
    RETURNS: JSON with status (always 200 for consistency)
    """
    try:
        print("[CLEAR_DATA] Request to clear all predictions...")
        success = clear_all_predictions()
        
        if success:
            print("[CLEAR_DATA] ✅ Data cleared successfully!")
            return jsonify({
                'status': 'success',
                'message': 'All data cleared!',
                'timestamp': datetime.now().isoformat()
            }), 200
        else:
            print("[CLEAR_DATA] ❌ Failed to clear data - database error")
            return jsonify({
                'status': 'error',
                'message': 'Failed to clear data - database error',
                'timestamp': datetime.now().isoformat()
            }), 200  # Return 200 to be consistent with other endpoints
            
    except Exception as e:
        print(f"[ERROR] Exception clearing data: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'Exception: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 200  # Return 200 to be consistent with other endpoints


# ======================== ERROR HANDLERS =============================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors (page not found)"""
    return jsonify({'status': 'error', 'message': 'Route not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors (server error)"""
    print(f"[ERROR] Server error: {error}")
    return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


# ======================== CLEANUP ON APP SHUTDOWN =============================

def cleanup_resources():
    """
    Clean up resources when Flask app shuts down (process exit).
    IMPORTANT: Do NOT do this in teardown_appcontext, because that runs after
    every request and would immediately stop the camera.
    """
    global camera_active
    try:
        try:
            if camera_manager and getattr(camera_manager, "is_running", False):
                camera_manager.stop_camera()
        except Exception:
            pass

        camera_active = False

        if 'gesture_recognizer' in globals() and gesture_recognizer is not None:
            if hasattr(gesture_recognizer, 'close'):
                try:
                    gesture_recognizer.close()
                except Exception:
                    pass

        print("[APP] Cleanup completed!")
    except Exception as e:
        print(f"[ERROR] Error during cleanup: {e}")

# Ensure cleanup runs once when the Python process exits
atexit.register(cleanup_resources)


# ======================== MAIN APPLICATION RUN =============================

if __name__ == '__main__':
    """
    Entry point of the application.
    This runs only if you execute this file directly (not imported).
    
    HOW TO RUN:
    1. Open terminal in project folder
    2. Type: python app.py
    3. Open browser and go to http://localhost:5000
    
    DEBUG=True means:
    - Server reloads automatically when you change code
    - Shows error details in browser
    - Good for development, bad for production
    """
    print("=" * 60)
    print("Indian Sign Language (ISL) to Text Converter - Flask App")
    print("Starting server...")
    print("Open browser and go to: http://localhost:5000")
    print("Press CTRL+C to stop the server")
    print("=" * 60)
    
    # Run Flask development server
    # host='0.0.0.0' = accessible from any IP on network
    # port=5000 = default Flask port
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
