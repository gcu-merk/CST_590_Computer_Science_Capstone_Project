#!/usr/bin/env python3
"""
Database Persistence Service
Consumes consolidated traffic data from Redis and stores in permanent database

This service implements the final stage of the data pipeline:
Radar Motion -> Consolidator -> Redis -> Database Persistence -> Long-term Storage

Architecture:
- Listens for 'database_events' on Redis pub/sub
- Consumes consolidated traffic records from consolidator service  
- Stores structured data in PostgreSQL/SQLite database
- Implements proper data retention and cleanup policies
- Provides efficient querying for API layer consumption
"""

import time
import json
import logging
import sqlite3
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import os

# Redis for consuming consolidated data
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.error("Redis required for database persistence service")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class TrafficRecord:
    """Structured traffic record for database storage"""
    id: str
    timestamp: datetime
    trigger_source: str
    
    # Radar data
    radar_speed: Optional[float] = None
    radar_direction: Optional[str] = None
    radar_magnitude: Optional[float] = None
    
    # Weather data
    air_temperature: Optional[float] = None
    humidity: Optional[float] = None
    airport_weather: Optional[str] = None
    
    # Camera data
    vehicle_count: Optional[int] = None
    primary_vehicle_type: Optional[str] = None
    detection_confidence: Optional[float] = None
    
    # Metadata
    processing_notes: Optional[str] = None

