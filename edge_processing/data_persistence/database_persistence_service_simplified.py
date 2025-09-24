#!/usr/bin/env python3
"""
Enhanced Database Persistence Service - SIMPLIFIED SQLITE-ONLY - WITH CENTRALIZED LOGGING
Enhanced version of database_persistence_service.py with centralized logging integration

This simplified enhanced service maintains the original SQLite-focused architecture:
- Single SQLite database for reliable local persistence (no failover complexity)
- Enhanced with ServiceLogger and CorrelationContext for observability
- Improved performance monitoring and business event tracking
- Maintains original simplicity while adding comprehensive logging

Enhanced Features:
- Centralized logging with ServiceLogger and CorrelationContext integration
- SQLite operation monitoring and performance tracking
- Business event logging for database operations and health monitoring
- Query performance optimization with detailed analytics
- Real-time database health and performance monitoring
- Correlation tracking across database operations

The goal is to enhance observability of the existing simple SQLite architecture
without adding architectural complexity or failover mechanisms.
"""

import time
import json
import sqlite3
import threading
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import os
import sys

# Add edge_processing to path for shared_logging
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))
from shared_logging import ServiceLogger, CorrelationContext

# Redis for consuming consolidated data with logging
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

# Initialize centralized logging
logger = ServiceLogger("database_persistence_service")

@dataclass
class TrafficRecord:
    """Structured traffic record for database storage"""
    id: str
    timestamp: datetime
    trigger_source: str
    
    # Radar data
    radar_confidence: float
    radar_distance: Optional[float]
    radar_speed: Optional[float]
    
    # Vehicle data
    vehicle_count: int
    vehicle_types: List[str]
    detection_confidence: float
    
    # Weather data
    temperature: Optional[float]
    humidity: Optional[float]
    weather_condition: Optional[str]
    
    # Camera data
    image_path: Optional[str]
    roi_data: Optional[Dict]
    
    # Location data
    location_id: str = "default"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'trigger_source': self.trigger_source,
            'radar_confidence': self.radar_confidence,
            'radar_distance': self.radar_distance,
            'radar_speed': self.radar_speed,
            'vehicle_count': self.vehicle_count,
            'vehicle_types': json.dumps(self.vehicle_types),
            'detection_confidence': self.detection_confidence,
            'temperature': self.temperature,
            'humidity': self.humidity,
            'weather_condition': self.weather_condition,
            'image_path': self.image_path,
            'roi_data': json.dumps(self.roi_data) if self.roi_data else None,
            'location_id': self.location_id
        }

