/* ========================================================================
   Sign Language to Text Converter - JavaScript Logic
   ========================================================================
   WHY JAVASCRIPT?
   - Makes webpage interactive and responsive
   - Communicates with Flask backend via API calls
   - Updates HTML dynamically without refreshing page
   - Handles button clicks, form submissions, etc.
   
   KEY CONCEPTS:
   - fetch(): Send requests to Flask backend
   - async/await: Wait for responses without freezing UI
   - DOM manipulation: Change HTML content dynamically
   ======================================================================== */

/* ========================================================================
   1. GLOBAL VARIABLES
   ======================================================================== */

// Track camera state
let cameraRunning = false;

// Track gesture detection
let lastDetectedGesture = null;
let detectionUpdateInterval = null;

// Video stream update interval
let videoStreamInterval = null;

/* ========================================================================
   2. CAMERA CONTROL FUNCTIONS
   ======================================================================== */

/**
 * START VIDEO STREAM - Continuously update video display
 */
function startVideoStream() {
    console.log("[VIDEO] Starting video stream updates...");

    const videoFeed = document.getElementById('videoFeed');
    const videoStatus = document.getElementById('videoStatus');
    
    // Stop any existing stream
    if (videoStreamInterval) {
        clearInterval(videoStreamInterval);
    }
    
    // Update video frame every 150ms (~7 FPS) - smooth but not overloading
    videoStreamInterval = setInterval(async () => {
        try {
            const response = await fetch('/api/frame');
            if (!response.ok) return;
            
            const data = await response.json();

            if (data && data.frame) {
                // We have a valid frame → show it
                videoFeed.src = 'data:image/jpeg;base64,' + data.frame;
                if (!cameraRunning) {
                    cameraRunning = true;
                    videoStatus.textContent = '🟢 Camera is running...';
                }
            } else {
                // No frame – inspect backend status
                if (data && data.status === 'no_camera') {
                    console.log("[VIDEO] Backend reports no camera available");
                    cameraRunning = false;

                    // Stop polling for frames
                    stopVideoStream();

                    // Reset UI to stopped state
                    videoFeed.src = '/static/placeholder.svg';
                    videoStatus.textContent = '🔴 Camera not available or stopped';

                    document.getElementById('startBtn').disabled = false;
                    document.getElementById('stopBtn').disabled = true;
                } else if (data && data.status === 'no_frame') {
                    // Camera is “on” but not giving frames – show a warning
                    videoStatus.textContent = '⚠️ No frame from camera (check permissions or other apps using camera)';
                }
            }
        } catch (error) {
            console.error("[VIDEO] Error updating frame:", error.message);
        }
    }, 150);
}

/**
 * STOP VIDEO STREAM
 */
function stopVideoStream() {
    console.log("[VIDEO] Stopping video stream updates...");
    if (videoStreamInterval) {
        clearInterval(videoStreamInterval);
        videoStreamInterval = null;
    }
}

/**
 * START CAMERA - Called when user clicks "Start Camera" button
 * 
 * PROCESS:
 * 1. Send POST request to Flask /start_camera endpoint
 * 2. If successful, update UI (buttons, status)
 * 3. Start the video stream
 * 4. Begin gesture detection loop
 * 5. Show error message if failed
 */
