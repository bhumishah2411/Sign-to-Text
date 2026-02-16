# ============================================================================
# PROJECT: Sign Language to Text Converter (Web-based)
# MODULE: Camera Video Capture and Processing
# PURPOSE: Handle webcam capture and convert frames to web-compatible format
# EXPLANATION: This module manages the camera input and provides frames
#              to the Flask backend via streaming. We use OpenCV because:
#              1. Industry standard for computer vision
#              2. Works with all webcams
#              3. Fast and efficient frame processing
#              4. Easy to capture and manipulate video
# ============================================================================

import cv2
import mediapipe as mp
import base64
import io
import numpy as np
import threading
import time
from collections import deque
from gesture_model import GestureRecognizer
from config import WEBCAM_WIDTH, WEBCAM_HEIGHT, WEBCAM_FPS

# Initialize gesture recognizer
gesture_recognizer = GestureRecognizer()
mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands


class CameraManager:
    """
    Manages webcam capture and frame processing.
    
    WHY THIS CLASS?
    - Encapsulates camera logic (single responsibility principle)
    - Easy to modify or swap different cameras
    - Clear interface for the Flask app
    """
    
    def __init__(self):
        """Initialize the camera manager"""
        self.camera = None
        self.is_running = False
        self.index = None
        self.startup_time = None
        self.time_module = time
        
        # Performance optimization: Frame buffering and caching
        self.latest_frame = None
        self.latest_gesture = None
        self.latest_detection_results = None  # Cache full detection results (landmarks + gesture)
        self.frame_lock = threading.Lock()
        self.capture_thread = None
        self.processing_thread = None
        
        # Frame rate control
        self.target_fps = 30
        self.last_frame_time = 0
        self.frame_interval = 1.0 / self.target_fps
        
        # Processing queue for async gesture detection
        self.frame_queue = deque(maxlen=2)  # Keep only latest 2 frames
        self.processing_enabled = True
    
    # ======================== CAMERA INITIALIZATION =============================
    
    def start_camera(self):
        """
        Open webcam connection.
        
        PARAMETER 0: Uses default webcam
        WHY VideoCapture(0)? Because 0 is the default/first camera on most systems
        
        RETURNS: True if camera opened successfully, False otherwise
        """
        # Clean up any existing camera first
        if self.camera is not None:
            print("[CAMERA] Cleaning up existing camera object before starting new one...")
            try:
                if self.camera.isOpened():
                    self.camera.release()
            except Exception:
                pass
            self.camera = None
            self.is_running = False
            self.index = None
        
        try:
            print("[CAMERA] Attempting to open camera (indices 0-5)...")

            # Try multiple camera indices to increase chance of finding available device
            for idx in range(0, 6):
                try:
                    print(f"[CAMERA] Trying index {idx}...")
                    cap = cv2.VideoCapture(idx)
                    if not cap or not cap.isOpened():
                        try:
                            cap.release()
                        except Exception:
                            pass
                        print(f"[CAMERA] Index {idx} not opened")
                        continue

                    # Successfully opened candidate camera; set properties
                    self.camera = cap
                    self.index = idx
                    
                    # Try to set properties (some cameras may not support all properties)
                    try:
                        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, WEBCAM_WIDTH)
                        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, WEBCAM_HEIGHT)
                        self.camera.set(cv2.CAP_PROP_FPS, WEBCAM_FPS)
                    except Exception as prop_error:
                        print(f"[CAMERA] Warning: Could not set some camera properties: {prop_error}")

                    # Give camera a moment to initialize
                    import time
                    time.sleep(0.3)

                    # Warm up the camera (more lenient - allow some failures)
                    print(f"[CAMERA] Warming up camera at index {idx}...")
                    warmup_success_count = 0
                    warmup_attempts = 5  # Reduced from 10 to 5
                    
                    for attempt in range(warmup_attempts):
                        ret, frame = self.camera.read()
                        if ret and frame is not None:
                            warmup_success_count += 1
                        time.sleep(0.1)  # Slightly longer delay between attempts

                    # Require at least 3 successful frames out of 5 (more lenient)
                    if warmup_success_count < 3:
                        print(f"[CAMERA] Warning: Warmup insufficient for index {idx} ({warmup_success_count}/{warmup_attempts} frames succeeded), trying next index")
                        try:
                            self.camera.release()
                        except Exception:
                            pass
                        self.camera = None
                        self.index = None
                        continue

                    # Final check - verify camera is still open and can read
                    if not self.camera or not self.camera.isOpened():
                        print(f"[CAMERA] Camera at index {idx} closed unexpectedly after warmup")
                        try:
                            if self.camera:
                                self.camera.release()
                        except Exception:
                            pass
                        self.camera = None
                        self.index = None
                        continue
                    
                    # One final test read to confirm it's working
                    ret, test_frame = self.camera.read()
                    if not ret or test_frame is None:
                        print(f"[CAMERA] Camera at index {idx} cannot read frames after warmup")
                        try:
                            self.camera.release()
                        except Exception:
                            pass
                        self.camera = None
                        self.index = None
                        continue

                    # Success! Camera is ready
                    self.is_running = True
                    self.startup_time = time.time()
                    
                    # Start background frame capture thread for better performance
                    self.capture_thread = threading.Thread(target=self._frame_capture_loop, daemon=True)
                    self.capture_thread.start()
                    
                    # Start background processing thread
                    self.processing_thread = threading.Thread(target=self._frame_processing_loop, daemon=True)
                    self.processing_thread.start()
                    
                    print(f"[CAMERA] ✅ Camera started successfully at index {idx}! (Warmup: {warmup_success_count}/{warmup_attempts} frames)")
                    print("[CAMERA] Background frame capture and processing threads started")
                    return True

                except Exception as e:
                    print(f"[CAMERA] Exception while trying index {idx}: {e}")
                    try:
                        if cap:
                            cap.release()
                    except Exception:
                        pass
                    self.camera = None
                    self.index = None
                    continue

            # If we get here, no camera could be opened
            print("[CAMERA] ❌ Error: Could not open any camera index 0-5!")
            print("[CAMERA] Troubleshooting tips:")
            print("  1. Check if camera is physically connected")
            print("  2. Check if another app is using the camera")
            print("  3. Ensure OS camera permissions are granted to apps")
            print("  4. Restart your computer")
            return False
            
        except Exception as e:
            print(f"[CAMERA ERROR] ❌ Failed to start camera: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # ======================== BACKGROUND FRAME CAPTURE (PERFORMANCE OPTIMIZATION) =============================
    
    def _frame_capture_loop(self):
        """
        Background thread that continuously captures frames from camera.
        This prevents blocking and ensures smooth frame rate.
        """
        while self.is_running:
            try:
                if not self.camera or not self.camera.isOpened():
                    time.sleep(0.1)
                    continue
                
                # Read frame from camera (fast operation)
                ret, frame = self.camera.read()
                
                if ret and frame is not None:
                    # Flip frame horizontally (mirror effect)
                    frame = cv2.flip(frame, 1)
                    
                    # Update latest frame atomically
                    with self.frame_lock:
                        self.latest_frame = frame.copy()
                        # Add to processing queue if processing is enabled
                        if self.processing_enabled:
                            self.frame_queue.append(frame.copy())
                else:
                    time.sleep(0.01)  # Small delay if frame read fails
                    
            except Exception as e:
                print(f"[CAMERA ERROR] Error in capture loop: {e}")
                time.sleep(0.1)
    
    def _frame_processing_loop(self):
        """
        Background thread that processes frames for gesture detection.
        Separates heavy MediaPipe processing from frame capture.
        """
        while self.is_running:
            try:
                # Process frames from queue
                if self.frame_queue:
                    frame = self.frame_queue.popleft()
                    
                    # Process frame for gesture detection (heavy operation)
                    detection_results = gesture_recognizer.process_frame(frame)
                    
                    detected_gesture = None
                    if detection_results['hand_landmarks']:
                        detected_gesture = detection_results['gestures'][0] if detection_results['gestures'] else None
                    
                    # Update latest gesture and detection results atomically (for drawing)
                    with self.frame_lock:
                        self.latest_gesture = detected_gesture
                        self.latest_detection_results = detection_results
                else:
                    time.sleep(0.05)  # Small delay if queue is empty
                    
            except Exception as e:
                print(f"[CAMERA ERROR] Error in processing loop: {e}")
                time.sleep(0.1)
    
    # ======================== FRAME CAPTURE AND PROCESSING =============================
    
    def get_frame_with_gesture(self, draw_landmarks=True):
        """
        Get latest frame and gesture from cache (optimized - no blocking).
        Uses background threads for capture and processing.
        
        OPTIMIZATION:
        - Returns cached frame/gesture from background threads
        - No blocking MediaPipe processing here
        - Draws landmarks/text on demand for display
        
        PARAMETER:
        - draw_landmarks: Whether to draw hand landmarks (default True for video feed)
        
        RETURNS: Tuple (frame, detected_gesture) or (None, None) if error
        """
        if not self.camera or not self.is_running:
            return None, None
        
        try:
            # Get latest frame, gesture, and detection results from cache (fast, non-blocking)
            with self.frame_lock:
                if self.latest_frame is None:
                    return None, None
                
                frame = self.latest_frame.copy()
                detected_gesture = self.latest_gesture
                detection_results = self.latest_detection_results  # Use cached results
            
            # Only draw landmarks/text if requested (for video feed)
            # Skip drawing for detection API calls to save time
            if draw_landmarks and detection_results:
                # Draw hand skeleton and landmarks only if hands detected (using cached results)
                if detection_results.get('hand_landmarks'):
                    for hand_landmarks in detection_results['hand_landmarks']:
                        mp_drawing.draw_landmarks(
                            frame,
                            hand_landmarks,
                            mp_hands.HAND_CONNECTIONS,
                            mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2),
                            mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=2)
                        )
                
                # Display gesture on frame if detected
                if detected_gesture:
                    cv2.putText(
                        frame,
                        f"ISL: {detected_gesture}",
                        (20, 50),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1.2,
                        (0, 255, 0),
                        2
                    )
                else:
                    cv2.putText(
                        frame,
                        "No ISL gesture detected",
                        (20, 50),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1.0,
                        (0, 0, 255),
                        2
                    )
                
                # Add instruction text
                cv2.putText(
                    frame,
                    "Make hand gestures in front of camera",
                    (20, frame.shape[0] - 20),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    1
                )
            
            return frame, detected_gesture
            
        except Exception as e:
            print(f"[CAMERA ERROR] Error getting frame: {e}")
            return None, None
    
    # ======================== FRAME TO BASE64 CONVERSION =============================
    
    def frame_to_base64(self, frame):
        """
        Convert OpenCV frame to base64 string for sending to web frontend.
        
        WHY BASE64?
        - It's a text format that can be sent over HTTP
        - Can be directly embedded in HTML img tag
        - Safe for network transmission
        
        PROCESS:
        1. Encode frame to JPEG bytes
        2. Encode bytes to base64 string
        3. Return string
        
        PARAMETER: frame - OpenCV frame (numpy array)
        RETURNS: Base64 encoded string
        """
        if frame is None:
            return None
        
        try:
            # Encode frame as JPEG
            # Why JPEG? Small file size, good quality, web-compatible
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
            
            # Convert bytes to base64 string
            frame_base64 = base64.b64encode(buffer).decode('utf-8')
            
            return frame_base64
            
        except Exception as e:
            print(f"[CAMERA ERROR] Error converting frame to base64: {e}")
            return None

    def process_uploaded_frame_bytes(self, file_bytes):
        """
        Process raw image bytes uploaded by client and run gesture detection.

        INPUT: file_bytes (raw bytes of an image file, e.g., JPEG/PNG)
        RETURNS: (frame (BGR numpy array), detected_gesture or None)
        """
        try:
            if not file_bytes:
                return None, None

            # Convert bytes to numpy array and decode image
            nparr = np.frombuffer(file_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if frame is None:
                print("[CAMERA] Uploaded image could not be decoded")
                return None, None

            # Mirror for consistency with webcam frames
            frame = cv2.flip(frame, 1)

            # Run gesture detection on the uploaded frame
            detection_results = gesture_recognizer.process_frame(frame)
            detected_gesture = detection_results['gestures'][0] if detection_results['gestures'] else None

            return frame, detected_gesture
        except Exception as e:
            print(f"[CAMERA ERROR] Error processing uploaded image bytes: {e}")
            return None, None
    
    # ======================== STREAM GENERATOR =============================
    
    def get_frame_stream(self):
        """
        Generator function for continuous video streaming (OPTIMIZED).
        
        OPTIMIZATIONS:
        - Uses cached frames from background thread (no blocking)
        - FPS control to prevent overwhelming browser
        - Lower JPEG quality for faster encoding
        
        YIELDS: MJPEG-formatted frame data
        """
        frame_skip_count = 0
        
        while self.is_running:
            try:
                # FPS control: ensure we don't exceed target frame rate
                current_time = time.time()
                elapsed = current_time - self.last_frame_time
                
                if elapsed < self.frame_interval:
                    time.sleep(self.frame_interval - elapsed)
                
                self.last_frame_time = time.time()
                
                # Get frame with drawings (for video feed)
                frame, gesture = self.get_frame_with_gesture(draw_landmarks=True)
                
                if frame is None:
                    frame_skip_count += 1
                    if frame_skip_count > 30:
                        print("[CAMERA] Warning: No frames captured for 30 cycles")
                        frame_skip_count = 0
                    time.sleep(0.033)  # ~30 FPS fallback
                    continue
                
                frame_skip_count = 0
                
                # Encode frame as JPEG bytes (optimized quality for speed)
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                frame_bytes = buffer.tobytes()
                
                # Yield in proper MJPEG format
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n'
                       b'Content-Length: ' + str(len(frame_bytes)).encode() + b'\r\n\r\n'
                       + frame_bytes + b'\r\n')
                       
            except Exception as e:
                print(f"[CAMERA ERROR] Error in frame stream: {e}")
                time.sleep(0.1)
                continue
    
    # ======================== CAMERA CLEANUP =============================
    
    def stop_camera(self):
        """
        Stop camera and release resources.
        
        IMPORTANT: Always release camera when done!
        If you don't, the camera stays locked and you can't use it again
        until you restart Python.
        """
        # Stop background threads first
        self.is_running = False
        
        # Wait for threads to finish (with timeout)
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=1.0)
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=1.0)
        
        if self.camera:
            elapsed = None
            if self.startup_time:
                elapsed = time.time() - self.startup_time
                print(f"[CAMERA] Camera was running for {elapsed:.2f} seconds")
            
            try:
                self.camera.release()
                print(f"[CAMERA] Camera released successfully at index {self.index}")
            except Exception as e:
                print(f"[CAMERA] Error releasing camera: {e}")
            
            self.index = None
            self.startup_time = None
            
            # Clear frame cache
            with self.frame_lock:
                self.latest_frame = None
                self.latest_gesture = None
                self.latest_detection_results = None
                self.frame_queue.clear()
            
            print("[CAMERA] Camera stopped and resources released!")
    
    # ======================== STATUS CHECK =============================
    
    def is_camera_available(self):
        """Check if camera is available and running"""
        return self.is_running and self.camera is not None