class SimplifiedEnhancedDatabasePersistenceService:
    """
    Simplified enhanced database persistence service with SQLite-only architecture
    Focuses on reliable local persistence with comprehensive centralized logging
    """
    
    def __init__(self,
                 database_path: str = "/app/data/traffic_data.db",
                 redis_host: str = "redis",
                 redis_port: int = 6379,
                 batch_size: int = 100,
                 commit_interval_seconds: int = 30,
                 retention_days: int = 90):
        
        self.database_path = Path(database_path)
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.batch_size = batch_size
        self.commit_interval_seconds = commit_interval_seconds
        self.retention_days = retention_days
        
        # Service state
        self.running = False
        self.db_connection = None
        self.redis_client = None
        self.pubsub = None
        
        # Processing threads
        self.consumer_thread = None
        self.maintenance_thread = None
        
        # Statistics tracking
        self.stats = {
            "records_processed": 0,
            "records_stored": 0,
            "database_errors": 0,
            "redis_errors": 0,
            "last_record_time": None,
            "startup_time": None,
            "database_size_mb": 0.0,
            "total_records": 0,
            "avg_processing_time_ms": 0.0
        }
        
        # Processing queues and batching
        self.record_batch = []
        self.last_commit_time = time.time()
        self.processing_times = []
        
        logger.info("Simplified Enhanced Database Persistence Service initialized", extra={
            "business_event": "service_initialization",
            "database_path": str(self.database_path),
            "redis_host": self.redis_host,
            "batch_size": self.batch_size,
            "retention_days": self.retention_days
        })
    
    @logger.monitor_performance("database_initialization")
    def initialize_database(self) -> bool:
        """Initialize SQLite database with optimized schema and performance monitoring"""
        correlation_id = CorrelationContext.get_correlation_id() or str(uuid.uuid4())[:8]
        
        try:
            with CorrelationContext.set_correlation_id(correlation_id):
                # Ensure database directory exists
                self.database_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Connect to SQLite with optimizations
                self.db_connection = sqlite3.connect(
                    str(self.database_path),
                    check_same_thread=False,
                    timeout=30.0
                )
                
                # Enable WAL mode for better concurrent access
                self.db_connection.execute("PRAGMA journal_mode=WAL")
                self.db_connection.execute("PRAGMA synchronous=NORMAL")
                self.db_connection.execute("PRAGMA cache_size=10000")
                self.db_connection.execute("PRAGMA temp_store=MEMORY")
                
                # Create optimized schema
                cursor = self.db_connection.cursor()
                
                # Main traffic records table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS traffic_records (
                        id TEXT PRIMARY KEY,
                        timestamp TEXT NOT NULL,
                        trigger_source TEXT NOT NULL,
                        radar_confidence REAL,
                        radar_distance REAL,
                        radar_speed REAL,
                        vehicle_count INTEGER NOT NULL,
                        vehicle_types TEXT,
                        detection_confidence REAL NOT NULL,
                        temperature REAL,
                        humidity REAL,
                        weather_condition TEXT,
                        image_path TEXT,
                        roi_data TEXT,
                        location_id TEXT DEFAULT 'default',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Performance indexes
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON traffic_records(timestamp)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_trigger_source ON traffic_records(trigger_source)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_location_timestamp ON traffic_records(location_id, timestamp)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON traffic_records(created_at)")
                
                # Daily summaries table for reporting
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS daily_summaries (
                        date TEXT PRIMARY KEY,
                        location_id TEXT,
                        total_detections INTEGER,
                        avg_confidence REAL,
                        avg_vehicle_count REAL,
                        weather_conditions TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_summary_date_location ON daily_summaries(date, location_id)")
                
                # Service health tracking table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS service_health (
                        timestamp TEXT PRIMARY KEY,
                        service_name TEXT,
                        status TEXT,
                        metrics TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                self.db_connection.commit()
                cursor.close()
                
                # Get database statistics
                db_stats = self._get_database_stats()
                
                logger.info("SQLite database initialized successfully", extra={
                    "business_event": "database_initialization_success",
                    "correlation_id": correlation_id,
                    "database_path": str(self.database_path),
                    "database_size_mb": db_stats["size_mb"],
                    "total_records": db_stats["total_records"],
                    "wal_mode_enabled": True
                })
                
                return True
                
        except Exception as e:
            logger.error("Failed to initialize SQLite database", extra={
                "business_event": "database_initialization_failure",
                "correlation_id": correlation_id,
                "database_path": str(self.database_path),
                "error": str(e)
            })
            return False
    
    def connect_redis(self) -> bool:
        """Connect to Redis with enhanced error handling and logging"""
        try:
            if not REDIS_AVAILABLE:
                logger.error("Redis client not available", extra={
                    "business_event": "redis_connection_failure",
                    "error": "redis_module_not_available"
                })
                return False
            
            self.redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=10,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            start_time = time.time()
            self.redis_client.ping()
            connection_time_ms = (time.time() - start_time) * 1000
            
            # Subscribe to database events
            self.pubsub = self.redis_client.pubsub()
            self.pubsub.subscribe('database_events')
            
            logger.info("Redis connection established successfully", extra={
                "business_event": "redis_connection_established",
                "redis_host": self.redis_host,
                "redis_port": self.redis_port,
                "connection_time_ms": round(connection_time_ms, 2),
                "subscribed_channels": ["database_events"]
            })
            return True
            
        except Exception as e:
            logger.error("Failed to connect to Redis", extra={
                "business_event": "redis_connection_failure",
                "redis_host": self.redis_host,
                "redis_port": self.redis_port,
                "error": str(e)
            })
            return False
    
    @logger.monitor_performance("record_processing")
    def process_traffic_record(self, record_data: Dict[str, Any]) -> bool:
        """Process individual traffic record with performance monitoring"""
        correlation_id = record_data.get('correlation_id') or str(uuid.uuid4())[:8]
        
        try:
            with CorrelationContext.set_correlation_id(correlation_id):
                # Parse timestamp
                timestamp_str = record_data.get('timestamp', datetime.now().isoformat())
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                
                # Create traffic record
                traffic_record = TrafficRecord(
                    id=record_data.get('id', str(uuid.uuid4())),
                    timestamp=timestamp,
                    trigger_source=record_data.get('trigger_source', 'unknown'),
                    radar_confidence=record_data.get('radar_confidence', 0.0),
                    radar_distance=record_data.get('radar_distance'),
                    radar_speed=record_data.get('radar_speed'),
                    vehicle_count=record_data.get('vehicle_count', 0),
                    vehicle_types=record_data.get('vehicle_types', []),
                    detection_confidence=record_data.get('detection_confidence', 0.0),
                    temperature=record_data.get('temperature'),
                    humidity=record_data.get('humidity'),
                    weather_condition=record_data.get('weather_condition'),
                    image_path=record_data.get('image_path'),
                    roi_data=record_data.get('roi_data'),
                    location_id=record_data.get('location_id', 'default')
                )
                
                # Add to batch for processing
                self.record_batch.append(traffic_record)
                self.stats["records_processed"] += 1
                
                logger.debug("Traffic record processed for batch", extra={
                    "business_event": "record_processed",
                    "correlation_id": correlation_id,
                    "record_id": traffic_record.id,
                    "trigger_source": traffic_record.trigger_source,
                    "vehicle_count": traffic_record.vehicle_count,
                    "batch_size": len(self.record_batch)
                })
                
                # Check if batch is ready for commit
                current_time = time.time()
                batch_ready = (len(self.record_batch) >= self.batch_size or 
                             (current_time - self.last_commit_time) >= self.commit_interval_seconds)
                
                if batch_ready:
                    return self._commit_batch()
                
                return True
                
        except Exception as e:
            logger.error("Failed to process traffic record", extra={
                "business_event": "record_processing_failure",
                "correlation_id": correlation_id,
                "error": str(e),
                "record_data_keys": list(record_data.keys()) if record_data else None
            })
            self.stats["database_errors"] += 1
            return False
    
    @logger.monitor_performance("batch_commit")
    def _commit_batch(self) -> bool:
        """Commit batch of records to SQLite database with performance monitoring"""
        if not self.record_batch:
            return True
            
        correlation_id = CorrelationContext.get_correlation_id() or str(uuid.uuid4())[:8]
        batch_size = len(self.record_batch)
        
        try:
            with CorrelationContext.set_correlation_id(correlation_id):
                start_time = time.time()
                cursor = self.db_connection.cursor()
                
                # Prepare batch insert
                insert_sql = """
                    INSERT OR REPLACE INTO traffic_records 
                    (id, timestamp, trigger_source, radar_confidence, radar_distance, radar_speed,
                     vehicle_count, vehicle_types, detection_confidence, temperature, humidity,
                     weather_condition, image_path, roi_data, location_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                # Convert records to tuples for batch insert
                batch_data = []
                for record in self.record_batch:
                    record_dict = record.to_dict()
                    batch_data.append((
                        record_dict['id'],
                        record_dict['timestamp'],
                        record_dict['trigger_source'],
                        record_dict['radar_confidence'],
                        record_dict['radar_distance'],
                        record_dict['radar_speed'],
                        record_dict['vehicle_count'],
                        record_dict['vehicle_types'],
                        record_dict['detection_confidence'],
                        record_dict['temperature'],
                        record_dict['humidity'],
                        record_dict['weather_condition'],
                        record_dict['image_path'],
                        record_dict['roi_data'],
                        record_dict['location_id']
                    ))
                
                # Execute batch insert
                cursor.executemany(insert_sql, batch_data)
                self.db_connection.commit()
                cursor.close()
                
                # Update statistics
                commit_time_ms = (time.time() - start_time) * 1000
                self.stats["records_stored"] += batch_size
                self.last_commit_time = time.time()
                self.stats["last_record_time"] = datetime.now().isoformat()
                
                # Track processing times
                self.processing_times.append(commit_time_ms)
                if len(self.processing_times) > 100:  # Keep last 100 measurements
                    self.processing_times.pop(0)
                self.stats["avg_processing_time_ms"] = sum(self.processing_times) / len(self.processing_times)
                
                logger.info("Batch committed to SQLite database", extra={
                    "business_event": "batch_commit_success",
                    "correlation_id": correlation_id,
                    "batch_size": batch_size,
                    "commit_time_ms": round(commit_time_ms, 2),
                    "total_records_stored": self.stats["records_stored"],
                    "avg_processing_time_ms": round(self.stats["avg_processing_time_ms"], 2)
                })
                
                # Clear batch
                self.record_batch.clear()
                return True
                
        except Exception as e:
            logger.error("Failed to commit batch to database", extra={
                "business_event": "batch_commit_failure",
                "correlation_id": correlation_id,
                "batch_size": batch_size,
                "error": str(e)
            })
            self.stats["database_errors"] += 1
            # Don't clear batch on error - will retry
            return False
    
    def _get_database_stats(self) -> Dict[str, Any]:
        """Get comprehensive database statistics"""
        try:
            cursor = self.db_connection.cursor()
            
            # Get record count
            cursor.execute("SELECT COUNT(*) FROM traffic_records")
            total_records = cursor.fetchone()[0]
            
            # Get database size
            db_size_bytes = 0
            if self.database_path.exists():
                db_size_bytes = self.database_path.stat().st_size
            
            # Get recent activity
            cursor.execute("""
                SELECT COUNT(*) FROM traffic_records 
                WHERE timestamp > datetime('now', '-24 hours')
            """)
            recent_records = cursor.fetchone()[0]
            
            cursor.close()
            
            stats = {
                "total_records": total_records,
                "size_mb": round(db_size_bytes / (1024 * 1024), 2),
                "recent_24h_records": recent_records
            }
            
            self.stats["database_size_mb"] = stats["size_mb"]
            self.stats["total_records"] = stats["total_records"]
            
            return stats
            
        except Exception as e:
            logger.error("Failed to get database statistics", extra={
                "error": str(e)
            })
            return {"total_records": 0, "size_mb": 0.0, "recent_24h_records": 0}
    
    def start(self) -> bool:
        """Start the enhanced database persistence service"""
        try:
            logger.info("Starting Simplified Enhanced Database Persistence Service", extra={
                "business_event": "service_startup",
                "database_path": str(self.database_path),
                "batch_size": self.batch_size,
                "commit_interval_sec": self.commit_interval_seconds
            })
            
            # Initialize database
            if not self.initialize_database():
                logger.error("Cannot start without database initialization")
                return False
            
            # Connect to Redis
            if not self.connect_redis():
                logger.error("Cannot start without Redis connection")
                return False
            
            self.running = True
            self.stats["startup_time"] = time.time()
            
            # Start consumer thread
            self.consumer_thread = threading.Thread(
                target=self._consume_redis_messages,
                daemon=True
            )
            self.consumer_thread.start()
            
            # Start maintenance thread
            self.maintenance_thread = threading.Thread(
                target=self._maintenance_loop,
                daemon=True
            )
            self.maintenance_thread.start()
            
            logger.info("Simplified Enhanced Database Persistence Service started successfully", extra={
                "business_event": "service_startup_success",
                "database_initialized": self.db_connection is not None,
                "redis_connected": self.redis_client is not None
            })
            return True
            
        except Exception as e:
            logger.error("Failed to start Simplified Enhanced Database Persistence Service", extra={
                "business_event": "service_startup_failure",
                "error": str(e)
            })
            return False
    
    def _consume_redis_messages(self):
        """Background thread to consume Redis pub/sub messages with correlation tracking"""
        logger.info("Starting Redis message consumer", extra={
            "business_event": "redis_consumer_start"
        })
        
        try:
            for message in self.pubsub.listen():
                if not self.running:
                    break
                
                if message['type'] == 'message':
                    try:
                        # Parse message data
                        record_data = json.loads(message['data'])
                        
                        # Process the record
                        self.process_traffic_record(record_data)
                        
                    except json.JSONDecodeError as e:
                        logger.error("Invalid JSON in Redis message", extra={
                            "business_event": "redis_message_parse_failure",
                            "error": str(e),
                            "message_data": message['data'][:200]  # First 200 chars
                        })
                        self.stats["redis_errors"] += 1
                        
                    except Exception as e:
                        logger.error("Error processing Redis message", extra={
                            "business_event": "redis_message_processing_failure",
                            "error": str(e)
                        })
                        self.stats["redis_errors"] += 1
                        
        except Exception as e:
            logger.error("Redis consumer thread failed", extra={
                "business_event": "redis_consumer_failure",
                "error": str(e)
            })
        finally:
            logger.info("Redis message consumer stopped")
    
    def _maintenance_loop(self):
        """Background maintenance tasks with logging"""
        logger.info("Starting database maintenance loop", extra={
            "business_event": "maintenance_loop_start"
        })
        
        while self.running:
            try:
                time.sleep(300)  # Run maintenance every 5 minutes
                
                if self.running:
                    self._perform_maintenance()
                    
            except Exception as e:
                logger.error("Error in maintenance loop", extra={
                    "business_event": "maintenance_loop_error",
                    "error": str(e)
                })
    
    def _perform_maintenance(self):
        """Perform periodic maintenance tasks"""
        correlation_id = str(uuid.uuid4())[:8]
        
        try:
            with CorrelationContext.set_correlation_id(correlation_id):
                # Commit any pending batch
                if self.record_batch:
                    self._commit_batch()
                
                # Update database statistics
                db_stats = self._get_database_stats()
                
                # Clean old records if needed
                self._cleanup_old_records()
                
                # Log health status
                logger.info("Database maintenance completed", extra={
                    "business_event": "maintenance_completed",
                    "correlation_id": correlation_id,
                    "database_stats": db_stats,
                    "service_stats": self.get_service_stats()
                })
                
        except Exception as e:
            logger.error("Maintenance task failed", extra={
                "business_event": "maintenance_failure",
                "correlation_id": correlation_id,
                "error": str(e)
            })
    
    def _cleanup_old_records(self):
        """Clean up old records based on retention policy"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            
            cursor = self.db_connection.cursor()
            cursor.execute("""
                DELETE FROM traffic_records 
                WHERE timestamp < ?
            """, (cutoff_date.isoformat(),))
            
            deleted_count = cursor.rowcount
            self.db_connection.commit()
            cursor.close()
            
            if deleted_count > 0:
                logger.info("Old records cleaned up", extra={
                    "business_event": "record_cleanup",
                    "deleted_records": deleted_count,
                    "retention_days": self.retention_days,
                    "cutoff_date": cutoff_date.isoformat()
                })
                
        except Exception as e:
            logger.error("Failed to cleanup old records", extra={
                "business_event": "record_cleanup_failure",
                "error": str(e)
            })
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get comprehensive service statistics"""
        uptime_seconds = (time.time() - self.stats["startup_time"]) if self.stats["startup_time"] else 0
        
        return {
            **self.stats,
            "uptime_seconds": uptime_seconds,
            "service_running": self.running,
            "batch_queue_size": len(self.record_batch),
            "database_path": str(self.database_path),
            "architecture": "simplified_sqlite_only"
        }
    
    def stop(self):
        """Stop the database persistence service"""
        logger.info("Stopping Simplified Enhanced Database Persistence Service", extra={
            "business_event": "service_shutdown",
            "final_stats": self.get_service_stats()
        })
        
        self.running = False
        
        # Commit any remaining records
        if self.record_batch:
            self._commit_batch()
        
        # Close connections
        if self.pubsub:
            self.pubsub.close()
        if self.redis_client:
            self.redis_client.close()
        if self.db_connection:
            self.db_connection.close()
        
        logger.info("Simplified Enhanced Database Persistence Service stopped", extra={
            "business_event": "service_shutdown_complete"
        })


def main():
    """Main entry point for simplified enhanced database persistence service"""
    try:
        # Configuration from environment
        service = SimplifiedEnhancedDatabasePersistenceService(
            database_path=os.environ.get('DATABASE_PATH', '/app/data/traffic_data.db'),
            redis_host=os.environ.get('REDIS_HOST', 'redis'),
            redis_port=int(os.environ.get('REDIS_PORT', 6379)),
            batch_size=int(os.environ.get('BATCH_SIZE', 100)),
            commit_interval_seconds=int(os.environ.get('COMMIT_INTERVAL_SEC', 30)),
            retention_days=int(os.environ.get('RETENTION_DAYS', 90))
        )
        
        # Start service
        if service.start():
            logger.info("Simplified Enhanced Database Persistence Service running successfully")
            
            # Keep running until interrupted
            try:
                while service.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Shutdown requested by user")
            finally:
                service.stop()
        else:
            logger.error("Failed to start Simplified Enhanced Database Persistence Service")
            sys.exit(1)
            
    except Exception as e:
        logger.error("Simplified Enhanced Database Persistence Service failed", extra={
            "business_event": "service_failure",
            "error": str(e)
        })
        sys.exit(1)


if __name__ == "__main__":
    main()