async function startCamera() {
    try {
        console.log("Starting camera...");
        
        // Show loading state
        const startBtn = document.getElementById('startBtn');
        startBtn.disabled = true;
        startBtn.textContent = '⏳ Stopping old session...';
        
        // FIRST: Force stop any previous camera session (check HTTP status)
        try {
            const stopResp = await fetch('/stop_camera', { method: 'POST' });
            if (stopResp.ok) {
                console.log("[DEBUG] Stopped previous camera session");
            } else {
                console.log("[DEBUG] stop_camera returned non-ok status:", stopResp.status);
            }
        } catch (e) {
            console.log("[DEBUG] Failed to call stop_camera:", e.message);
        }
        
        // Wait 1 second for cleanup
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // NOW: Start fresh camera
        startBtn.textContent = '⏳ Starting...';
        
        const response = await fetch('/start_camera', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        console.log("[DEBUG] Start camera response:", data);
        
        // Check if status indicates success
        if (data && data.status === 'success') {
            // Success! Update UI
            console.log("[SUCCESS] Camera started!", data.message);
            
            cameraRunning = true;
            
            // Update button states
            document.getElementById('startBtn').disabled = true;
            document.getElementById('stopBtn').disabled = false;
            
            // Update status message
            document.getElementById('videoStatus').textContent = '🟢 Camera is running...';
            
            // Start video stream updates (fetch frames every 150ms)
            startVideoStream();
            
            // Start detecting gestures periodically
            startGestureDetection();
            
            // Update predictions and statistics once on start
            updatePredictions();
            updateStatistics();
            
            // Refresh data every 3 seconds (less frequent to reduce load)
            setInterval(() => {
                updateStatistics();  // Just update stats, predictions update on gesture detection
            }, 3000);
            
        } else {
            // Error response from backend
            console.error("[ERROR] Camera start failed:", data);
            alert("Camera Error: " + data.message + (data.hint ? "\n\n" + data.hint : ""));
            startBtn.disabled = false;
            startBtn.textContent = '▶ Start Camera';
        }
        
    } catch (error) {
        console.error("[ERROR] Exception starting camera:", error);
        alert("Failed to start camera: " + error.message);
        
        // Reset button
        const startBtn = document.getElementById('startBtn');
        startBtn.disabled = false;
        startBtn.textContent = '▶ Start Camera';
    }
}

/**
 * STOP CAMERA - Called when user clicks "Stop Camera" button
 * 
 * PROCESS:
 * 1. Send POST request to Flask /stop_camera endpoint
 * 2. Stop video stream
 * 3. Update UI (buttons, status)
 * 4. Stop gesture detection loop
 */
async function stopCamera() {
    try {
        console.log("Stopping camera...");
        
        // Show loading state
        const stopBtn = document.getElementById('stopBtn');
        stopBtn.disabled = true;
        stopBtn.textContent = '⏳ Stopping...';
        
        // Send request to Flask backend to stop camera
        const response = await fetch('/stop_camera', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            console.log("[SUCCESS] Camera stopped!");
            
            cameraRunning = false;
            
            // Stop the video stream updates
            stopVideoStream();
            
            // Stop gesture detection
            if (detectionUpdateInterval) {
                clearInterval(detectionUpdateInterval);
            }
            
            // Reset video display to static placeholder
            const videoFeed = document.getElementById('videoFeed');
            videoFeed.src = '/static/placeholder.svg';
            
            // Update button states
            document.getElementById('startBtn').disabled = false;
            document.getElementById('stopBtn').disabled = true;
            
            // Update status message
            document.getElementById('videoStatus').textContent = '🔴 Camera stopped';
            
        } else {
            console.error("Error:", data.message);
            alert("Error: " + data.message);
        }
        
    } catch (error) {
        console.error("[ERROR] Error stopping camera:", error);
        alert("Failed to stop camera: " + error.message);
    }
}

/* ========================================================================
   3. GESTURE DETECTION FUNCTION
   ======================================================================== */

/**
 * START GESTURE DETECTION - Continuously detect gestures
 * 
 * PROCESS:
 * 1. Call /api/detect_gesture every 100ms
 * 2. Get current gesture from camera
 * 3. Update UI with detected gesture
 * 4. If gesture saved successfully, update predictions list
 */
function startGestureDetection() {
    console.log("Starting gesture detection...");
    
    // Call gesture detection every 200ms (~5 FPS) - good balance between responsiveness and performance
    detectionUpdateInterval = setInterval(async () => {
        try {
            // Send request to Flask backend (no body required when using server camera)
            const response = await fetch('/api/detect_gesture', {
                method: 'POST'
            });

            // Check if response is OK (200-299)
            if (!response.ok) {
                console.error(`[WARNING] Unexpected HTTP status: ${response.status}`);
                return; // Skip this frame
            }

            const data = await response.json();
            
            // Handle successful response (ALL responses from backend are now 200)
            if (data && data.status === 'success') {
                if (data.gesture) {
                    // Gesture detected
                    lastDetectedGesture = data.gesture;
                    document.getElementById('currentGesture').textContent = data.gesture;
                    document.getElementById('confidenceLevel').textContent = 'Confidence: 90%';
                    
                    // If gesture was saved, ONLY update predictions (not stats every time)
                    if (data.saved) {
                        console.log("[SAVED] Gesture saved:", data.gesture);
                        updatePredictions();
                        // Statistics will be updated every 3 seconds in main interval
                    }
                } else {
                    // No gesture in this frame (normal, no hand visible)
                    document.getElementById('currentGesture').textContent = 'No gesture detected';
                    document.getElementById('confidenceLevel').textContent = 'Confidence: 0%';
                }
            } else {
                // Unexpected response format
                console.warn("[WARNING] Unexpected response format:", data);
            }
            
        } catch (error) {
            // Network or parsing error (log once, don't spam)
            console.error("[ERROR] Exception in gesture detection:", error.message);
            // Don't update UI to prevent showing repeated errors
        }
    }, 200);  // Poll every 200ms
}

/* ========================================================================
   4. DATA UPDATE FUNCTIONS
   ======================================================================== */

/**
 * UPDATE PREDICTIONS - Fetch and display detected gestures
 * 
 * PROCESS:
 * 1. Call /api/predictions to get last 10 predictions
 * 2. Loop through predictions
 * 3. Create HTML for each prediction
 * 4. Display in predictions list
 */
async function updatePredictions() {
    try {
        // Fetch last 10 predictions from database
        const response = await fetch('/api/predictions?limit=10');
        const data = await response.json();
        
        if (response.ok) {
            const predictions = data.predictions;
            const predictionsList = document.getElementById('predictionsList');
            
            // Check if there are any predictions
            if (predictions.length === 0) {
                predictionsList.innerHTML = 
                    '<p class="empty-message">No predictions yet. Start camera to detect signs!</p>';
                return;
            }
            
            // Create HTML for each prediction
            let html = '';
            predictions.forEach((prediction, index) => {
                // Format timestamp to readable format
                const date = new Date(prediction.timestamp);
                const timeStr = date.toLocaleTimeString();
                const dateStr = date.toLocaleDateString();
                
                html += `
                    <div class="prediction-item">
                        <div>
                            <span class="prediction-gesture">${index + 1}. ${prediction.gesture}</span>
                        </div>
                        <span class="prediction-time">${timeStr}</span>
                    </div>
                `;
            });
            
            // Update the list
            predictionsList.innerHTML = html;
            
            // Auto-scroll to newest (bottom)
            predictionsList.scrollTop = predictionsList.scrollHeight;
            
        }
        
    } catch (error) {
        console.error("[ERROR] Error updating predictions:", error);
    }
}

/**
 * UPDATE STATISTICS - Fetch and display dashboard statistics
 * 
 * PROCESS:
 * 1. Call /api/statistics to get prediction stats
 * 2. Update the stat cards with new values
 * 3. Display total, unique gestures, most detected
 */
async function updateStatistics() {
    try {
        // Fetch statistics from backend
        const response = await fetch('/api/statistics');
        const data = await response.json();
        
        if (response.ok) {
            const stats = data.statistics;
            
            // Update stat cards
            document.getElementById('totalPredictions').textContent = stats.total_predictions || 0;
            document.getElementById('uniqueGestures').textContent = stats.unique_gestures || 0;
            document.getElementById('mostDetected').textContent = 
                stats.most_detected || '--';
        }
        
    } catch (error) {
        console.error("[ERROR] Error updating statistics:", error);
    }
}

/* ========================================================================
   5. CLEAR DATA FUNCTION
   ======================================================================== */

/**
 * CLEAR DATA - Delete all predictions from database
 * 
 * PROCESS:
 * 1. Ask user for confirmation
 * 2. Send POST request to /api/clear_data
 * 3. Clear predictions list
 * 4. Reset statistics
 */
async function clearData() {
    // Ask for user confirmation
    const confirmed = confirm(
        'Are you sure you want to delete all predictions? This cannot be undone!'
    );
    
    if (!confirmed) {
        return;  // User cancelled
    }
    
    try {
        console.log("Clearing all data...");
        
        // Send request to Flask backend
        const response = await fetch('/api/clear_data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            console.log("[SUCCESS] Data cleared!");
            
            // Update UI
            document.getElementById('predictionsList').innerHTML = 
                '<p class="empty-message">No predictions yet. Start camera to detect signs!</p>';
            document.getElementById('totalPredictions').textContent = '0';
            document.getElementById('uniqueGestures').textContent = '0';
            document.getElementById('mostDetected').textContent = '--';
            
            alert('All predictions cleared!');
            
        } else {
            console.error("Error:", data.message);
            alert("Error: " + data.message);
        }
        
    } catch (error) {
        console.error("[ERROR] Error clearing data:", error);
        alert("Failed to clear data: " + error.message);
    }
}

/* ========================================================================
   6. PAGE INITIALIZATION
   ======================================================================== */

/**
 * RUN ON PAGE LOAD
 * 
 * PROCESS:
 * 1. Wait for HTML to fully load
 * 2. Initialize UI (buttons, status)
 * 3. Load initial predictions and statistics
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log("[INIT] Page loaded, initializing...");
    
    // Initialize button states
    document.getElementById('startBtn').disabled = false;
    document.getElementById('stopBtn').disabled = true;
    
    // Load initial predictions
    updatePredictions();
    
    // Load initial statistics
    updateStatistics();
    
    console.log("[INIT] Initialization complete!");
});

/* ========================================================================
   7. HELPFUL COMMENTS FOR LEARNING
   ======================================================================== */

/*
   WHAT HAPPENS WHEN YOU CLICK "START CAMERA"?
   
   1. Browser calls startCamera() JavaScript function
   2. startCamera() sends POST request to Flask backend (/start_camera)
   3. Flask app.py receives request and calls camera_module.start_camera()
   4. camera_module opens webcam and starts capturing frames
   5. JavaScript updates UI: video shows /video_feed stream
   6. /video_feed endpoint continuously sends camera frames to browser
   7. Browser displays frames as video
   8. startGestureDetection() begins polling /api/detect_gesture
   9. Each poll:
      - camera_module gets frame
      - gesture_model detects gesture from frame
      - If gesture detected, database.py saves it to SQLite
      - JSON response sent back to JavaScript
      - JavaScript updates the detected gesture display
   10. updatePredictions() shows all saved gestures
   11. updateStatistics() shows summary statistics
   
   WHY THIS ARCHITECTURE?
   - Separation of concerns (each module has one job)
   - Frontend and backend are independent
   - Easy to test each component separately
   - Can easily add features or modify without breaking other parts
*/
