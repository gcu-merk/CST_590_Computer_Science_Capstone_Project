#!/usr/bin/env python3
"""
Enhanced Database Persistence Service - WITH CENTRALIZED LOGGING
Consumes consolidated traffic data from Redis and stores in permanent database with full observability

This enhanced service implements the final stage of the data pipeline with comprehensive logging:
Radar Motion -> Consolidator -> Redis -> Enhanced Database Persistence -> Long-term Storage

Enhanced Features:
- Centralized logging with ServiceLogger and CorrelationContext integration
- Query performance monitoring and optimization tracking
- Database operation correlation tracking across all queries
- Real-time database health and performance monitoring
- Business event logging for all database operations
- Error tracking and recovery monitoring

Architecture:
- Listens for 'database_events' on Redis pub/sub with correlation tracking
- Consumes consolidated traffic records with full logging
- Stores structured data in PostgreSQL/SQLite with performance monitoring
- Implements data retention and cleanup with operational logging
- Provides efficient querying with query performance tracking
"""

import time
import json
import threading
import sqlite3
import psycopg2
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from pathlib import Path
import os
import sys
from contextlib import contextmanager
import uuid

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
    correlation_id: Optional[str] = None
    
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

class EnhancedDatabasePersistenceService:
    """
    Enhanced database persistence service with centralized logging and correlation tracking
    Provides long-term storage optimization with full observability
    """
    
    def __init__(self,
                 redis_host: str = "redis",
                 redis_port: int = 6379,
                 postgres_host: str = None,
                 postgres_db: str = None,
                 postgres_user: str = None,
                 postgres_password: str = None,
                 sqlite_path: str = "/app/data/traffic_data.db",
                 retention_days: int = 90,
                 batch_size: int = 100):
        
        if not REDIS_AVAILABLE:
            logger.error("Redis required for database persistence service", extra={
                "business_event": "service_initialization_failure",
                "error": "redis_unavailable"
            })
            raise RuntimeError("Redis required for database persistence service")
        
        # Configuration
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.postgres_config = {
            "host": postgres_host or os.environ.get('POSTGRES_HOST'),
            "database": postgres_db or os.environ.get('POSTGRES_DB'),
            "user": postgres_user or os.environ.get('POSTGRES_USER'),
            "password": postgres_password or os.environ.get('POSTGRES_PASSWORD')
        }
        self.sqlite_path = sqlite_path
        self.retention_days = retention_days
        self.batch_size = batch_size
        
        # Service state
        self.running = False
        self.redis_client = None
        self.pubsub = None
        self.postgres_connection = None
        self.sqlite_connection = None
        
        # Processing threads
        self.event_thread = None
        self.cleanup_thread = None
        self.health_monitor_thread = None
        
        # Statistics tracking
        self.stats = {
            "records_processed": 0,
            "batch_operations": 0,
            "queries_executed": 0,
            "avg_query_time_ms": 0.0,
            "database_errors": 0,
            "startup_time": None,
            "last_health_check": None
        }
        
        logger.info("Enhanced Database Persistence Service initialized", extra={
            "business_event": "service_initialization",
            "redis_host": self.redis_host,
            "postgres_available": all(self.postgres_config.values()),
            "sqlite_path": self.sqlite_path,
            "retention_days": retention_days
        })
    
    @contextmanager
    def database_operation(self, operation_name: str, correlation_id: str = None):
        """Context manager for database operations with logging and monitoring"""
        correlation_id = correlation_id or CorrelationContext.get_correlation_id()
        start_time = time.time()
        
        try:
            logger.debug("Database operation started", extra={
                "business_event": "database_operation_start",
                "correlation_id": correlation_id,
                "operation": operation_name
            })
            
            yield
            
            # Log successful operation
            duration_ms = (time.time() - start_time) * 1000
            
            # Update average query time
            if self.stats["queries_executed"] > 0:
                current_avg = self.stats["avg_query_time_ms"]
                new_avg = ((current_avg * (self.stats["queries_executed"] - 1)) + duration_ms) / self.stats["queries_executed"]
                self.stats["avg_query_time_ms"] = round(new_avg, 2)
            else:
                self.stats["avg_query_time_ms"] = round(duration_ms, 2)
            
            logger.info("Database operation completed successfully", extra={
                "business_event": "database_operation_success",
                "correlation_id": correlation_id,
                "operation": operation_name,
                "duration_ms": round(duration_ms, 2)
            })
            
        except Exception as e:
            # Log operation failure
            duration_ms = (time.time() - start_time) * 1000
            self.stats["database_errors"] += 1
            
            logger.error("Database operation failed", extra={
                "business_event": "database_operation_failure",
                "correlation_id": correlation_id,
                "operation": operation_name,
                "duration_ms": round(duration_ms, 2),
                "error": str(e),
                "error_type": type(e).__name__
            })
            raise
        finally:
            self.stats["queries_executed"] += 1
    
    def connect_redis(self) -> bool:
        """Connect to Redis with enhanced logging"""
        try:
            self.redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=10
            )
            
            # Test connection
            with self.database_operation("redis_connection_test"):
                self.redis_client.ping()
            
            # Setup pub/sub for database events
            self.pubsub = self.redis_client.pubsub()
            self.pubsub.subscribe("database_events")
            
            logger.info("Redis connection established successfully", extra={
                "business_event": "redis_connection_established",
                "redis_host": self.redis_host,
                "redis_port": self.redis_port
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
    
    def connect_postgres(self) -> bool:
        """Connect to PostgreSQL with enhanced logging"""
        if not all(self.postgres_config.values()):
            logger.info("PostgreSQL configuration incomplete, skipping PostgreSQL connection", extra={
                "business_event": "postgres_connection_skipped",
                "reason": "incomplete_configuration"
            })
            return True  # Not an error, just using SQLite only
        
        try:
            self.postgres_connection = psycopg2.connect(
                host=self.postgres_config["host"],
                database=self.postgres_config["database"],
                user=self.postgres_config["user"],
                password=self.postgres_config["password"],
                connect_timeout=10
            )
            self.postgres_connection.autocommit = True
            
            # Test connection
            with self.database_operation("postgres_connection_test"):
                cursor = self.postgres_connection.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
            
            logger.info("PostgreSQL connection established successfully", extra={
                "business_event": "postgres_connection_established",
                "postgres_host": self.postgres_config["host"],
                "postgres_db": self.postgres_config["database"]
            })
            return True
            
        except Exception as e:
            logger.error("Failed to connect to PostgreSQL", extra={
                "business_event": "postgres_connection_failure",
                "postgres_host": self.postgres_config.get("host"),
                "error": str(e)
            })
            return False
    
    def init_sqlite_database(self) -> bool:
        """Initialize SQLite database with enhanced logging"""
        try:
            # Ensure directory exists
            db_dir = Path(self.sqlite_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)
            
            with self.database_operation("sqlite_initialization"):
                self.sqlite_connection = sqlite3.connect(
                    self.sqlite_path,
                    check_same_thread=False,
                    isolation_level=None  # Autocommit mode
                )
                
                # Enable optimizations
                self.sqlite_connection.execute("PRAGMA journal_mode=WAL")
                self.sqlite_connection.execute("PRAGMA synchronous=NORMAL")
                self.sqlite_connection.execute("PRAGMA cache_size=10000")
                self.sqlite_connection.execute("PRAGMA temp_store=memory")
                
                # Create optimized table schema
                self.sqlite_connection.execute("""
                    CREATE TABLE IF NOT EXISTS traffic_records (
                        id TEXT PRIMARY KEY,
                        timestamp DATETIME NOT NULL,
                        trigger_source TEXT NOT NULL,
                        correlation_id TEXT,
                        
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
                indexes = [
                    "CREATE INDEX IF NOT EXISTS idx_timestamp ON traffic_records(timestamp)",
                    "CREATE INDEX IF NOT EXISTS idx_trigger_source ON traffic_records(trigger_source)",
                    "CREATE INDEX IF NOT EXISTS idx_correlation_id ON traffic_records(correlation_id)",
                    "CREATE INDEX IF NOT EXISTS idx_radar_speed ON traffic_records(radar_speed) WHERE radar_speed IS NOT NULL",
                    "CREATE INDEX IF NOT EXISTS idx_vehicle_count ON traffic_records(vehicle_count) WHERE vehicle_count IS NOT NULL"
                ]
                
                for index_sql in indexes:
                    self.sqlite_connection.execute(index_sql)
                
                # Create summary tables for analytics
                self.sqlite_connection.execute("""
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
            
            logger.info("SQLite database initialized successfully", extra={
                "business_event": "sqlite_initialization_success",
                "database_path": self.sqlite_path
            })
            return True
            
        except Exception as e:
            logger.error("Failed to initialize SQLite database", extra={
                "business_event": "sqlite_initialization_failure",
                "database_path": self.sqlite_path,
                "error": str(e)
            })
            return False
    
    def init_postgres_schema(self) -> bool:
        """Initialize PostgreSQL schema with enhanced logging"""
        if not self.postgres_connection:
            return True  # Not using PostgreSQL
        
        try:
            with self.database_operation("postgres_schema_initialization"):
                cursor = self.postgres_connection.cursor()
                
                # Create main traffic records table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS traffic_records (
                        id VARCHAR(255) PRIMARY KEY,
                        timestamp TIMESTAMP NOT NULL,
                        trigger_source VARCHAR(100) NOT NULL,
                        correlation_id VARCHAR(100),
                        
                        -- Radar measurements
                        radar_speed DECIMAL(10,2),
                        radar_direction VARCHAR(50),
                        radar_magnitude DECIMAL(10,2),
                        
                        -- Environmental conditions
                        air_temperature DECIMAL(5,2),
                        humidity DECIMAL(5,2),
                        airport_weather TEXT,
                        
                        -- Vehicle detection data
                        vehicle_count INTEGER,
                        primary_vehicle_type VARCHAR(100),
                        detection_confidence DECIMAL(5,4),
                        
                        -- Processing metadata
                        processing_notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes
                indexes = [
                    "CREATE INDEX IF NOT EXISTS idx_traffic_timestamp ON traffic_records(timestamp)",
                    "CREATE INDEX IF NOT EXISTS idx_traffic_trigger_source ON traffic_records(trigger_source)",
                    "CREATE INDEX IF NOT EXISTS idx_traffic_correlation_id ON traffic_records(correlation_id)",
                    "CREATE INDEX IF NOT EXISTS idx_traffic_radar_speed ON traffic_records(radar_speed) WHERE radar_speed IS NOT NULL",
                    "CREATE INDEX IF NOT EXISTS idx_traffic_vehicle_count ON traffic_records(vehicle_count) WHERE vehicle_count IS NOT NULL"
                ]
                
                for index_sql in indexes:
                    try:
                        cursor.execute(index_sql)
                    except psycopg2.Error as e:
                        # Index might already exist, continue
                        logger.debug(f"Index creation note: {e}")
                
                # Create summary table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS daily_summary (
                        date DATE PRIMARY KEY,
                        total_detections INTEGER DEFAULT 0,
                        avg_speed DECIMAL(10,2),
                        max_speed DECIMAL(10,2),
                        vehicle_types TEXT,  -- JSON array
                        weather_conditions TEXT,  -- JSON array
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cursor.close()
            
            logger.info("PostgreSQL schema initialized successfully", extra={
                "business_event": "postgres_schema_initialization_success",
                "postgres_db": self.postgres_config["database"]
            })
            return True
            
        except Exception as e:
            logger.error("Failed to initialize PostgreSQL schema", extra={
                "business_event": "postgres_schema_initialization_failure",
                "postgres_db": self.postgres_config["database"],
                "error": str(e)
            })
            return False
    
    @logger.monitor_performance("traffic_record_insertion")
    def insert_traffic_record(self, record: TrafficRecord) -> bool:
        """Insert traffic record with correlation tracking and performance monitoring"""
        correlation_id = record.correlation_id or CorrelationContext.get_correlation_id()
        
        try:
            with CorrelationContext.set_correlation_id(correlation_id):
                # Insert into SQLite
                if self.sqlite_connection:
                    with self.database_operation("sqlite_insert", correlation_id):
                        cursor = self.sqlite_connection.cursor()
                        cursor.execute("""
                            INSERT OR REPLACE INTO traffic_records 
                            (id, timestamp, trigger_source, correlation_id, radar_speed, radar_direction, 
                             radar_magnitude, air_temperature, humidity, airport_weather, vehicle_count, 
                             primary_vehicle_type, detection_confidence, processing_notes)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            record.id, record.timestamp, record.trigger_source, correlation_id,
                            record.radar_speed, record.radar_direction, record.radar_magnitude,
                            record.air_temperature, record.humidity, record.airport_weather,
                            record.vehicle_count, record.primary_vehicle_type, record.detection_confidence,
                            record.processing_notes
                        ))
                        cursor.close()
                
                # Insert into PostgreSQL if available
                if self.postgres_connection:
                    with self.database_operation("postgres_insert", correlation_id):
                        cursor = self.postgres_connection.cursor()
                        cursor.execute("""
                            INSERT INTO traffic_records 
                            (id, timestamp, trigger_source, correlation_id, radar_speed, radar_direction,
                             radar_magnitude, air_temperature, humidity, airport_weather, vehicle_count,
                             primary_vehicle_type, detection_confidence, processing_notes)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (id) DO UPDATE SET
                                timestamp = EXCLUDED.timestamp,
                                trigger_source = EXCLUDED.trigger_source,
                                correlation_id = EXCLUDED.correlation_id,
                                radar_speed = EXCLUDED.radar_speed,
                                radar_direction = EXCLUDED.radar_direction,
                                radar_magnitude = EXCLUDED.radar_magnitude,
                                air_temperature = EXCLUDED.air_temperature,
                                humidity = EXCLUDED.humidity,
                                airport_weather = EXCLUDED.airport_weather,
                                vehicle_count = EXCLUDED.vehicle_count,
                                primary_vehicle_type = EXCLUDED.primary_vehicle_type,
                                detection_confidence = EXCLUDED.detection_confidence,
                                processing_notes = EXCLUDED.processing_notes
                        """, (
                            record.id, record.timestamp, record.trigger_source, correlation_id,
                            record.radar_speed, record.radar_direction, record.radar_magnitude,
                            record.air_temperature, record.humidity, record.airport_weather,
                            record.vehicle_count, record.primary_vehicle_type, record.detection_confidence,
                            record.processing_notes
                        ))
                        cursor.close()
                
                self.stats["records_processed"] += 1
                
                logger.info("Traffic record inserted successfully", extra={
                    "business_event": "traffic_record_inserted",
                    "correlation_id": correlation_id,
                    "record_id": record.id,
                    "trigger_source": record.trigger_source,
                    "vehicle_count": record.vehicle_count,
                    "radar_speed": record.radar_speed
                })
                
                return True
                
        except Exception as e:
            logger.error("Failed to insert traffic record", extra={
                "business_event": "traffic_record_insertion_failure",
                "correlation_id": correlation_id,
                "record_id": record.id,
                "error": str(e)
            })
            return False
    
    def start(self) -> bool:
        """Start the enhanced persistence service"""
        try:
            logger.info("Starting Enhanced Database Persistence Service", extra={
                "business_event": "service_startup",
                "sqlite_path": self.sqlite_path,
                "postgres_enabled": all(self.postgres_config.values())
            })
            
            # Connect to Redis
            if not self.connect_redis():
                logger.error("Cannot start without Redis connection")
                return False
            
            # Connect to databases
            if not self.init_sqlite_database():
                logger.error("Cannot start without SQLite database")
                return False
            
            if not self.connect_postgres():
                logger.warning("PostgreSQL connection failed, continuing with SQLite only")
            else:
                self.init_postgres_schema()
            
            self.running = True
            self.stats["startup_time"] = time.time()
            
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
            
            self.health_monitor_thread = threading.Thread(
                target=self._health_monitor_loop,
                daemon=True
            )
            self.health_monitor_thread.start()
            
            logger.info("Enhanced Database Persistence Service started successfully", extra={
                "business_event": "service_startup_success",
                "databases_connected": {
                    "sqlite": self.sqlite_connection is not None,
                    "postgres": self.postgres_connection is not None
                }
            })
            return True
            
        except Exception as e:
            logger.error("Failed to start Enhanced Database Persistence Service", extra={
                "business_event": "service_startup_failure",
                "error": str(e)
            })
            return False
    
    def _process_database_events(self):
        """Process database persistence events with correlation tracking"""
        logger.info("Processing database persistence events with correlation tracking", extra={
            "business_event": "event_processing_start"
        })
        
        while self.running:
            try:
                message = self.pubsub.get_message(timeout=1.0)
                if message and message['type'] == 'message':
                    # Generate or extract correlation ID
                    correlation_id = str(uuid.uuid4())[:8]
                    
                    with CorrelationContext.set_correlation_id(correlation_id):
                        logger.debug("Processing database event", extra={
                            "business_event": "database_event_received",
                            "correlation_id": correlation_id,
                            "message_size": len(message['data']) if message['data'] else 0
                        })
                        
                        # Process the database event
                        self._handle_database_event(message['data'], correlation_id)
                        
            except Exception as e:
                logger.error("Error processing database event", extra={
                    "business_event": "database_event_processing_error",
                    "error": str(e)
                })
                time.sleep(1)  # Prevent tight error loop
    
    def _handle_database_event(self, event_data: str, correlation_id: str):
        """Handle individual database event with correlation tracking"""
        try:
            # Parse event data
            event = json.loads(event_data)
            
            # Create traffic record
            record = TrafficRecord(
                id=event.get('id', f"rec_{int(time.time())}"),
                timestamp=datetime.fromisoformat(event.get('timestamp', datetime.now().isoformat())),
                trigger_source=event.get('trigger_source', 'unknown'),
                correlation_id=correlation_id,
                radar_speed=event.get('radar_speed'),
                radar_direction=event.get('radar_direction'),
                radar_magnitude=event.get('radar_magnitude'),
                air_temperature=event.get('air_temperature'),
                humidity=event.get('humidity'),
                airport_weather=event.get('airport_weather'),
                vehicle_count=event.get('vehicle_count'),
                primary_vehicle_type=event.get('primary_vehicle_type'),
                detection_confidence=event.get('detection_confidence'),
                processing_notes=event.get('processing_notes')
            )
            
            # Insert record
            self.insert_traffic_record(record)
            
        except Exception as e:
            logger.error("Failed to handle database event", extra={
                "business_event": "database_event_handling_failure",
                "correlation_id": correlation_id,
                "error": str(e),
                "event_data_preview": event_data[:200] if event_data else None
            })
    
    def _cleanup_loop(self):
        """Background cleanup loop with logging"""
        logger.info("Starting database cleanup loop", extra={
            "business_event": "cleanup_loop_start",
            "retention_days": self.retention_days
        })
        
        while self.running:
            try:
                time.sleep(3600)  # Run cleanup every hour
                self._perform_cleanup()
            except Exception as e:
                logger.error("Error in cleanup loop", extra={
                    "business_event": "cleanup_loop_error",
                    "error": str(e)
                })
    
    def _perform_cleanup(self):
        """Perform database cleanup with monitoring"""
        correlation_id = str(uuid.uuid4())[:8]
        
        with CorrelationContext.set_correlation_id(correlation_id):
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            
            try:
                # Cleanup SQLite
                if self.sqlite_connection:
                    with self.database_operation("sqlite_cleanup", correlation_id):
                        cursor = self.sqlite_connection.cursor()
                        cursor.execute("DELETE FROM traffic_records WHERE timestamp < ?", (cutoff_date,))
                        deleted_sqlite = cursor.rowcount
                        cursor.close()
                
                # Cleanup PostgreSQL
                deleted_postgres = 0
                if self.postgres_connection:
                    with self.database_operation("postgres_cleanup", correlation_id):
                        cursor = self.postgres_connection.cursor()
                        cursor.execute("DELETE FROM traffic_records WHERE timestamp < %s", (cutoff_date,))
                        deleted_postgres = cursor.rowcount
                        cursor.close()
                
                logger.info("Database cleanup completed", extra={
                    "business_event": "database_cleanup_completed",
                    "correlation_id": correlation_id,
                    "cutoff_date": cutoff_date.isoformat(),
                    "deleted_sqlite_records": deleted_sqlite if self.sqlite_connection else 0,
                    "deleted_postgres_records": deleted_postgres
                })
                
            except Exception as e:
                logger.error("Database cleanup failed", extra={
                    "business_event": "database_cleanup_failure",
                    "correlation_id": correlation_id,
                    "error": str(e)
                })
    
    def _health_monitor_loop(self):
        """Background health monitoring loop"""
        while self.running:
            try:
                time.sleep(300)  # Check health every 5 minutes
                self._perform_health_check()
            except Exception as e:
                logger.error("Error in health monitoring loop", extra={
                    "business_event": "health_monitor_error",
                    "error": str(e)
                })
    
    def _perform_health_check(self):
        """Perform comprehensive health check"""
        correlation_id = str(uuid.uuid4())[:8]
        
        with CorrelationContext.set_correlation_id(correlation_id):
            health_status = {
                "sqlite_healthy": False,
                "postgres_healthy": False,
                "redis_healthy": False,
                "records_processed": self.stats["records_processed"],
                "avg_query_time_ms": self.stats["avg_query_time_ms"],
                "database_errors": self.stats["database_errors"]
            }
            
            # Test SQLite
            try:
                if self.sqlite_connection:
                    cursor = self.sqlite_connection.cursor()
                    cursor.execute("SELECT COUNT(*) FROM traffic_records")
                    cursor.fetchone()
                    cursor.close()
                    health_status["sqlite_healthy"] = True
            except Exception:
                health_status["sqlite_healthy"] = False
            
            # Test PostgreSQL
            try:
                if self.postgres_connection:
                    cursor = self.postgres_connection.cursor()
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
                    cursor.close()
                    health_status["postgres_healthy"] = True
            except Exception:
                health_status["postgres_healthy"] = False
            
            # Test Redis
            try:
                if self.redis_client:
                    self.redis_client.ping()
                    health_status["redis_healthy"] = True
            except Exception:
                health_status["redis_healthy"] = False
            
            self.stats["last_health_check"] = datetime.now().isoformat()
            
            logger.info("Database health check completed", extra={
                "business_event": "database_health_check",
                "correlation_id": correlation_id,
                "health_status": health_status
            })
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get comprehensive service statistics"""
        uptime_seconds = (time.time() - self.stats["startup_time"]) if self.stats["startup_time"] else 0
        
        return {
            **self.stats,
            "uptime_seconds": uptime_seconds,
            "databases_connected": {
                "sqlite": self.sqlite_connection is not None,
                "postgres": self.postgres_connection is not None,
                "redis": self.redis_client is not None
            },
            "service_running": self.running
        }
    
    def stop(self):
        """Stop the persistence service"""
        logger.info("Stopping Enhanced Database Persistence Service", extra={
            "business_event": "service_shutdown",
            "final_stats": self.get_service_stats()
        })
        
        self.running = False
        
        # Close connections
        if self.pubsub:
            self.pubsub.close()
        if self.redis_client:
            self.redis_client.close()
        if self.sqlite_connection:
            self.sqlite_connection.close()
        if self.postgres_connection:
            self.postgres_connection.close()
        
        logger.info("Enhanced Database Persistence Service stopped", extra={
            "business_event": "service_shutdown_complete"
        })


def main():
    """Main entry point for enhanced database persistence service"""
    try:
        # Configuration from environment
        service = EnhancedDatabasePersistenceService(
            redis_host=os.environ.get('REDIS_HOST', 'redis'),
            redis_port=int(os.environ.get('REDIS_PORT', 6379)),
            sqlite_path=os.environ.get('DATABASE_PATH', '/app/data/traffic_data.db'),
            retention_days=int(os.environ.get('RETENTION_DAYS', 90))
        )
        
        # Start service
        if service.start():
            logger.info("Enhanced Database Persistence Service running successfully")
            
            # Keep running until interrupted
            try:
                while service.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Shutdown requested by user")
            finally:
                service.stop()
        else:
            logger.error("Failed to start Enhanced Database Persistence Service")
            sys.exit(1)
            
    except Exception as e:
        logger.error("Enhanced Database Persistence Service failed", extra={
            "business_event": "service_failure",
            "error": str(e)
        })
        sys.exit(1)


if __name__ == "__main__":
    main()