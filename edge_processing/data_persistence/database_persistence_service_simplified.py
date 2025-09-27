#!/usr/bin/env python3
"""
Enhanced Database Persistence Service - NORMALIZED 3NF SCHEMA - WITH CENTRALIZED LOGGING
Enhanced version with normalized 3NF database schema and centralized logging integration

This enhanced service implements proper database normalization:
- Normalized 3NF schema with separate tables for traffic, radar, camera, weather data
- Enhanced with ServiceLogger and CorrelationContext for observability
- Improved performance monitoring and business event tracking
- Multi-table insertion with transaction management for data integrity
- Backwards compatibility with legacy schema detection
- Version: 2.0 (Normalized Schema)

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

# ============================================================
# NORMALIZED 3NF DATABASE ENTITIES
# ============================================================

@dataclass
class TrafficDetection:
    """Core traffic detection record (3NF normalized)"""
    id: str
    correlation_id: str
    timestamp: float  # Unix timestamp for precision
    trigger_source: str
    location_id: str = "default"
    processing_metadata: Optional[Dict] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'correlation_id': self.correlation_id,
            'timestamp': self.timestamp,
            'trigger_source': self.trigger_source,
            'location_id': self.location_id,
            'processing_metadata': json.dumps(self.processing_metadata) if self.processing_metadata else None
        }

@dataclass  
class RadarDetection:
    """Radar-specific detection data (3NF normalized)"""
    detection_id: str
    speed_mph: float
    speed_mps: float
    confidence: float
    alert_level: str
    direction: Optional[str] = None
    distance: Optional[float] = None
    detection_source_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'detection_id': self.detection_id,
            'speed_mph': self.speed_mph,
            'speed_mps': self.speed_mps,
            'confidence': self.confidence,
            'alert_level': self.alert_level,
            'direction': self.direction,
            'distance': self.distance,
            'detection_source_id': self.detection_source_id
        }

@dataclass
class CameraDetection:
    """Camera/AI detection data (3NF normalized)"""
    detection_id: str
    vehicle_count: int = 0
    vehicle_types: Optional[List[str]] = None
    detection_confidence: Optional[float] = None
    image_path: Optional[str] = None
    roi_data: Optional[Dict] = None
    inference_time_ms: Optional[int] = None
    camera_source: str = "imx500"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'detection_id': self.detection_id,
            'vehicle_count': self.vehicle_count,
            'vehicle_types': json.dumps(self.vehicle_types) if self.vehicle_types else None,
            'detection_confidence': self.detection_confidence,
            'image_path': self.image_path,
            'roi_data': json.dumps(self.roi_data) if self.roi_data else None,
            'inference_time_ms': self.inference_time_ms,
            'camera_source': self.camera_source
        }

@dataclass
class WeatherCondition:
    """Weather condition data (3NF normalized, time-bucketed)"""
    id: Optional[int] = None
    timestamp: Optional[float] = None
    source: Optional[str] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    conditions: Optional[str] = None
    wind_speed: Optional[float] = None
    pressure: Optional[float] = None
    visibility: Optional[float] = None
    raw_data: Optional[Dict] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp,
            'source': self.source,
            'temperature': self.temperature,
            'humidity': self.humidity,
            'conditions': self.conditions,
            'wind_speed': self.wind_speed,
            'pressure': self.pressure,
            'visibility': self.visibility,
            'raw_data': json.dumps(self.raw_data) if self.raw_data else None
        }

# Legacy TrafficRecord for backwards compatibility during migration
@dataclass
class TrafficRecord:
    """Legacy structured traffic record (DEPRECATED - use normalized entities)"""
    id: str
    timestamp: datetime
    trigger_source: str
    radar_confidence: float
    radar_distance: Optional[float]
    radar_speed: Optional[float]
    vehicle_count: int
    vehicle_types: List[str]
    detection_confidence: float
    temperature: Optional[float]
    humidity: Optional[float]
    weather_condition: Optional[str]
    image_path: Optional[str]
    roi_data: Optional[Dict]
    location_id: str = "default"

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
        
        # Redis stream configuration
        self.stream_name = "traffic:consolidated"
        self.consumer_group = "database_persistence"
        self.consumer_name = "persistence_worker"
        
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
        self.record_batch = []  # Legacy batch for backward compatibility
        self.normalized_batch = []  # New normalized 3NF batch
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
                
                # ============================================================
                # NORMALIZED 3NF SCHEMA - TRAFFIC MONITORING SYSTEM
                # ============================================================
                
                # Core traffic detections table (1NF - atomic values only)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS traffic_detections (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        consolidation_id TEXT UNIQUE NOT NULL,
                        correlation_id TEXT NOT NULL,
                        timestamp REAL NOT NULL,
                        trigger_source TEXT NOT NULL,
                        location_id TEXT DEFAULT 'default',
                        processing_metadata TEXT, -- JSON for processor version, etc.
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Radar detection data (2NF - functionally dependent on detection_id)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS radar_detections (
                        detection_id INTEGER PRIMARY KEY,
                        speed_mph REAL NOT NULL,
                        speed_mps REAL NOT NULL,
                        confidence REAL NOT NULL,
                        alert_level TEXT NOT NULL,
                        direction TEXT,
                        distance REAL,
                        detection_source_id TEXT,
                        FOREIGN KEY (detection_id) REFERENCES traffic_detections(id) ON DELETE CASCADE
                    )
                """)
                
                # Camera/AI detection data (2NF - functionally dependent on detection_id)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS camera_detections (
                        detection_id INTEGER PRIMARY KEY,
                        vehicle_count INTEGER DEFAULT 0,
                        detection_confidence REAL,
                        vehicle_types TEXT, -- JSON array
                        processing_time REAL,
                        image_metadata TEXT, -- JSON for image details
                        FOREIGN KEY (detection_id) REFERENCES traffic_detections(id) ON DELETE CASCADE
                    )
                """)
                
                # Weather conditions (3NF - independent entity, time-bucketed)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS weather_conditions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp REAL UNIQUE NOT NULL,
                        temperature REAL,
                        humidity REAL,
                        pressure REAL,
                        weather_source TEXT DEFAULT 'dht22',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Traffic-Weather correlation (3NF - relationship table)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS traffic_weather_correlation (
                        traffic_detection_id INTEGER,
                        weather_condition_id INTEGER,
                        correlation_strength REAL DEFAULT 1.0,
                        PRIMARY KEY (traffic_detection_id, weather_condition_id),
                        FOREIGN KEY (traffic_detection_id) REFERENCES traffic_detections(id) ON DELETE CASCADE,
                        FOREIGN KEY (weather_condition_id) REFERENCES weather_conditions(id) ON DELETE CASCADE
                    )
                """)
                
                # ============================================================
                # CONSOLIDATED EVENTS TABLE - JSON SOURCE OF TRUTH
                # ============================================================
                
                # Original consolidated JSON data for API efficiency
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS consolidated_events (
                        consolidation_id TEXT PRIMARY KEY,
                        event_json TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (consolidation_id) REFERENCES traffic_detections(consolidation_id) ON DELETE CASCADE
                    )
                """)
                
                # ============================================================
                # PERFORMANCE INDEXES FOR NORMALIZED SCHEMA
                # ============================================================
                
                # Core detections indexes
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_traffic_consolidation_id ON traffic_detections(consolidation_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_detections_timestamp ON traffic_detections(timestamp)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_detections_correlation ON traffic_detections(correlation_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_detections_source ON traffic_detections(trigger_source)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_detections_location_time ON traffic_detections(location_id, timestamp)")
                
                # Radar indexes
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_radar_speed ON radar_detections(speed_mph)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_radar_alert_level ON radar_detections(alert_level)")
                
                # Camera indexes  
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_camera_vehicle_count ON camera_detections(vehicle_count)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_camera_confidence ON camera_detections(detection_confidence)")
                
                # Weather indexes
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_weather_timestamp ON weather_conditions(timestamp)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_weather_source ON weather_conditions(weather_source)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_weather_temperature ON weather_conditions(temperature)")
                
                # Correlation indexes
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_correlation_detection ON traffic_weather_correlation(traffic_detection_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_correlation_weather ON traffic_weather_correlation(weather_condition_id)")
                
                # Consolidated events indexes
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_consolidated_created_at ON consolidated_events(created_at)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_consolidated_id_time ON consolidated_events(consolidation_id, created_at)")
                
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
                
                # Weather analysis tables (consolidated from weather_data_storage)
                cursor.execute("""
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
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS weather_traffic_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        event_data TEXT,
                        weather_id INTEGER,
                        created_at REAL NOT NULL,
                        FOREIGN KEY (weather_id) REFERENCES weather_analysis (id)
                    )
                """)
                
                cursor.execute("""
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
                """)
                
                # Create weather analysis indexes for performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_weather_analysis_timestamp ON weather_analysis(timestamp)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_weather_traffic_events_timestamp ON weather_traffic_events(timestamp)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_weather_traffic_events_weather_id ON weather_traffic_events(weather_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_weather_summaries_period ON weather_summaries(period_start, period_type)")
                
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
            import traceback
            logger.error("Failed to initialize SQLite database", extra={
                "business_event": "database_initialization_failure",
                "correlation_id": correlation_id,
                "database_path": str(self.database_path),
                "error": str(e),
                "error_type": type(e).__name__,
                "traceback": traceback.format_exc()
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
            
            # Setup Redis stream consumer for traffic:consolidated
            self.stream_name = "traffic:consolidated"
            self.consumer_group = "database_persistence"
            self.consumer_name = "persistence_worker"
            
            # Create consumer group if it doesn't exist
            try:
                self.redis_client.xgroup_create(
                    self.stream_name,
                    self.consumer_group,
                    id='0',
                    mkstream=True
                )
                logger.info("Created Redis stream consumer group", extra={
                    "business_event": "redis_consumer_group_created",
                    "stream_name": self.stream_name,
                    "consumer_group": self.consumer_group
                })
            except Exception as e:
                if "BUSYGROUP" in str(e):
                    logger.info("Redis stream consumer group already exists", extra={
                        "business_event": "redis_consumer_group_exists",
                        "stream_name": self.stream_name,
                        "consumer_group": self.consumer_group
                    })
                else:
                    logger.warning("Consumer group setup issue", extra={
                        "business_event": "redis_consumer_group_warning",
                        "error": str(e)
                    })
            
            logger.info("Redis connection established successfully", extra={
                "business_event": "redis_connection_established",
                "redis_host": self.redis_host,
                "redis_port": self.redis_port,
                "connection_time_ms": round(connection_time_ms, 2),
                "stream_name": self.stream_name,
                "consumer_group": self.consumer_group,
                "consumer_name": self.consumer_name
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
        """Process consolidated traffic record into normalized 3NF database"""
        correlation_id = record_data.get('correlation_id') or str(uuid.uuid4())[:8]
        
        try:
            with CorrelationContext.set_correlation_id(correlation_id):
                # Parse timestamp 
                timestamp_value = record_data.get('timestamp', time.time())
                if isinstance(timestamp_value, str):
                    timestamp_dt = datetime.fromisoformat(timestamp_value.replace('Z', '+00:00'))
                    timestamp = timestamp_dt.timestamp()
                else:
                    timestamp = float(timestamp_value)
                
                # Extract data from nested consolidated record structure
                radar_data = record_data.get('radar_data', {})
                weather_data = record_data.get('weather_data', {})
                camera_data = record_data.get('camera_data', {})
                processing_metadata = record_data.get('processing_metadata', {})
                
                # Use consolidation_id as record ID if available
                record_id = record_data.get('consolidation_id', record_data.get('id', str(uuid.uuid4())))
                
                # ============================================================ 
                # STORE ORIGINAL JSON (SOURCE OF TRUTH)
                # ============================================================
                
                # Store original consolidated JSON for API efficiency
                original_json = json.dumps(record_data, ensure_ascii=False)
                self._store_consolidated_json(record_id, original_json)
                
                # ============================================================ 
                # CREATE NORMALIZED ENTITIES
                # ============================================================
                
                # 1. Core traffic detection
                traffic_detection = TrafficDetection(
                    id=record_id,
                    correlation_id=correlation_id,
                    timestamp=timestamp,
                    trigger_source=record_data.get('trigger_source', 'unknown'),
                    location_id=record_data.get('location_id', 'default'),
                    processing_metadata=processing_metadata
                )
                
                # 2. Radar detection data (if present)
                radar_detection = None
                if radar_data and radar_data.get('speed') is not None:
                    radar_detection = RadarDetection(
                        detection_id=record_id,
                        speed_mph=float(radar_data.get('speed', 0)),
                        speed_mps=float(radar_data.get('speed_mps', 0)),
                        confidence=float(radar_data.get('confidence', 0.0)),
                        alert_level=radar_data.get('alert_level', 'normal'),
                        direction=radar_data.get('direction'),
                        distance=radar_data.get('distance'),
                        detection_source_id=radar_data.get('detection_id')
                    )
                
                # 3. Camera detection data (if present)
                camera_detection = None
                if camera_data and (camera_data.get('vehicle_count', 0) > 0 or camera_data.get('image_path')):
                    vehicle_types = camera_data.get('vehicle_types')
                    if isinstance(vehicle_types, str):
                        try:
                            vehicle_types = json.loads(vehicle_types)
                        except:
                            vehicle_types = [vehicle_types] if vehicle_types else None
                    
                    camera_detection = CameraDetection(
                        detection_id=record_id,
                        vehicle_count=int(camera_data.get('vehicle_count', 0)),
                        vehicle_types=vehicle_types,
                        detection_confidence=camera_data.get('detection_confidence'),
                        image_path=camera_data.get('image_path'),
                        roi_data=camera_data.get('roi_data'),
                        inference_time_ms=camera_data.get('inference_time_ms'),
                        camera_source=camera_data.get('camera_source', 'imx500')
                    )
                
                # 4. Weather condition data (time-bucketed to reduce redundancy)
                weather_conditions = []
                
                # DHT22 sensor data
                dht22_data = weather_data.get('dht22', {})
                if dht22_data and (dht22_data.get('temperature') is not None or dht22_data.get('humidity') is not None):
                    weather_conditions.append(WeatherCondition(
                        timestamp=timestamp,
                        source='dht22',
                        temperature=dht22_data.get('temperature'),
                        humidity=dht22_data.get('humidity'),
                        raw_data=dht22_data
                    ))
                
                # Airport weather data
                airport_weather = weather_data.get('airport_weather', {})
                if airport_weather and airport_weather.get('temperature') is not None:
                    weather_conditions.append(WeatherCondition(
                        timestamp=timestamp,
                        source='airport',
                        temperature=airport_weather.get('temperature'),
                        conditions=airport_weather.get('conditions'),
                        wind_speed=airport_weather.get('wind_speed'),
                        pressure=airport_weather.get('pressure'),
                        visibility=airport_weather.get('visibility'),
                        raw_data=airport_weather
                    ))
                
                # Add normalized entities to batch
                normalized_record = {
                    'traffic_detection': traffic_detection,
                    'radar_detection': radar_detection,
                    'camera_detection': camera_detection, 
                    'weather_conditions': weather_conditions,
                    'correlation_id': correlation_id
                }
                
                self.normalized_batch.append(normalized_record)
                self.stats["records_processed"] += 1
                
                logger.info("Normalized traffic record processed", extra={
                    "business_event": "normalized_record_processed",
                    "correlation_id": correlation_id,
                    "detection_id": record_id,
                    "trigger_source": traffic_detection.trigger_source,
                    "has_radar": radar_detection is not None,
                    "has_camera": camera_detection is not None,
                    "weather_sources": len(weather_conditions),
                    "radar_speed": radar_detection.speed_mph if radar_detection else None,
                    "vehicle_count": camera_detection.vehicle_count if camera_detection else 0,
                    "batch_size": len(self.normalized_batch)
                })
                
                # Check if batch is ready for commit
                current_time = time.time()
                batch_ready = (len(self.normalized_batch) >= self.batch_size or 
                             (current_time - self.last_commit_time) >= self.commit_interval_seconds)
                
                if batch_ready:
                    return self._commit_normalized_batch()
                
                return True
                
        except Exception as e:
            logger.error("Failed to process normalized traffic record", extra={
                "business_event": "normalized_processing_failure",
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
    
    @logger.monitor_performance("normalized_batch_commit")
    def _commit_normalized_batch(self) -> bool:
        """Commit normalized 3NF batch to multiple tables with transaction management"""
        if not self.normalized_batch:
            return True
            
        correlation_id = CorrelationContext.get_correlation_id() or str(uuid.uuid4())[:8]
        batch_size = len(self.normalized_batch)
        
        try:
            with CorrelationContext.set_correlation_id(correlation_id):
                start_time = time.time()
                cursor = self.db_connection.cursor()
                
                # Start transaction for atomicity
                cursor.execute("BEGIN TRANSACTION")
                
                weather_id_cache = {}  # Cache weather IDs to avoid duplicates
                
                for record in self.normalized_batch:
                    traffic_detection = record['traffic_detection']
                    radar_detection = record['radar_detection']
                    camera_detection = record['camera_detection']
                    weather_conditions = record['weather_conditions']
                    
                    # 1. Insert core traffic detection
                    # Debug: Check data types before insert
                    debug_data = {
                        "id_type": type(traffic_detection.id).__name__,
                        "id_value": traffic_detection.id,
                        "correlation_id_type": type(traffic_detection.correlation_id).__name__,
                        "timestamp_type": type(traffic_detection.timestamp).__name__,
                        "timestamp_value": traffic_detection.timestamp,
                        "trigger_source_type": type(traffic_detection.trigger_source).__name__,
                        "location_id_type": type(traffic_detection.location_id).__name__
                    }
                    print(f"DEBUG TRAFFIC DETECTION DATA TYPES: {debug_data}")
                    
                    # Insert traffic detection with auto-increment id and separate consolidation_id
                    cursor.execute("""
                        INSERT OR REPLACE INTO traffic_detections 
                        (consolidation_id, correlation_id, timestamp, trigger_source, location_id, processing_metadata)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        str(traffic_detection.id),  # This is actually the consolidation_id
                        str(traffic_detection.correlation_id),
                        float(traffic_detection.timestamp) if traffic_detection.timestamp else None,
                        str(traffic_detection.trigger_source),
                        str(traffic_detection.location_id) if traffic_detection.location_id else 'default',
                        json.dumps(traffic_detection.processing_metadata) if traffic_detection.processing_metadata else None
                    ))
                    
                    # Get the auto-generated database ID for foreign key relationships
                    db_detection_id = cursor.lastrowid
                    
                    # 2. Insert radar detection (if present)
                    if radar_detection:
                        cursor.execute("""
                            INSERT OR REPLACE INTO radar_detections
                            (detection_id, speed_mph, speed_mps, confidence, alert_level, direction, distance, detection_source_id)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            db_detection_id,  # Use the auto-generated database ID
                            radar_detection.speed_mph,
                            radar_detection.speed_mps,
                            radar_detection.confidence,
                            radar_detection.alert_level,
                            radar_detection.direction,
                            radar_detection.distance,
                            radar_detection.detection_source_id
                        ))
                    
                    # 3. Insert camera detection (if present)
                    if camera_detection:
                        cursor.execute("""
                            INSERT OR REPLACE INTO camera_detections
                            (detection_id, vehicle_count, vehicle_types, detection_confidence, 
                             processing_time, image_metadata)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            db_detection_id,  # Use the auto-generated database ID
                            camera_detection.vehicle_count,
                            json.dumps(camera_detection.vehicle_types) if camera_detection.vehicle_types else None,
                            camera_detection.detection_confidence,
                            camera_detection.inference_time_ms if hasattr(camera_detection, 'inference_time_ms') else None,
                            json.dumps({
                                'image_path': getattr(camera_detection, 'image_path', None),
                                'roi_data': getattr(camera_detection, 'roi_data', None),
                                'camera_source': getattr(camera_detection, 'camera_source', None)
                            })
                        ))
                    
                    # 4. Insert weather conditions (time-bucketed to reduce redundancy)
                    for weather_condition in weather_conditions:
                        # Check if we already have weather data for this time bucket (5-minute intervals)
                        time_bucket = int(weather_condition.timestamp // 300) * 300  # 5-minute buckets
                        cache_key = f"{weather_condition.source}_{time_bucket}"
                        
                        if cache_key not in weather_id_cache:
                            # Check if weather record exists in this time bucket
                            cursor.execute("""
                                SELECT id FROM weather_conditions 
                                WHERE weather_source = ? AND timestamp BETWEEN ? AND ?
                                ORDER BY timestamp DESC LIMIT 1
                            """, (weather_condition.weather_source if hasattr(weather_condition, 'weather_source') else 'dht22', time_bucket, time_bucket + 300))
                            
                            existing_weather = cursor.fetchone()
                            
                            if existing_weather:
                                weather_id_cache[cache_key] = existing_weather[0]
                            else:
                                # Insert new weather condition
                                cursor.execute("""
                                    INSERT INTO weather_conditions
                                    (timestamp, temperature, humidity, pressure, weather_source)
                                    VALUES (?, ?, ?, ?, ?)
                                """, (
                                    weather_condition.timestamp,
                                    weather_condition.temperature,
                                    weather_condition.humidity,
                                    weather_condition.pressure if hasattr(weather_condition, 'pressure') else None,
                                    weather_condition.weather_source if hasattr(weather_condition, 'weather_source') else 'dht22'
                                ))
                                weather_id_cache[cache_key] = cursor.lastrowid
                        
                        # 5. Create traffic-weather correlation
                        cursor.execute("""
                            INSERT OR IGNORE INTO traffic_weather_correlation
                            (traffic_detection_id, weather_condition_id, correlation_strength)
                            VALUES (?, ?, ?)
                        """, (
                            db_detection_id,  # Use the auto-generated database ID
                            weather_id_cache[cache_key],
                            1.0  # Full correlation for concurrent readings
                        ))
                
                # Commit transaction
                cursor.execute("COMMIT")
                cursor.close()
                
                # Update statistics
                commit_time_ms = (time.time() - start_time) * 1000
                self.stats["records_stored"] += batch_size
                self.last_commit_time = time.time()
                self.stats["last_record_time"] = datetime.now().isoformat()
                
                # Track processing times
                self.processing_times.append(commit_time_ms)
                if len(self.processing_times) > 100:
                    self.processing_times.pop(0)
                self.stats["avg_processing_time_ms"] = sum(self.processing_times) / len(self.processing_times)
                
                logger.info("Normalized batch committed to 3NF database", extra={
                    "business_event": "normalized_batch_commit_success",
                    "correlation_id": correlation_id,
                    "batch_size": batch_size,
                    "commit_time_ms": round(commit_time_ms, 2),
                    "total_records_stored": self.stats["records_stored"],
                    "weather_buckets_cached": len(weather_id_cache),
                    "schema_type": "3NF_normalized"
                })
                
                # Clear batch
                self.normalized_batch.clear()
                return True
                
        except Exception as e:
            # Rollback transaction on error
            try:
                cursor.execute("ROLLBACK")
                cursor.close()
            except:
                pass
                
            # Enhanced error logging with full exception details
            import traceback
            error_details = {
                "business_event": "normalized_batch_commit_failure", 
                "correlation_id": correlation_id,
                "batch_size": batch_size,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "full_traceback": traceback.format_exc()
            }
            
            logger.error("Failed to commit normalized batch to database", extra=error_details)
            
            # Also log to console for debugging
            print(f"DATABASE COMMIT ERROR: {type(e).__name__}: {str(e)}")
            print(f"Full traceback: {traceback.format_exc()}")
            print(f"Batch size: {batch_size}, Correlation ID: {correlation_id}")
            self.stats["database_errors"] += 1
            # Don't clear batch on error - will retry
            return False
    
    def _store_consolidated_json(self, consolidation_id: str, event_json: str):
        """Store original consolidated JSON for API efficiency"""
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO consolidated_events 
                (consolidation_id, event_json)
                VALUES (?, ?)
            """, (consolidation_id, event_json))
            
            logger.debug("Stored consolidated JSON", extra={
                "business_event": "consolidated_json_stored",
                "consolidation_id": consolidation_id,
                "json_size_bytes": len(event_json)
            })
            
        except Exception as e:
            logger.error("Failed to store consolidated JSON", extra={
                "business_event": "consolidated_json_storage_failed",
                "consolidation_id": consolidation_id,
                "error": str(e)
            })
    
    def _get_database_stats(self) -> Dict[str, Any]:
        """Get comprehensive database statistics for normalized 3NF schema"""
        try:
            cursor = self.db_connection.cursor()
            
            # Check if we have normalized tables, fallback to legacy if needed
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='traffic_detections'")
            has_normalized_schema = cursor.fetchone() is not None
            
            if has_normalized_schema:
                # Get normalized schema stats
                cursor.execute("SELECT COUNT(*) FROM traffic_detections")
                total_detections = cursor.fetchone()[0] or 0
                
                cursor.execute("SELECT COUNT(*) FROM radar_detections")
                total_radar = cursor.fetchone()[0] or 0
                
                cursor.execute("SELECT COUNT(*) FROM camera_detections")
                total_camera = cursor.fetchone()[0] or 0
                
                cursor.execute("SELECT COUNT(*) FROM weather_conditions")
                total_weather = cursor.fetchone()[0] or 0
                
                # Get recent activity (last 24 hours)
                current_time = time.time()
                yesterday = current_time - (24 * 60 * 60)
                cursor.execute("""
                    SELECT COUNT(*) FROM traffic_detections 
                    WHERE timestamp > ?
                """, (yesterday,))
                recent_records = cursor.fetchone()[0] or 0
                
                stats = {
                    "total_detections": total_detections,
                    "total_records": total_detections,  # Add this for backward compatibility
                    "total_radar_records": total_radar,
                    "total_camera_records": total_camera,
                    "total_weather_records": total_weather,
                    "recent_24h_records": recent_records,
                    "schema_type": "3NF_normalized"
                }
                self.stats["total_records"] = total_detections
                
            else:
                # Fallback to legacy schema stats
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='traffic_records'")
                if cursor.fetchone():
                    cursor.execute("SELECT COUNT(*) FROM traffic_records")
                    total_records = cursor.fetchone()[0] or 0
                    
                    cursor.execute("""
                        SELECT COUNT(*) FROM traffic_records 
                        WHERE datetime(timestamp) > datetime('now', '-24 hours')
                    """)
                    recent_records = cursor.fetchone()[0] or 0
                    
                    stats = {
                        "total_records": total_records,
                        "recent_24h_records": recent_records,
                        "schema_type": "legacy_denormalized"
                    }
                    self.stats["total_records"] = total_records
                else:
                    stats = {
                        "total_records": 0,
                        "recent_24h_records": 0,
                        "schema_type": "no_tables"
                    }
                    self.stats["total_records"] = 0
            
            # Get database size
            db_size_bytes = 0
            if self.database_path.exists():
                db_size_bytes = self.database_path.stat().st_size
            
            stats["size_mb"] = round(db_size_bytes / (1024 * 1024), 2)
            self.stats["database_size_mb"] = stats["size_mb"]
            
            cursor.close()
            
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
        """Background thread to consume Redis stream messages with correlation tracking"""
        logger.info("Starting Redis message consumer", extra={
            "business_event": "redis_consumer_start",
            "stream_name": self.stream_name,
            "consumer_group": self.consumer_group,
            "consumer_name": self.consumer_name
        })
        
        try:
            while self.running:
                try:
                    # Read messages from stream using consumer group (FIFO)
                    messages = self.redis_client.xreadgroup(
                        self.consumer_group,
                        self.consumer_name,
                        {self.stream_name: '>'},
                        count=5,  # Process up to 5 messages at a time
                        block=1000  # Block for 1 second if no messages
                    )
                    
                    for stream_name, stream_messages in messages:
                        for message_id, fields in stream_messages:
                            try:
                                # Parse consolidated data from stream
                                consolidated_data_str = fields.get('data', '{}')
                                consolidated_data = json.loads(consolidated_data_str)
                                
                                # Extract correlation_id for tracking
                                correlation_id = fields.get('correlation_id') or consolidated_data.get('correlation_id')
                                
                                # Process the consolidated record
                                success = self.process_traffic_record(consolidated_data)
                                
                                if success:
                                    # Acknowledge message processing (removes from pending)
                                    self.redis_client.xack(self.stream_name, self.consumer_group, message_id)
                                    
                                    # Delete processed message from stream
                                    self.redis_client.xdel(self.stream_name, message_id)
                                    
                                    logger.debug("Processed and removed stream message", extra={
                                        "business_event": "stream_message_processed",
                                        "message_id": message_id,
                                        "correlation_id": correlation_id
                                    })
                                else:
                                    logger.warning("Failed to process stream message", extra={
                                        "business_event": "stream_message_processing_failure",
                                        "message_id": message_id,
                                        "correlation_id": correlation_id
                                    })
                                
                            except json.JSONDecodeError as e:
                                logger.error("Invalid JSON in stream message", extra={
                                    "business_event": "stream_message_parse_failure",
                                    "error": str(e),
                                    "message_id": message_id,
                                    "message_data": str(fields)[:200]  # First 200 chars
                                })
                                self.stats["redis_errors"] += 1
                                # Acknowledge bad message to prevent reprocessing
                                self.redis_client.xack(self.stream_name, self.consumer_group, message_id)
                                self.redis_client.xdel(self.stream_name, message_id)
                                
                            except Exception as e:
                                logger.error("Error processing stream message", extra={
                                    "business_event": "stream_message_processing_failure",
                                    "error": str(e),
                                    "message_id": message_id
                                })
                                self.stats["redis_errors"] += 1
                                
                except Exception as e:
                    logger.error("Error reading from Redis stream", extra={
                        "business_event": "redis_stream_read_error",
                        "error": str(e)
                    })
                    time.sleep(1)  # Brief pause before retry
                        
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