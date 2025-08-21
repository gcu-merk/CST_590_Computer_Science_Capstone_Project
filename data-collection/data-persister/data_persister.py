#!/usr/bin/env python3
"""
Data Persister Service
Handles persistent storage of traffic monitoring data to database
"""

import time
import logging
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database connections and operations"""
    
    def __init__(self, db_path="traffic_data.db"):
        self.db_path = db_path
        self.connection = None
        self._create_tables()
    
    def _create_tables(self):
        """Create database tables if they don't exist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Vehicle detections table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS vehicle_detections (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        detection_id TEXT UNIQUE,
                        timestamp REAL,
                        bbox_x INTEGER,
                        bbox_y INTEGER,
                        bbox_width INTEGER,
                        bbox_height INTEGER,
                        confidence REAL,
                        vehicle_type TEXT,
                        frame_id INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Speed measurements table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS speed_measurements (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        detection_id TEXT UNIQUE,
                        start_time REAL,
                        end_time REAL,
                        avg_speed_mps REAL,
                        max_speed_mps REAL,
                        direction TEXT,
                        confidence REAL,
                        peak_magnitude INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Vehicle tracks table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS vehicle_tracks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        track_id TEXT UNIQUE,
                        start_time REAL,
                        last_update REAL,
                        vehicle_type TEXT,
                        current_speed REAL,
                        confidence REAL,
                        is_active BOOLEAN,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # System metrics table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS system_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp REAL,
                        cpu_percent REAL,
                        memory_percent REAL,
                        disk_percent REAL,
                        temperature REAL,
                        gpu_temp REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.commit()
                logger.info("Database tables created successfully")
                
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")

class DataPersister:
    """
    Main data persistence service
    Stores traffic monitoring data to database
    """
    
    def __init__(self, db_path="traffic_data.db"):
        self.db_manager = DatabaseManager(db_path)
        self.is_running = False
        
    def persist_vehicle_detection(self, detection_data):
        """Persist vehicle detection data"""
        try:
            with sqlite3.connect(self.db_manager.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO vehicle_detections 
                    (detection_id, timestamp, bbox_x, bbox_y, bbox_width, bbox_height,
                     confidence, vehicle_type, frame_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    detection_data.get('detection_id'),
                    detection_data.get('timestamp'),
                    detection_data.get('bbox', [0, 0, 0, 0])[0],
                    detection_data.get('bbox', [0, 0, 0, 0])[1],
                    detection_data.get('bbox', [0, 0, 0, 0])[2],
                    detection_data.get('bbox', [0, 0, 0, 0])[3],
                    detection_data.get('confidence'),
                    detection_data.get('vehicle_type'),
                    detection_data.get('frame_id')
                ))
                conn.commit()
                logger.debug(f"Persisted vehicle detection: {detection_data.get('detection_id')}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to persist vehicle detection: {e}")
            return False
    
    def persist_speed_measurement(self, speed_data):
        """Persist speed measurement data"""
        try:
            with sqlite3.connect(self.db_manager.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO speed_measurements 
                    (detection_id, start_time, end_time, avg_speed_mps, max_speed_mps,
                     direction, confidence, peak_magnitude)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    speed_data.get('detection_id'),
                    speed_data.get('start_time'),
                    speed_data.get('end_time'),
                    speed_data.get('avg_speed_mps'),
                    speed_data.get('max_speed_mps'),
                    speed_data.get('direction'),
                    speed_data.get('confidence'),
                    speed_data.get('peak_magnitude')
                ))
                conn.commit()
                logger.debug(f"Persisted speed measurement: {speed_data.get('detection_id')}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to persist speed measurement: {e}")
            return False
    
    def persist_vehicle_track(self, track_data):
        """Persist vehicle track data"""
        try:
            with sqlite3.connect(self.db_manager.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO vehicle_tracks 
                    (track_id, start_time, last_update, vehicle_type, current_speed,
                     confidence, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    track_data.get('track_id'),
                    track_data.get('start_time'),
                    track_data.get('last_update'),
                    track_data.get('vehicle_type'),
                    track_data.get('current_speed'),
                    track_data.get('confidence'),
                    track_data.get('is_active', True)
                ))
                conn.commit()
                logger.debug(f"Persisted vehicle track: {track_data.get('track_id')}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to persist vehicle track: {e}")
            return False
    
    def persist_system_metrics(self, metrics_data):
        """Persist system metrics data"""
        try:
            with sqlite3.connect(self.db_manager.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO system_metrics 
                    (timestamp, cpu_percent, memory_percent, disk_percent, temperature, gpu_temp)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    metrics_data.get('timestamp'),
                    metrics_data.get('cpu_percent'),
                    metrics_data.get('memory_percent'),
                    metrics_data.get('disk_percent'),
                    metrics_data.get('temperature'),
                    metrics_data.get('gpu_temp')
                ))
                conn.commit()
                logger.debug("Persisted system metrics")
                return True
                
        except Exception as e:
            logger.error(f"Failed to persist system metrics: {e}")
            return False
    
    def get_recent_detections(self, minutes=60):
        """Get vehicle detections from the last N minutes"""
        try:
            cutoff_time = time.time() - (minutes * 60)
            with sqlite3.connect(self.db_manager.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM vehicle_detections 
                    WHERE timestamp > ? 
                    ORDER BY timestamp DESC
                """, (cutoff_time,))
                
                rows = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                
                return [dict(zip(columns, row)) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get recent detections: {e}")
            return []
    
    def get_recent_speeds(self, minutes=60):
        """Get speed measurements from the last N minutes"""
        try:
            cutoff_time = time.time() - (minutes * 60)
            with sqlite3.connect(self.db_manager.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM speed_measurements 
                    WHERE start_time > ? 
                    ORDER BY start_time DESC
                """, (cutoff_time,))
                
                rows = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                
                return [dict(zip(columns, row)) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get recent speeds: {e}")
            return []
    
    def get_database_stats(self):
        """Get database statistics"""
        try:
            with sqlite3.connect(self.db_manager.db_path) as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # Count records in each table
                tables = ['vehicle_detections', 'speed_measurements', 'vehicle_tracks', 'system_metrics']
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    stats[f"{table}_count"] = cursor.fetchone()[0]
                
                # Get date range
                cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM vehicle_detections")
                result = cursor.fetchone()
                if result and result[0]:
                    stats['data_start'] = datetime.fromtimestamp(result[0]).isoformat()
                    stats['data_end'] = datetime.fromtimestamp(result[1]).isoformat()
                
                return stats
                
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}

if __name__ == "__main__":
    # Test the data persister
    persister = DataPersister("test_traffic_data.db")
    
    # Test data
    test_detection = {
        'detection_id': 'test_det_1',
        'timestamp': time.time(),
        'bbox': [100, 100, 200, 150],
        'confidence': 0.85,
        'vehicle_type': 'car',
        'frame_id': 1
    }
    
    test_speed = {
        'detection_id': 'test_speed_1',
        'start_time': time.time() - 5,
        'end_time': time.time(),
        'avg_speed_mps': 15.5,
        'max_speed_mps': 18.2,
        'direction': 'approaching',
        'confidence': 0.9,
        'peak_magnitude': 150
    }
    
    test_metrics = {
        'timestamp': time.time(),
        'cpu_percent': 25.5,
        'memory_percent': 45.2,
        'disk_percent': 60.1,
        'temperature': 55.8,
        'gpu_temp': 52.3
    }
    
    # Persist test data
    persister.persist_vehicle_detection(test_detection)
    persister.persist_speed_measurement(test_speed)
    persister.persist_system_metrics(test_metrics)
    
    # Get stats
    stats = persister.get_database_stats()
    print(f"Database stats: {stats}")
    
    print("Data persister test completed")