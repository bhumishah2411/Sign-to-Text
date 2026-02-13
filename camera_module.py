# ============================================================================
# PROJECT: Sign Language to Text Converter (Web-based)
# MODULE: Camera Video Capture and Processing
# PURPOSE: Handle webcam capture and convert frames to web-compatible format
# OPTIMIZED VERSION: Improved performance & reduced camera hanging
# ============================================================================

import cv2
import mediapipe as mp
import base64
import numpy as np
from gesture_model import GestureRecognizer
from config import WEBCAM_WIDTH, WEBCAM_HEIGHT, WEBCAM_FPS
import time

# Initialize gesture recognizer
gesture_recognizer = GestureRecognizer()

mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands


class CameraManager:

    def __init__(self):
        self.camera = None
        self.is_running = False
        self.index = None
        self.startup_time = None
        self.process_counter = 0  # For skipping heavy ML processing

    # ======================== CAMERA INITIALIZATION =============================

    def start_camera(self):

        if self.camera is not None:
            try:
                if self.camera.isOpened():
                    self.camera.release()
            except Exception:
                pass

        try:
            print("[CAMERA] Searching for available camera...")

            for idx in range(0, 3):  # Reduced range for faster startup
                cap = cv2.VideoCapture(idx)

                if not cap or not cap.isOpened():
                    continue

                self.camera = cap
                self.index = idx

                # Set resolution and FPS
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, WEBCAM_WIDTH)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, WEBCAM_HEIGHT)
                self.camera.set(cv2.CAP_PROP_FPS, WEBCAM_FPS)

                time.sleep(0.3)

                ret, test_frame = self.camera.read()
                if not ret:
                    self.camera.release()
                    continue

                self.is_running = True
                self.startup_time = time.time()
                print(f"[CAMERA] ✅ Camera started at index {idx}")
                return True

            print("[CAMERA] ❌ No camera found.")
            return False

        except Exception as e:
            print(f"[CAMERA ERROR] {e}")
            return False

    # ======================== FRAME CAPTURE & GESTURE PROCESSING =============================

    def get_frame_with_gesture(self):

        if not self.camera or not self.is_running:
            return None, None

        try:
            ret, frame = self.camera.read()
            if not ret:
                return None, None

            # Resize frame (major performance improvement)
            frame = cv2.resize(frame, (640, 480))

            # Mirror effect
            frame = cv2.flip(frame, 1)

            detected_gesture = None

            # Only process gesture every 2 frames (reduces CPU load)
            self.process_counter += 1

            if self.process_counter % 2 == 0:
                detection_results = gesture_recognizer.process_frame(frame)

                if detection_results["hand_landmarks"]:
                    for hand_landmarks in detection_results["hand_landmarks"]:
                        mp_drawing.draw_landmarks(
                            frame,
                            hand_landmarks,
                            mp_hands.HAND_CONNECTIONS
                        )

                    if detection_results["gestures"]:
                        detected_gesture = detection_results["gestures"][0]

            # Display status text
            if detected_gesture:
                cv2.putText(
                    frame,
                    f"ISL: {detected_gesture}",
                    (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0),
                    2
                )
            else:
                cv2.putText(
                    frame,
                    "No ISL gesture detected",
                    (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 0, 255),
                    2
                )

            return frame, detected_gesture

        except Exception as e:
            print(f"[CAMERA ERROR] {e}")
            return None, None

    # ======================== FRAME TO BASE64 =============================

    def frame_to_base64(self, frame):

        if frame is None:
            return None

        try:
            _, buffer = cv2.imencode(
                '.jpg',
                frame,
                [cv2.IMWRITE_JPEG_QUALITY, 70]
            )

            return base64.b64encode(buffer).decode('utf-8')

        except Exception as e:
            print(f"[CAMERA ERROR] {e}")
            return None

    # ======================== STREAM GENERATOR =============================

    def get_frame_stream(self):

        frame_counter = 0

        while self.is_running:
            try:
                frame_counter += 1

                # Skip alternate frames (huge performance boost)
                if frame_counter % 2 != 0:
                    continue

                frame, gesture = self.get_frame_with_gesture()

                if frame is None:
                    continue

                _, buffer = cv2.imencode(
                    '.jpg',
                    frame,
                    [cv2.IMWRITE_JPEG_QUALITY, 55]  # Lower quality = faster
                )

                frame_bytes = buffer.tobytes()

                yield (
                    b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' +
                    frame_bytes +
                    b'\r\n'
                )

                # Prevent 100% CPU usage
                time.sleep(0.01)

            except Exception as e:
                print(f"[STREAM ERROR] {e}")
                continue

    # ======================== CAMERA CLEANUP =============================

    def stop_camera(self):

        if self.camera:
            self.is_running = False
            try:
                self.camera.release()
                print("[CAMERA] Released successfully")
            except Exception as e:
                print(f"[CAMERA ERROR] {e}")

            self.camera = None
            self.index = None
            self.startup_time = None

    # ======================== STATUS CHECK =============================

    def is_camera_available(self):
        return self.is_running and self.camera is not None
