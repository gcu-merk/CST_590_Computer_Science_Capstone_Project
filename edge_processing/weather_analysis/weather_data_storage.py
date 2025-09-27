#!/usr/bin/env python3
"""
Weather Data Storage and Correlation Module
Stores weather analysis data and correlates it with traffic events
"""

import json
import sqlite3
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class WeatherDataStorage:
    """Handles storage and retrieval of weather analysis data"""
    
    def __init__(self, db_path: str = None, max_records: int = 10000):
        """
        Initialize weather data storage - now using consolidated main traffic database
        
        Args:
            db_path: Path to SQLite database file (defaults to main traffic database)
            max_records: Maximum number of records to keep (for cleanup)
        """
        if db_path is None:
            # Use main traffic database path instead of separate weather database
            db_path = os.environ.get('DATABASE_PATH', '/app/data/traffic_data.db')
        
        self.db_path = db_path
        self.max_records = max_records
        self._init_database()
    
    def _init_database(self):
        """Initialize the SQLite database with required tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Note: Weather analysis tables are now created by the main database persistence service
                # This method now ensures the tables exist but doesn't recreate them
                
                # Verify weather analysis tables exist (they should be created by main persistence service)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS weather_analysis (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        condition TEXT NOT NULL,
                        confidence REAL NOT NULL,
                        visibility_estimate TEXT,
                        analysis_methods TEXT,
                        system_temperature REAL,
                        frame_info TEXT,
                        created_at REAL NOT NULL
                    )
                ''')
                
                # Weather traffic events table (renamed to avoid conflict with main traffic_records)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS weather_traffic_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        event_data TEXT,
                        weather_id INTEGER,
                        created_at REAL NOT NULL,
                        FOREIGN KEY (weather_id) REFERENCES weather_analysis (id)
                    )
                ''')
                
                # Weather summaries table (hourly/daily aggregates)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS weather_summaries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        period_start TEXT NOT NULL,
                        period_end TEXT NOT NULL,
                        period_type TEXT NOT NULL,
                        clear_count INTEGER DEFAULT 0,
                        partly_cloudy_count INTEGER DEFAULT 0,
                        cloudy_count INTEGER DEFAULT 0,
                        unknown_count INTEGER DEFAULT 0,
                        avg_confidence REAL,
                        total_analyses INTEGER DEFAULT 0,
                        created_at REAL NOT NULL
                    )
                ''')
                
                # Create indexes for performance (matching main database schema)
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_weather_analysis_timestamp ON weather_analysis(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_weather_traffic_events_timestamp ON weather_traffic_events(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_weather_traffic_events_weather_id ON weather_traffic_events(weather_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_weather_summaries_period ON weather_summaries(period_start, period_type)')
                
                conn.commit()
                logger.info(f"Weather database initialized: {self.db_path}")
                
        except Exception as e:
            logger.error(f"Error initializing weather database: {e}")
            raise
    
    def store_weather_analysis(self, weather_data: Dict) -> int:
        """
        Store weather analysis result
        
        Args:
            weather_data: Weather analysis result from SkyAnalyzer
            
        Returns:
            ID of stored record
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                sky_condition = weather_data.get('sky_condition', {})
                weather_metrics = weather_data.get('weather_metrics', {})
                
                cursor.execute('''
                    INSERT INTO weather_analysis (
                        timestamp, condition, confidence, visibility_estimate,
                        analysis_methods, system_temperature, frame_info, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    weather_data.get('timestamp', datetime.now().isoformat()),
                    sky_condition.get('condition', 'unknown'),
                    sky_condition.get('confidence', 0.0),
                    weather_data.get('visibility_estimate', 'unknown'),
                    json.dumps(sky_condition.get('analysis_methods', {})),
                    weather_metrics.get('system_temperature_c'),
                    json.dumps(weather_data.get('frame_info', {})),
                    time.time()
                ))
                
                weather_id = cursor.lastrowid
                conn.commit()
                
                # Cleanup old records if needed
                self._cleanup_old_records(cursor)
                
                return weather_id
                
        except Exception as e:
            logger.error(f"Error storing weather analysis: {e}")
            return -1
    
    def store_traffic_event(self, event_data: Dict, weather_id: int = None) -> int:
        """
        Store traffic event with weather correlation
        
        Args:
            event_data: Traffic event data (detection, speed, track)
            weather_id: ID of correlated weather record
            
        Returns:
            ID of stored record
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # If no weather_id provided, try to find the most recent one
                if weather_id is None:
                    cursor.execute('''
                        SELECT id FROM weather_analysis 
                        ORDER BY created_at DESC LIMIT 1
                    ''')
                    result = cursor.fetchone()
                    weather_id = result[0] if result else None
                
                cursor.execute('''
                    INSERT INTO weather_traffic_events (
                        timestamp, event_type, event_data, weather_id, created_at
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (
                    event_data.get('timestamp', datetime.now().isoformat()),
                    event_data.get('type', 'unknown'),
                    json.dumps(event_data),
                    weather_id,
                    time.time()
                ))
                
                event_id = cursor.lastrowid
                conn.commit()
                return event_id
                
        except Exception as e:
            logger.error(f"Error storing traffic event: {e}")
            return -1
    
    def get_weather_history(self, hours: int = 24, limit: int = 100) -> List[Dict]:
        """
        Get weather analysis history
        
        Args:
            hours: Number of hours to look back
            limit: Maximum number of records to return
            
        Returns:
            List of weather analysis records
        """
        try:
            cutoff_time = time.time() - (hours * 3600)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT timestamp, condition, confidence, visibility_estimate,
                           analysis_methods, system_temperature, frame_info, created_at
                    FROM weather_analysis 
                    WHERE created_at > ? 
                    ORDER BY created_at DESC 
                    LIMIT ?
                ''', (cutoff_time, limit))
                
                results = []
                for row in cursor.fetchall():
                    try:
                        analysis_methods = json.loads(row[4]) if row[4] else {}
                        frame_info = json.loads(row[6]) if row[6] else {}
                    except json.JSONDecodeError:
                        analysis_methods = {}
                        frame_info = {}
                    
                    results.append({
                        'timestamp': row[0],
                        'condition': row[1],
                        'confidence': row[2],
                        'visibility_estimate': row[3],
                        'analysis_methods': analysis_methods,
                        'system_temperature_c': row[5],
                        'frame_info': frame_info,
                        'created_at': row[7]
                    })
                
                return results
                
        except Exception as e:
            logger.error(f"Error getting weather history: {e}")
            return []
    
    def get_weather_traffic_correlation(self, hours: int = 24) -> Dict:
        """
        Get correlation between weather conditions and traffic events
        
        Args:
            hours: Number of hours to analyze
            
        Returns:
            Dictionary with correlation data
        """
        try:
            cutoff_time = time.time() - (hours * 3600)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get weather condition counts
                cursor.execute('''
                    SELECT condition, COUNT(*) as count
                    FROM weather_analysis 
                    WHERE created_at > ?
                    GROUP BY condition
                ''', (cutoff_time,))
                
                weather_counts = dict(cursor.fetchall())
                
                # Get traffic events by weather condition
                cursor.execute('''
                    SELECT w.condition, t.event_type, COUNT(*) as count
                    FROM weather_traffic_events t
                    JOIN weather_analysis w ON t.weather_id = w.id
                    WHERE t.created_at > ?
                    GROUP BY w.condition, t.event_type
                ''', (cutoff_time,))
                
                traffic_by_weather = {}
                for condition, event_type, count in cursor.fetchall():
                    if condition not in traffic_by_weather:
                        traffic_by_weather[condition] = {}
                    traffic_by_weather[condition][event_type] = count
                
                return {
                    'period_hours': hours,
                    'weather_conditions': weather_counts,
                    'traffic_by_weather': traffic_by_weather,
                    'total_weather_records': sum(weather_counts.values()),
                    'analysis_timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error getting weather-traffic correlation: {e}")
            return {}
    
    def create_hourly_summary(self, target_hour: datetime = None) -> bool:
        """
        Create hourly weather summary
        
        Args:
            target_hour: Hour to summarize (defaults to previous hour)
            
        Returns:
            True if successful
        """
        try:
            if target_hour is None:
                target_hour = datetime.now().replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)
            
            period_start = target_hour
            period_end = period_start + timedelta(hours=1)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if summary already exists
                cursor.execute('''
                    SELECT id FROM weather_summaries 
                    WHERE period_start = ? AND period_type = 'hourly'
                ''', (period_start.isoformat(),))
                
                if cursor.fetchone():
                    return True  # Already exists
                
                # Analyze weather data for the hour
                cursor.execute('''
                    SELECT condition, confidence FROM weather_analysis 
                    WHERE timestamp BETWEEN ? AND ?
                ''', (period_start.isoformat(), period_end.isoformat()))
                
                conditions = {'clear': 0, 'partly_cloudy': 0, 'cloudy': 0, 'unknown': 0}
                confidences = []
                
                for condition, confidence in cursor.fetchall():
                    if condition in conditions:
                        conditions[condition] += 1
                    else:
                        conditions['unknown'] += 1
                    confidences.append(confidence)
                
                total_analyses = sum(conditions.values())
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                
                # Store summary
                cursor.execute('''
                    INSERT INTO weather_summaries (
                        period_start, period_end, period_type,
                        clear_count, partly_cloudy_count, cloudy_count, unknown_count,
                        avg_confidence, total_analyses, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    period_start.isoformat(), period_end.isoformat(), 'hourly',
                    conditions['clear'], conditions['partly_cloudy'], 
                    conditions['cloudy'], conditions['unknown'],
                    avg_confidence, total_analyses, time.time()
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error creating hourly summary: {e}")
            return False
    
    def _cleanup_old_records(self, cursor):
        """Clean up old records to maintain database size"""
        try:
            # Count current records
            cursor.execute('SELECT COUNT(*) FROM weather_analysis')
            count = cursor.fetchone()[0]
            
            if count > self.max_records:
                # Delete oldest records
                records_to_delete = count - self.max_records
                cursor.execute('''
                    DELETE FROM weather_analysis 
                    WHERE id IN (
                        SELECT id FROM weather_analysis 
                        ORDER BY created_at ASC 
                        LIMIT ?
                    )
                ''', (records_to_delete,))
                
                logger.info(f"Cleaned up {records_to_delete} old weather records")
                
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")
    
    def get_database_stats(self) -> Dict:
        """Get database statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Count records in each table
                cursor.execute('SELECT COUNT(*) FROM weather_analysis')
                weather_count = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM weather_traffic_events')
                traffic_count = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM weather_summaries')
                summary_count = cursor.fetchone()[0]
                
                # Get date range
                cursor.execute('SELECT MIN(created_at), MAX(created_at) FROM weather_analysis')
                date_range = cursor.fetchone()
                
                return {
                    'database_path': self.db_path,
                    'weather_records': weather_count,
                    'weather_traffic_events': traffic_count,
                    'summaries': summary_count,
                    'date_range': {
                        'earliest': datetime.fromtimestamp(date_range[0]).isoformat() if date_range[0] else None,
                        'latest': datetime.fromtimestamp(date_range[1]).isoformat() if date_range[1] else None
                    },
                    'max_records': self.max_records
                }
                
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {'error': str(e)}