# ============================================================================
# PROJECT: Sign Language to Text Converter (Web-based)
# MODULE: Gesture Recognition Model
# PURPOSE: Detect hand gestures from MediaPipe hand landmarks
# EXPLANATION: This module contains the logic to recognize different gestures.
#              We use MediaPipe (Google's pre-trained model) instead of 
#              building our own ML model because:
#              1. Pre-trained models work great out-of-the-box
#              2. No GPU needed
#              3. Easier to explain and maintain
#              4. Suitable for college projects
# ============================================================================

import mediapipe as mp
import cv2
import math
from config import MIN_DETECTION_CONFIDENCE, MIN_TRACKING_CONFIDENCE

# ======================== INITIALIZE MEDIAPIPE =============================
# MediaPipe is a Google framework for building ML pipelines
# We use it for hand detection and landmark extraction

mp_hands = mp.solutions.hands  # Solution for hand tracking
mp_drawing = mp.solutions.drawing_utils  # Utilities to draw landmarks


class GestureRecognizer:
    """
    Main class for gesture recognition.
    
    HOW IT WORKS:
    1. Receives video frames from the camera
    2. Detects hands and their landmarks (21 key points on hand)
    3. Analyzes finger positions to identify the gesture
    4. Returns the recognized gesture name
    """
    
    def __init__(self):
        """Initialize the gesture recognizer with MediaPipe Hands"""
        self.hands = mp_hands.Hands(
            static_image_mode=False,  # Process video, not static images
            max_num_hands=2,  # Detect up to 2 hands
            min_detection_confidence=MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=MIN_TRACKING_CONFIDENCE
        )
    
    # ======================== FINGER STATE DETECTION =============================
    
    def get_finger_state(self, landmarks):
        """
        Determine which fingers are extended or folded.
        
        MEDIAPIPE HAND LANDMARKS:
        - Finger tips: thumb=4, index=8, middle=12, ring=16, pinky=20
        - PIP joints: thumb=3, index=6, middle=10, ring=14, pinky=18
        - MCP joints: thumb=2, index=5, middle=9, ring=13, pinky=17
        
        LOGIC:
        A finger is "extended" if its tip is further from the hand center
        than the PIP joint (middle joint).
        
        PARAMETER: landmarks - 21 hand landmark points from MediaPipe
        RETURNS: Dictionary showing which fingers are extended
        """
        # Check if each finger is extended (tip beyond PIP joint)
        thumb_extended = landmarks[4].x < landmarks[3].x  # Thumb opens to side
        index_extended = landmarks[8].y < landmarks[6].y   # Index extends up
        middle_extended = landmarks[12].y < landmarks[10].y
        ring_extended = landmarks[16].y < landmarks[14].y
        pinky_extended = landmarks[20].y < landmarks[18].y
        
        return {
            'thumb': thumb_extended,
            'index': index_extended,
            'middle': middle_extended,
            'ring': ring_extended,
            'pinky': pinky_extended
        }
    
    # ======================== DISTANCE CALCULATION =============================
    
    def calculate_distance(self, point1, point2):
        """
        Calculate Euclidean distance between two hand landmarks.
        Used to detect if fingers are touching (e.g., OK sign).
        
        FORMULA: distance = sqrt((x2-x1)² + (y2-y1)² + (z2-z1)²)
        
        PARAMETERS:
        - point1, point2: Landmark objects with x, y, z coordinates
        
        RETURNS: Distance value (0 to 1, where 1 is full hand width)
        """
        return math.sqrt(
            (point1.x - point2.x)**2 + 
            (point1.y - point2.y)**2 + 
            (point1.z - point2.z)**2
        )
    
    # ======================== GESTURE DETECTION LOGIC =============================
    
    def detect_gesture(self, landmarks):
        """
        Main gesture detection function for Indian Sign Language (ISL).
        Analyzes finger positions and returns the detected gesture.
        
        INDIAN SIGN LANGUAGE (ISL) CONVENTIONS:
        - YES: Closed fist
        - NO: Pinched fingers (index and thumb touching)
        - GOOD: Thumbs up
        - BAD: Thumbs down
        - OK: Thumb and index circle with open fingers
        - HELLO: Open palm raised (all fingers extended)
        - STOP: Vertical blocking horizontal hand (requires 2 hands)
        - HELP: Thumbs up on open palm
        - THANK YOU: Flat hand near chin
        - PLEASE: Flat hand on chest
        
        PARAMETER: landmarks - 21 hand landmark points
        RETURNS: Gesture name (string) or None if no gesture detected
        """
        
        # Get which fingers are extended
        fingers = self.get_finger_state(landmarks)
        
        # Get important landmark positions
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        middle_tip = landmarks[12]
        ring_tip = landmarks[16]
        pinky_tip = landmarks[20]
        wrist = landmarks[0]
        
        # ==================== INDIAN SIGN LANGUAGE (ISL) DETECTION ====================
        
        # ---------------------- ISL GESTURE 1: YES ----------------------
        # ISL YES = Closed fist (all fingers folded)
        if (not fingers['index'] and not fingers['middle'] and 
            not fingers['ring'] and not fingers['pinky'] and not fingers['thumb']):
            return "YES"
        
        # ---------------------- ISL GESTURE 2: NO ----------------------
        # ISL NO = Pinched fingers (index and thumb touching, others closed)
        thumb_index_dist = self.calculate_distance(thumb_tip, index_tip)
        if thumb_index_dist < 0.05:  # Index and thumb touching
            if (not fingers['middle'] and not fingers['ring'] and not fingers['pinky']):
                return "NO"
        
        # ---------------------- ISL GESTURE 3: GOOD ----------------------
        # GOOD = Thumbs up (thumb extended upward, others closed)
        if (fingers['thumb'] and not fingers['index'] and 
            not fingers['middle'] and not fingers['ring'] and not fingers['pinky']):
            if thumb_tip.y < landmarks[3].y:  # Thumb tip above thumb PIP (pointing up)
                return "GOOD"
        
        # ---------------------- ISL GESTURE 4: BAD ----------------------
        # BAD = Thumbs down (thumb extended downward, others closed)
        if (fingers['thumb'] and not fingers['index'] and 
            not fingers['middle'] and not fingers['ring'] and not fingers['pinky']):
            if thumb_tip.y > landmarks[3].y:  # Thumb tip below thumb PIP (pointing down)
                return "BAD"
        
        # ---------------------- ISL GESTURE 5: OK ----------------------
        # OK = Index and thumb forming circle with other fingers open/extended
        if thumb_index_dist < 0.05:  # Index and thumb touching forming circle
            if (fingers['middle'] and fingers['ring'] and fingers['pinky']):
                return "OK"
        
        # ---------------------- ISL GESTURE 6: HELLO ----------------------
        # HELLO = Open palm raised (all fingers fully extended, palm facing forward)
        if (fingers['index'] and fingers['middle'] and 
            fingers['ring'] and fingers['pinky'] and fingers['thumb']):
            # Check if palm is relatively horizontal (fingers facing up)
            if index_tip.y < wrist.y and middle_tip.y < wrist.y:
                return "HELLO"
        
        # ---------------------- ISL GESTURE 7: STOP ----------------------
        # STOP = One vertical hand blocking horizontal hand (palm facing forward, fingers up)
        # Detected as: Open hand with specific orientation (all fingers extended)
        # Note: Ideally requires 2-hand detection, here we detect hand orientation
        if (fingers['index'] and fingers['middle'] and 
            fingers['ring'] and fingers['pinky'] and fingers['thumb']):
            # Check if fingers are pointing upward (vertical stop hand)
            avg_finger_y = (index_tip.y + middle_tip.y + ring_tip.y + pinky_tip.y) / 4
            if avg_finger_y < wrist.y and wrist.y > landmarks[0].y:
                return "STOP"
        
        # ---------------------- ISL GESTURE 8: HELP ----------------------
        # HELP = Thumbs up hand resting on open palm (requires both hands)
        # Detected as: Thumbs up gesture
        if (fingers['thumb'] and not fingers['index'] and 
            not fingers['middle'] and not fingers['ring'] and not fingers['pinky']):
            if thumb_tip.y < landmarks[3].y:
                # This is similar to GOOD, but HELP is when thumb is on another palm
                # For single hand detection, we identify it as thumb-up orientation
                return "HELP"
        
        # ---------------------- ISL GESTURE 9: THANK YOU ----------------------
        # THANK YOU = Flat hand moved from chin area downward
        # Detected as: Flat open hand with palm facing to the side
        if (fingers['index'] and fingers['middle'] and 
            fingers['ring'] and fingers['pinky'] and fingers['thumb']):
            # Check if hand is near face/chin level (upper half of image)
            if wrist.y < 0.5:  # Upper portion of image (near head)
                return "THANK YOU"
        
        # ---------------------- ISL GESTURE 10: PLEASE ----------------------
        # PLEASE = Flat hand on chest (palm placed on chest)
        # Detected as: Flat open hand in middle-lower area of image
        if (fingers['index'] and fingers['middle'] and 
            fingers['ring'] and fingers['pinky'] and fingers['thumb']):
            # Check if hand is in chest area (middle of body)
            if 0.3 < wrist.y < 0.7:  # Middle portion of image (chest area)
                return "PLEASE"
        
        # If no gesture matched, return None
        return None
    
    # ======================== PROCESS FRAME =============================
    
    def process_frame(self, frame):
        """
        Main function to process a video frame and detect gestures.
        
        STEPS:
        1. Convert frame from BGR (OpenCV) to RGB (MediaPipe)
        2. Run MediaPipe hand detection
        3. For each detected hand, get landmarks
        4. Detect gesture from landmarks
        5. Return gesture and landmarks for drawing
        
        PARAMETER: frame - Video frame from webcam (numpy array)
        RETURNS: Dictionary with gestures and landmarks for drawing
        """
        
        # Convert BGR (OpenCV format) to RGB (MediaPipe format)
        # WHY? MediaPipe was trained on RGB images
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Run MediaPipe hand detection
        # This returns a list of detected hands and their landmarks
        results = self.hands.process(rgb_frame)
        
        detected_gestures = []
        landmarks_list = []
        
        # Process each detected hand
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Extract landmarks (21 points on hand)
                landmarks = hand_landmarks.landmark
                
                # Detect gesture from these landmarks
                gesture = self.detect_gesture(landmarks)
                
                if gesture:
                    detected_gestures.append(gesture)
                
                # Store landmarks for drawing skeleton
                landmarks_list.append(hand_landmarks)
        
        return {
            'gestures': detected_gestures,
            'hand_landmarks': landmarks_list,
            'raw_results': results
        }
    
    # ======================== CLEANUP =============================
    
    def close(self):
        """Close the hand detector and release resources"""
        self.hands.close()
