# ============================================================================
# PROJECT: Sign Language to Text Converter (Web-based)
# MODULE: Database Management
# PURPOSE: Handle all database operations using SQLite
# EXPLANATION: This module manages storing and retrieving gesture predictions
#              from the SQLite database. We use SQLite because:
#              1. No server needed (built into Python)
#              2. Perfect for college projects
#              3. Easy to backup (single file)
#              4. Lightweight and fast
# ============================================================================

import sqlite3
from datetime import datetime
from config import DATABASE_PATH

# ======================== DATABASE INITIALIZATION =============================

def initialize_database():
    """
    Create database and tables if they don't exist.
    This function runs once when the app starts.
    """
    try:
        # Connect to SQLite database (creates it if not exists)
        connection = sqlite3.connect(DATABASE_PATH)
        cursor = connection.cursor()
        
        # Create 'predictions' table to store gesture data
        # TABLE STRUCTURE:
        # - id: Unique identifier for each record (auto-increments)
        # - gesture: The recognized gesture/sign
        # - timestamp: When the gesture was detected
        # - confidence: How confident the model was (0-1)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gesture TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                confidence REAL
            )
        ''')
        
        connection.commit()
        connection.close()
        print("[DATABASE] Database initialized successfully!")
        
    except sqlite3.Error as e:
        print(f"[DATABASE ERROR] Failed to initialize database: {e}")


# ======================== INSERT OPERATIONS =============================

def save_prediction(gesture, confidence=None):
    """
    Save a detected gesture to the database.
    
    PARAMETERS:
    - gesture (str): The name of the detected gesture
    - confidence (float): How confident the model was (optional)
    
    RETURNS: True if saved successfully, False otherwise
    """
    try:
        connection = sqlite3.connect(DATABASE_PATH)
        cursor = connection.cursor()
        
        # Insert new record into predictions table
        cursor.execute('''
            INSERT INTO predictions (gesture, confidence)
            VALUES (?, ?)
        ''', (gesture, confidence))
        
        connection.commit()
        connection.close()
        
        print(f"[DATABASE] Saved gesture: {gesture}")
        return True
        
    except sqlite3.Error as e:
        print(f"[DATABASE ERROR] Failed to save prediction: {e}")
        return False


# ======================== RETRIEVE OPERATIONS =============================

def get_all_predictions():
    """
    Retrieve all saved predictions from the database.
    
    RETURNS: List of dictionaries containing prediction data
    """
    try:
        connection = sqlite3.connect(DATABASE_PATH)
        connection.row_factory = sqlite3.Row  # Return results as dictionaries
        cursor = connection.cursor()
        
        # Select all predictions ordered by newest first
        cursor.execute('''
            SELECT id, gesture, timestamp, confidence
            FROM predictions
            ORDER BY timestamp DESC
        ''')
        
        predictions = [dict(row) for row in cursor.fetchall()]
        connection.close()
        
        return predictions
        
    except sqlite3.Error as e:
        print(f"[DATABASE ERROR] Failed to retrieve predictions: {e}")
        return []


def get_recent_predictions(limit=10):
    """
    Retrieve recent predictions (last N records).
    
    PARAMETERS:
    - limit (int): How many recent records to retrieve
    
    RETURNS: List of recent predictions
    """
    try:
        connection = sqlite3.connect(DATABASE_PATH)
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        
        cursor.execute('''
            SELECT id, gesture, timestamp, confidence
            FROM predictions
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        predictions = [dict(row) for row in cursor.fetchall()]
        connection.close()
        
        return predictions
        
    except sqlite3.Error as e:
        print(f"[DATABASE ERROR] Failed to retrieve recent predictions: {e}")
        return []


def get_prediction_statistics():
    """
    Get statistics about the predictions (total count, unique gestures, etc.)
    
    RETURNS: Dictionary with statistics
    """
    try:
        connection = sqlite3.connect(DATABASE_PATH)
        cursor = connection.cursor()
        
        # Count total predictions
        cursor.execute('SELECT COUNT(*) FROM predictions')
        total = cursor.fetchone()[0]
        
        # Count unique gestures
        cursor.execute('SELECT COUNT(DISTINCT gesture) FROM predictions')
        unique_gestures = cursor.fetchone()[0]
        
        # Get most detected gesture
        cursor.execute('''
            SELECT gesture, COUNT(*) as count
            FROM predictions
            GROUP BY gesture
            ORDER BY count DESC
            LIMIT 1
        ''')
        result = cursor.fetchone()
        most_detected = result[0] if result else None
        
        connection.close()
        
        return {
            'total_predictions': total,
            'unique_gestures': unique_gestures,
            'most_detected': most_detected
        }
        
    except sqlite3.Error as e:
        print(f"[DATABASE ERROR] Failed to get statistics: {e}")
        return {}


# ======================== DELETE OPERATIONS =============================

def clear_all_predictions():
    """
    Delete all predictions from the database (for testing/reset).
    """
    try:
        connection = sqlite3.connect(DATABASE_PATH)
        cursor = connection.cursor()
        
        # Delete all records
        cursor.execute('DELETE FROM predictions')
        rows_deleted = cursor.rowcount
        connection.commit()
        connection.close()
        
        print(f"[DATABASE] All predictions cleared! ({rows_deleted} rows deleted)")
        return True
        
    except sqlite3.Error as e:
        print(f"[DATABASE ERROR] Failed to clear predictions: {e}")
        return False
    except Exception as e:
        print(f"[DATABASE ERROR] Unexpected error clearing predictions: {e}")
        return False
