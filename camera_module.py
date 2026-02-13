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
        import time
        self.time_module = time
    
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
                    import time as time_module
                    self.startup_time = time_module.time()
                    print(f"[CAMERA] ✅ Camera started successfully at index {idx}! (Warmup: {warmup_success_count}/{warmup_attempts} frames)")
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
    
    # ======================== FRAME CAPTURE AND PROCESSING =============================
    
    def get_frame_with_gesture(self):
        """
        Capture frame from camera and process for gesture detection.
        
        STEPS:
        1. Read frame from camera
        2. Mirror it (so it looks like user is looking at mirror)
        3. Detect hand gestures
        4. Draw hand skeleton on frame
        5. Add text showing detected gesture
        6. Return processed frame
        
        RETURNS: Tuple (frame, detected_gesture) or (None, None) if error
        """
        if not self.camera or not self.is_running:
            return None, None
        
        try:
            # Read frame from camera
            ret, frame = self.camera.read()
            
            if not ret:
                # Check if camera is still open
                if self.camera:
                    is_open = self.camera.isOpened()
                    print(f"[CAMERA] Frame read failed: ret={ret}, isOpened={is_open}, index={self.index}")
                    if not is_open:
                        print("[CAMERA] Camera closed unexpectedly; resetting is_running flag")
                        self.is_running = False
                else:
                    print("[CAMERA] Frame read failed: camera object is None")
                return None, None
            
            # Flip frame horizontally (mirror effect - more intuitive for user)
            frame = cv2.flip(frame, 1)
            
            # Process frame to detect gestures
            # This calls our gesture_model.py to analyze hand landmarks
            detection_results = gesture_recognizer.process_frame(frame)
            
            detected_gesture = None
            
            # Draw hand skeleton and landmarks only if hands detected (reduces drawing overhead)
            if detection_results['hand_landmarks']:
                for hand_landmarks in detection_results['hand_landmarks']:
                    mp_drawing.draw_landmarks(
                        frame,
                        hand_landmarks,
                        mp_hands.HAND_CONNECTIONS,
                        mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2),
                        mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=2)
                    )
                # Get detected gesture (if any)
                detected_gesture = detection_results['gestures'][0] if detection_results['gestures'] else None
            
            # Display gesture on frame if detected
            if detected_gesture:
                # Put green text on frame showing the detected gesture
                cv2.putText(
                    frame,
                    f"ISL: {detected_gesture}",
                    (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.2,
                    (0, 255, 0),  # Green color for positive detection
                    2
                )
            else:
                # Put red text if no gesture detected
                cv2.putText(
                    frame,
                    "No ISL gesture detected",
                    (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.0,
                    (0, 0, 255),  # Red color for no detection
                    2
                )
            
            # Add instruction text
            cv2.putText(
                frame,
                "Make hand gestures in front of camera",
                (20, frame.shape[0] - 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),  # White instruction text
                1
            )
            
            return frame, detected_gesture
            
        except Exception as e:
            print(f"[CAMERA ERROR] Error processing frame: {e}")
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
        Generator function for continuous video streaming.
        
        WHAT IS A GENERATOR?
        - A function that yields values one at a time
        - Useful for streaming (continuous data)
        - Used by Flask to send video stream to browser
        
        PROCESS:
        1. Continuously capture frames
        2. Process each frame for gesture detection
        3. Convert to JPEG bytes
        4. Yield frame data in MJPEG format
        
        MJPEG = Motion JPEG (sequence of JPEG images)
        This is how browser displays video
        
        YIELDS: MJPEG-formatted frame data
        """
        frame_skip_count = 0
        
        while self.is_running:
            try:
                frame, gesture = self.get_frame_with_gesture()
                
                if frame is None:
                    # Skip frames that failed to capture
                    frame_skip_count += 1
                    if frame_skip_count > 30:  # Log after 30 skipped frames
                        print("[CAMERA] Warning: No frames captured for 30 cycles")
                        frame_skip_count = 0
                    continue
                
                frame_skip_count = 0  # Reset skip counter on successful frame
                
                # Encode frame as JPEG bytes directly (not base64)
                # Use lower quality (70) to reduce file size and improve speed
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 65])
                frame_bytes = buffer.tobytes()
                
                # Yield in proper MJPEG format
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n'
                       b'Content-Length: ' + str(len(frame_bytes)).encode() + b'\r\n\r\n'
                       + frame_bytes + b'\r\n')
                       
            except Exception as e:
                print(f"[CAMERA ERROR] Error in frame stream: {e}")
                continue
    
    # ======================== CAMERA CLEANUP =============================
    
    def stop_camera(self):
        """
        Stop camera and release resources.
        
        IMPORTANT: Always release camera when done!
        If you don't, the camera stays locked and you can't use it again
        until you restart Python.
        """
        if self.camera:
            elapsed = None
            if self.startup_time:
                import time as time_module
                elapsed = time_module.time() - self.startup_time
                print(f"[CAMERA] Camera was running for {elapsed:.2f} seconds")
            self.is_running = False
            try:
                self.camera.release()
                print(f"[CAMERA] Camera released successfully at index {self.index}")
            except Exception as e:
                print(f"[CAMERA] Error releasing camera: {e}")
            self.index = None
            self.startup_time = None
            print("[CAMERA] Camera stopped and resources released!")
    
    # ======================== STATUS CHECK =============================
    
    def is_camera_available(self):
        """Check if camera is available and running"""
        return self.is_running and self.camera is not None