class DatabasePersistenceService:
    """
    Database persistence service for consolidated traffic monitoring data
    Focuses on long-term storage optimization and efficient API serving
    """
    
    def __init__(self,
                 redis_host: str = "redis",
                 redis_port: int = 6379,
                 db_path: str = "/mnt/storage/traffic_monitoring.db",
                 retention_days: int = 90,
                 batch_size: int = 100):
        
        if not REDIS_AVAILABLE:
            raise RuntimeError("Redis required for database persistence service")
        
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.db_path = db_path
        self.retention_days = retention_days
        self.batch_size = batch_size
        
        # Service state
        self.running = False
        self.redis_client = None
        self.pubsub = None
        self.db_connection = None
        
        # Processing threads
        self.event_thread = None
        self.cleanup_thread = None
        
        # Statistics
        self.records_processed = 0
        self.startup_time = None
        
        logger.info("Database Persistence Service initialized")
        logger.info(f"Database: {db_path}")
        logger.info(f"Data retention: {retention_days} days")
    
    def connect_redis(self) -> bool:
        """Connect to Redis and setup pub/sub"""
        try:
            self.redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=10
            )
            
            # Test connection
            self.redis_client.ping()
            
            # Setup pub/sub for database events
            self.pubsub = self.redis_client.pubsub()
            self.pubsub.subscribe("database_events")
            
            logger.info(f"✅ Connected to Redis at {self.redis_host}:{self.redis_port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            return False
    
    def init_database(self) -> bool:
        """Initialize SQLite database with optimized schema"""
        try:
            # Ensure directory exists
            db_dir = Path(self.db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)
            
            self.db_connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                isolation_level=None  # Autocommit mode
            )
            
            # Enable WAL mode for better concurrent access
            self.db_connection.execute("PRAGMA journal_mode=WAL")
            self.db_connection.execute("PRAGMA synchronous=NORMAL")
            self.db_connection.execute("PRAGMA cache_size=10000")
            
            # Create optimized table schema
            self.db_connection.execute("""
                CREATE TABLE IF NOT EXISTS traffic_records (
                    id TEXT PRIMARY KEY,
                    timestamp DATETIME NOT NULL,
                    trigger_source TEXT NOT NULL,
                    
                    -- Radar measurements
                    radar_speed REAL,
                    radar_direction TEXT,
                    radar_magnitude REAL,
                    
                    -- Environmental conditions
                    air_temperature REAL,
                    humidity REAL,
                    airport_weather TEXT,
                    
                    -- Vehicle detection data
                    vehicle_count INTEGER,
                    primary_vehicle_type TEXT,
                    detection_confidence REAL,
                    
                    -- Processing metadata
                    processing_notes TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for efficient querying
            self.db_connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON traffic_records(timestamp)
            """)
            
            self.db_connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_trigger_source 
                ON traffic_records(trigger_source)
            """)
            
            self.db_connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_radar_speed 
                ON traffic_records(radar_speed) 
                WHERE radar_speed IS NOT NULL
            """)
            
            # Create summary tables for analytics
            self.db_connection.execute("""
                CREATE TABLE IF NOT EXISTS daily_summary (
                    date DATE PRIMARY KEY,
                    total_detections INTEGER DEFAULT 0,
                    avg_speed REAL,
                    max_speed REAL,
                    vehicle_types TEXT,  -- JSON array
                    weather_conditions TEXT,  -- JSON array
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            logger.info(f"✅ Database initialized: {self.db_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            return False
    
    def start(self) -> bool:
        """Start the persistence service"""
        if not self.connect_redis():
            logger.error("Cannot start without Redis connection")
            return False
        
        if not self.init_database():
            logger.error("Cannot start without database initialization")
            return False
        
        self.running = True
        self.startup_time = time.time()
        logger.info("🗄️ Starting Database Persistence Service")
        
        # Start background threads
        self.event_thread = threading.Thread(
            target=self._process_database_events,
            daemon=True
        )
        self.event_thread.start()
        
        self.cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            daemon=True
        )
        self.cleanup_thread.start()
        
        logger.info("✅ Database persistence service started")
        return True
    
    def _process_database_events(self):
        """Process database persistence events from Redis pub/sub"""
        logger.info("Processing database persistence events...")
        
        while self.running:
            try:
                # Listen for Redis pub/sub messages
                message = self.pubsub.get_message(timeout=1.0)
                
                if message and message['type'] == 'message':
                    try:
                        event_data = json.loads(message['data'])
                        
                        if event_data.get('event_type') == 'new_consolidated_data':
                            self._process_consolidated_record(event_data)
                            
                    except json.JSONDecodeError:
                        logger.warning("Invalid JSON in database event")
                    except Exception as e:
                        logger.error(f"Error processing database event: {e}")
                
                time.sleep(0.1)  # Small delay to prevent CPU spinning
                
            except Exception as e:
                logger.error(f"Database event processing error: {e}")
                time.sleep(1)
    
    def _process_consolidated_record(self, event_data: Dict[str, Any]):
        """Process and store consolidated traffic record"""
        try:
            consolidation_id = event_data.get('consolidation_id')
            if not consolidation_id:
                logger.warning("No consolidation_id in database event")
                return
            
            # Fetch consolidated data from Redis
            consolidated_data = self._fetch_consolidated_data(consolidation_id)
            if not consolidated_data:
                logger.warning(f"Could not fetch consolidated data: {consolidation_id}")
                return
            
            # Convert to structured traffic record
            traffic_record = self._parse_consolidated_data(consolidated_data)
            if not traffic_record:
                logger.warning(f"Could not parse consolidated data: {consolidation_id}")
                return
            
            # Store in database
            self._store_traffic_record(traffic_record)
            
            # Update daily summary
            self._update_daily_summary(traffic_record)
            
            self.records_processed += 1
            logger.info(f"✅ Stored traffic record: {traffic_record.id} (total: {self.records_processed})")
            
        except Exception as e:
            logger.error(f"Error processing consolidated record: {e}")
    
    def _fetch_consolidated_data(self, consolidation_id: str) -> Optional[Dict[str, Any]]:
        """Fetch consolidated data from Redis"""
        try:
            # Try time-series key first
            ts_key = f"consolidation:history:{consolidation_id}"
            data = self.redis_client.get(ts_key)
            
            if not data:
                # Fallback to latest key
                data = self.redis_client.get('consolidation:latest')
            
            if data:
                return json.loads(data)
            
        except Exception as e:
            logger.error(f"Error fetching consolidated data: {e}")
        
        return None
    
    def _parse_consolidated_data(self, data: Dict[str, Any]) -> Optional[TrafficRecord]:
        """Parse consolidated data into structured traffic record"""
        try:
            # Extract radar data
            radar_data = data.get('radar_data', {})
            radar_speed = radar_data.get('speed')
            radar_direction = radar_data.get('direction')
            radar_magnitude = radar_data.get('magnitude')
            
            # Extract weather data
            weather_data = data.get('weather_data', {})
            dht22_data = weather_data.get('dht22', {})
            airport_data = weather_data.get('airport', {})
            
            air_temperature = dht22_data.get('temperature_c')
            humidity = dht22_data.get('humidity')
            airport_weather = None
            if airport_data:
                airport_weather = json.dumps(airport_data)  # Store as JSON string
            
            # Extract camera data
            camera_data = data.get('camera_data', {})
            latest_detection = camera_data.get('latest_detection', {})
            
            vehicle_count = camera_data.get('recent_summary', {}).get('count', 0)
            primary_vehicle_type = None
            detection_confidence = None
            
            if latest_detection:
                primary_vehicle_type = latest_detection.get('vehicle_type')
                detection_confidence = latest_detection.get('confidence')
            
            # Create traffic record
            traffic_record = TrafficRecord(
                id=data.get('consolidation_id', ''),
                timestamp=datetime.fromtimestamp(data.get('timestamp', time.time())),
                trigger_source=data.get('trigger_source', 'unknown'),
                radar_speed=radar_speed,
                radar_direction=radar_direction,
                radar_magnitude=radar_magnitude,
                air_temperature=air_temperature,
                humidity=humidity,
                airport_weather=airport_weather,
                vehicle_count=vehicle_count,
                primary_vehicle_type=primary_vehicle_type,
                detection_confidence=detection_confidence,
                processing_notes=data.get('processing_notes')
            )
            
            return traffic_record
            
        except Exception as e:
            logger.error(f"Error parsing consolidated data: {e}")
            return None
    
    def _store_traffic_record(self, record: TrafficRecord):
        """Store traffic record in database"""
        try:
            self.db_connection.execute("""
                INSERT OR REPLACE INTO traffic_records (
                    id, timestamp, trigger_source,
                    radar_speed, radar_direction, radar_magnitude,
                    air_temperature, humidity, airport_weather,
                    vehicle_count, primary_vehicle_type, detection_confidence,
                    processing_notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.id,
                record.timestamp,
                record.trigger_source,
                record.radar_speed,
                record.radar_direction,
                record.radar_magnitude,
                record.air_temperature,
                record.humidity,
                record.airport_weather,
                record.vehicle_count,
                record.primary_vehicle_type,
                record.detection_confidence,
                record.processing_notes
            ))
            
        except Exception as e:
            logger.error(f"Error storing traffic record: {e}")
            raise
    
    def _update_daily_summary(self, record: TrafficRecord):
        """Update daily summary statistics"""
        try:
            date_str = record.timestamp.date()
            
            # Get existing summary or create new one
            existing = self.db_connection.execute("""
                SELECT total_detections, avg_speed, max_speed, vehicle_types, weather_conditions
                FROM daily_summary WHERE date = ?
            """, (date_str,)).fetchone()
            
            if existing:
                total_detections = existing[0] + 1
                # Update running average (simplified)
                if record.radar_speed and existing[1]:
                    avg_speed = (existing[1] * existing[0] + record.radar_speed) / total_detections
                else:
                    avg_speed = record.radar_speed or existing[1]
                
                max_speed = max(existing[2] or 0, record.radar_speed or 0)
            else:
                total_detections = 1
                avg_speed = record.radar_speed
                max_speed = record.radar_speed
            
            # Store updated summary
            self.db_connection.execute("""
                INSERT OR REPLACE INTO daily_summary (
                    date, total_detections, avg_speed, max_speed
                ) VALUES (?, ?, ?, ?)
            """, (date_str, total_detections, avg_speed, max_speed))
            
        except Exception as e:
            logger.error(f"Error updating daily summary: {e}")
    
    def _cleanup_loop(self):
        """Cleanup old data periodically"""
        while self.running:
            try:
                self._cleanup_old_data()
                time.sleep(3600)  # Cleanup every hour
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
                time.sleep(600)  # Retry in 10 minutes
    
    def _cleanup_old_data(self):
        """Remove old data beyond retention period"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            
            # Remove old traffic records
            result = self.db_connection.execute("""
                DELETE FROM traffic_records 
                WHERE timestamp < ?
            """, (cutoff_date,))
            
            if result.rowcount > 0:
                logger.info(f"🧹 Cleaned up {result.rowcount} old traffic records")
            
        except Exception as e:
            logger.error(f"Error during data cleanup: {e}")
    
    def get_recent_records(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent traffic records for API consumption"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            cursor = self.db_connection.execute("""
                SELECT * FROM traffic_records 
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
                LIMIT 1000
            """, (cutoff_time,))
            
            columns = [desc[0] for desc in cursor.description]
            records = []
            
            for row in cursor.fetchall():
                record = dict(zip(columns, row))
                # Convert timestamp to ISO format for JSON serialization
                if record['timestamp']:
                    record['timestamp'] = datetime.fromisoformat(record['timestamp']).isoformat()
                records.append(record)
            
            return records
            
        except Exception as e:
            logger.error(f"Error fetching recent records: {e}")
            return []
    
    def get_daily_summary(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get daily summary statistics"""
        try:
            cutoff_date = datetime.now().date() - timedelta(days=days)
            
            cursor = self.db_connection.execute("""
                SELECT * FROM daily_summary 
                WHERE date >= ?
                ORDER BY date DESC
            """, (cutoff_date,))
            
            columns = [desc[0] for desc in cursor.description]
            summaries = []
            
            for row in cursor.fetchall():
                summary = dict(zip(columns, row))
                summaries.append(summary)
            
            return summaries
            
        except Exception as e:
            logger.error(f"Error fetching daily summary: {e}")
            return []
    
    def stop(self):
        """Stop the persistence service"""
        self.running = False
        
        if self.pubsub:
            self.pubsub.close()
        
        if self.redis_client:
            self.redis_client.close()
        
        if self.db_connection:
            self.db_connection.close()
        
        logger.info("Database Persistence Service stopped")

def main():
    """Main entry point"""
    # Configuration
    config = {
        'redis_host': os.getenv('REDIS_HOST', 'localhost'),
        'redis_port': int(os.getenv('REDIS_PORT', '6379')),
        'db_path': os.getenv('DB_PATH', '/mnt/storage/traffic_monitoring.db'),
        'retention_days': int(os.getenv('RETENTION_DAYS', '90')),
        'batch_size': int(os.getenv('BATCH_SIZE', '100'))
    }
    
    logger.info("=== Database Persistence Service ===")
    logger.info("Long-term storage for consolidated traffic monitoring data")
    
    try:
        persistence_service = DatabasePersistenceService(**config)
        
        if persistence_service.start():
            logger.info("Service running. Press Ctrl+C to stop.")
            
            try:
                while persistence_service.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received")
            finally:
                persistence_service.stop()
                
            return 0
        else:
            logger.error("Failed to start persistence service")
            return 1
        
    except Exception as e:
        logger.error(f"Service failed: {e}")
        return 1

if __name__ == '__main__':
    import sys
    sys.exit(main())