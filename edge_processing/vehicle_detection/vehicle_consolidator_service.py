#!/usr/bin/env python3
"""
Enhanced Vehicle Detection Data Consolidator Service with Centralized Logging
Consumes vehicle detection results from IMX500 host service and aggregates data with correlation tracking

This service replaces the software-based vehicle detection with a data consolidation
approach that leverages the IMX500's on-chip AI processing done by the host service.

Architecture:
IMX500 Host Service (AI Processing) -> Redis -> This Service (Data Aggregation) -> Database

Enhanced Features:
- Centralized logging with correlation tracking
- Performance monitoring of data consolidation
- Structured error handling and business events
- Correlation ID propagation from radar events
- Comprehensive event tracing across detection pipeline
"""

import time
import json
import threading
import uuid
import os
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, List, Optional, Any

# Import centralized logging infrastructure
from edge_processing.shared_logging import ServiceLogger, CorrelationContext, performance_monitor

# Redis for consuming IMX500 AI results
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

# Import our Redis data models
RedisDataManager = None
VehicleDetection = None
VehicleType = None
RedisKeys = None

try:
    from redis_models import (
        VehicleDetection, VehicleType, 
        RedisDataManager, RedisKeys
    )
except ImportError:
    try:
        from edge_processing.redis_models import (
            VehicleDetection, VehicleType, 
            RedisDataManager, RedisKeys
        )
    except ImportError:
        RedisDataManager = None

# Vehicle Grouping Configuration
VEHICLE_GROUPING_WINDOW = 3.0      # seconds - time window to group detections as same vehicle
SPEED_VARIATION_THRESHOLD = 5.0    # mph - max speed difference for same vehicle grouping
DIRECTION_CONSISTENCY_THRESHOLD = 0.8  # ratio for consistent direction (approaching/departing)
GROUP_CLEANUP_INTERVAL = 30.0      # seconds - how often to cleanup expired groups
MAX_VEHICLE_GROUPS = 100           # maximum number of active vehicle groups to track

class VehicleDetectionConsolidatorEnhanced:
    """
    Enhanced Vehicle Detection Consolidator with centralized logging and correlation tracking
    Focuses on data aggregation, statistics, and persistence with full event tracing
    """
    
    def __init__(self,
                 redis_host: str = "redis",
                 redis_port: int = 6379,
                 data_retention_hours: int = 24,
                 stats_update_interval: int = 60):
        
        # Initialize centralized logger
        self.logger = ServiceLogger(
            service_name="vehicle-consolidator",
            service_version="2.1.0",
            environment=os.environ.get('ENVIRONMENT', 'production')
        )
        
        if not REDIS_AVAILABLE:
            self.logger.log_error(
                error_type="missing_dependency",
                message="Redis required for vehicle detection data consolidation",
                error=str(RuntimeError("Redis not available"))
            )
            raise RuntimeError("Redis required for vehicle detection data consolidation")
        
        # Verify Redis models are available
        if RedisDataManager is None:
            self.logger.log_error(
                error_type="missing_redis_models",
                message="RedisDataManager not available - consolidator cannot start",
                error=str(RuntimeError("Redis models not available"))
            )
            raise RuntimeError("Redis models not available")
        
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.data_retention_hours = data_retention_hours
        self.stats_update_interval = stats_update_interval
        
        # Redis connection
        self.redis_client = None
        self.data_manager = None
        
        # Stream consumption configuration
        self.radar_stream = "traffic:radar"
        self.consumer_group = "consolidator-group"
        self.consumer_name = f"consolidator-{uuid.uuid4().hex[:8]}"
        
        # Camera integration configuration
        self.camera_channel = "camera_detections"
        self.camera_pubsub = None
        self.recent_camera_detections = deque(maxlen=100)  # Last 100 camera detections
        self.camera_correlation_window = 10.0  # seconds - time window to correlate radar and camera events
        
        # Service state
        self.running = False
        self.stats_thread = None
        self.cleanup_thread = None
        self.camera_thread = None
        
        # Statistics tracking
        self.hourly_stats = defaultdict(lambda: {
            'total_vehicles': 0,
            'vehicle_types': defaultdict(int),
            'avg_confidence': 0.0,
            'detection_count': 0
        })
        
        self.recent_detections = deque(maxlen=1000)  # Last 1000 detections
        
        # Vehicle Grouping for Multi-Detection Filtering
        self.recent_vehicle_groups = deque(maxlen=MAX_VEHICLE_GROUPS)  # Active vehicle groups
        self.last_group_cleanup = time.time()  # Track cleanup timing
        self.grouped_vehicles_count = 0  # Statistics tracking
        self.single_detections_count = 0
        
        # Performance tracking
        self.processing_times = []
        self.event_count = 0
        self.startup_time = None
        
        self.logger.log_service_event(
            event_type="consolidator_initialized",
            message="Vehicle Detection Consolidator initialized with centralized logging",
            details={
                "redis_host": redis_host,
                "redis_port": redis_port,
                "data_retention_hours": data_retention_hours,
                "stats_update_interval": stats_update_interval
            }
        )
    
    def connect_redis(self) -> bool:
        """Connect to Redis with enhanced error handling and logging"""
        
        with CorrelationContext.create("redis_connection") as ctx:
            self.logger.log_service_event(
                event_type="redis_connection_attempt",
                message=f"Attempting Redis connection to {self.redis_host}:{self.redis_port}"
            )
            
            try:
                with performance_monitor("redis_connection_setup"):
                    self.redis_client = redis.Redis(
                        host=self.redis_host,
                        port=self.redis_port,
                        decode_responses=True,
                        socket_connect_timeout=5,
                        socket_timeout=5
                    )
                    
                    # Test connection
                    self.redis_client.ping()
                    
                    # Initialize data manager
                    self.data_manager = RedisDataManager(self.redis_client)
                    
                    # Setup Redis stream consumer group for radar data
                    self._setup_stream_consumer_group()
                    
                    # Setup camera detections subscription
                    self._setup_camera_subscription()
                
                self.logger.log_service_event(
                    event_type="redis_connection_success",
                    message=f"✅ Connected to Redis successfully at {self.redis_host}:{self.redis_port}",
                    details={"redis_host": self.redis_host, "redis_port": self.redis_port}
                )
                return True
                
            except Exception as e:
                self.logger.log_error(
                    error_type="redis_connection_failed",
                    message=f"Failed to connect to Redis: {str(e)}",
                    error=str(e),
                    details={
                        "redis_host": self.redis_host,
                        "redis_port": self.redis_port
                    }
                )
                return False
    
    def _setup_stream_consumer_group(self):
        """Setup Redis stream consumer group for reliable FIFO consumption"""
        try:
            # Create consumer group if it doesn't exist
            try:
                self.redis_client.xgroup_create(
                    self.radar_stream, 
                    self.consumer_group, 
                    id='0', 
                    mkstream=True
                )
                self.logger.log_service_event(
                    event_type="consumer_group_created",
                    message=f"✅ Created consumer group '{self.consumer_group}' for stream '{self.radar_stream}'"
                )
            except redis.exceptions.ResponseError as e:
                if "BUSYGROUP" in str(e):
                    self.logger.log_service_event(
                        event_type="consumer_group_exists",
                        message=f"Consumer group '{self.consumer_group}' already exists"
                    )
                else:
                    raise e
                    
        except Exception as e:
            self.logger.log_error(
                error_type="consumer_group_setup_failed",
                message=f"Failed to setup consumer group: {str(e)}",
                error=str(e)
            )
            raise e
    
    def _setup_camera_subscription(self):
        """Setup camera detections Redis pub/sub subscription"""
        try:
            self.camera_pubsub = self.redis_client.pubsub()
            self.camera_pubsub.subscribe(self.camera_channel)
            
            self.logger.log_service_event(
                event_type="camera_subscription_created",
                message=f"✅ Subscribed to camera detections channel '{self.camera_channel}'"
            )
            
        except Exception as e:
            self.logger.log_error(
                error_type="camera_subscription_setup_failed",
                message=f"Failed to setup camera subscription: {str(e)}",
                error=str(e)
            )
            raise e
    
    def start(self) -> bool:
        """Start the consolidation service with full correlation tracking"""
        
        with CorrelationContext.create("consolidator_startup") as ctx:
            self.logger.log_service_event(
                event_type="service_startup_initiated",
                message="🚗 Starting Enhanced Vehicle Detection Consolidator with correlation tracking"
            )
            
            if not self.connect_redis():
                self.logger.log_error(
                    error_type="startup_failed",
                    message="Cannot start consolidator without Redis connection",
                    error=str(RuntimeError("Redis connection failed"))
                )
                return False
            
            self.running = True
            self.startup_time = time.time()
            
            # Start background threads with error handling
            try:
                self.stats_thread = threading.Thread(target=self._stats_update_loop_enhanced, daemon=True)
                self.cleanup_thread = threading.Thread(target=self._cleanup_loop_enhanced, daemon=True)
                self.camera_thread = threading.Thread(target=self._camera_processing_loop, daemon=True)
                
                self.stats_thread.start()
                self.cleanup_thread.start()
                self.camera_thread.start()
                
                self.logger.log_service_event(
                    event_type="background_threads_started",
                    message="Background processing threads started successfully",
                    details={
                        "stats_thread_id": self.stats_thread.ident,
                        "cleanup_thread_id": self.cleanup_thread.ident,
                        "camera_thread_id": self.camera_thread.ident
                    }
                )
                
                # Main stream processing loop
                self._process_radar_stream_enhanced()
                
            except KeyboardInterrupt:
                self.logger.log_service_event(
                    event_type="shutdown_requested",
                    message="Shutdown requested by user (Ctrl+C)"
                )
            except Exception as e:
                self.logger.log_error(
                    error_type="service_runtime_error",
                    message="Consolidator service encountered runtime error",
                    error=str(e)
                )
            finally:
                self.stop()
            
            return True
    
    def _process_radar_stream_enhanced(self):
        """Enhanced radar stream processing with FIFO consumption and correlation tracking"""
        
        with CorrelationContext.create("stream_processing_session") as ctx:
            self.logger.log_service_event(
                event_type="stream_processing_started",
                message=f"🎯 Starting radar stream consumption from '{self.radar_stream}' using consumer group '{self.consumer_group}'"
            )
            
            events_processed = 0
            last_stats_log = time.time()
            
            while self.running:
                try:
                    processing_start = time.time()
                    
                    # Read from radar stream using consumer group (FIFO with acknowledgment)
                    messages = self.redis_client.xreadgroup(
                        self.consumer_group,
                        self.consumer_name,
                        {self.radar_stream: '>'},  # Read only new messages
                        count=10,  # Process up to 10 messages at once
                        block=1000  # Block for 1 second if no messages
                    )
                    
                    if messages:
                        for stream_name, stream_messages in messages:
                            for message_id, fields in stream_messages:
                                try:
                                    # Process radar data and create consolidated event
                                    self._process_radar_data_enhanced(message_id, fields)
                                    
                                    # Acknowledge successful processing (removes from stream)
                                    self.redis_client.xack(self.radar_stream, self.consumer_group, message_id)
                                    
                                    events_processed += 1
                                    self.event_count += 1
                                    
                                except Exception as e:
                                    self.logger.log_error(
                                        error_type="radar_data_processing_error",
                                        message=f"Error processing radar message {message_id}: {str(e)}",
                                        error=str(e),
                                        details={"message_id": message_id, "fields": fields}
                                    )
                                    # Still acknowledge to prevent reprocessing
                                    self.redis_client.xack(self.radar_stream, self.consumer_group, message_id)
                    
                    # Log periodic statistics (every 5 minutes)
                    if time.time() - last_stats_log > 300:
                        self._log_processing_stats(events_processed, ctx)
                        last_stats_log = time.time()
                        events_processed = 0
                    
                    # Track processing performance
                    processing_time = time.time() - processing_start
                    self.processing_times.append(processing_time)
                    
                    # Keep only last 1000 processing times
                    if len(self.processing_times) > 1000:
                        self.processing_times = self.processing_times[-1000:]
                    
                except Exception as e:
                    self.logger.log_error(
                        message=f"Error in radar stream processing loop: {str(e)}",
                        error=str(e),
                        error_type="stream_processing_error",
                        details={"events_processed": events_processed}
                    )
                    time.sleep(1)
            
            self.logger.log_service_event(
                event_type="stream_processing_stopped",
                message="Radar stream processing stopped",
                details={"total_events_processed": events_processed}
            )
    
    def _cleanup_expired_vehicle_groups(self):
        """Remove expired vehicle groups to prevent memory leaks"""
        current_time = time.time()
        
        if current_time - self.last_group_cleanup < GROUP_CLEANUP_INTERVAL:
            return  # Don't cleanup too frequently
        
        initial_count = len(self.recent_vehicle_groups)
        
        # Remove groups older than the grouping window + buffer
        cutoff_time = current_time - (VEHICLE_GROUPING_WINDOW * 2)
        
        self.recent_vehicle_groups = deque([
            group for group in self.recent_vehicle_groups 
            if group['latest_timestamp'] > cutoff_time
        ], maxlen=MAX_VEHICLE_GROUPS)
        
        cleaned_count = initial_count - len(self.recent_vehicle_groups)
        
        if cleaned_count > 0:
            self.logger.debug(
                f"Cleaned up {cleaned_count} expired vehicle groups",
                details={
                    "initial_groups": initial_count,
                    "remaining_groups": len(self.recent_vehicle_groups),
                    "cutoff_age_seconds": VEHICLE_GROUPING_WINDOW * 2
                }
            )
        
        self.last_group_cleanup = current_time
    
    def _group_vehicle_detections(self, detection_data: Dict[str, Any]) -> Optional[str]:
        """
        Group radar detections that likely represent the same vehicle
        
        Returns:
            str: Existing group_id if this detection should be grouped with previous detections
            None: If this represents a new vehicle (create new consolidated record)
        """
        current_time = detection_data['timestamp']
        speed_mph = abs(detection_data['radar_data']['speed'])  # Use absolute speed for comparison
        speed_mps = detection_data['radar_data']['speed_mps']  # Keep sign for direction analysis
        
        # Cleanup expired groups periodically
        self._cleanup_expired_vehicle_groups()
        
        # Check recent vehicle groups for potential matching
        for existing_group in self.recent_vehicle_groups:
            time_diff = current_time - existing_group['latest_timestamp']
            speed_diff = abs(speed_mph - abs(existing_group['latest_speed_mph']))
            
            # Direction consistency check (both negative = approaching, both positive = departing)
            same_direction = (speed_mps * existing_group['latest_speed_mps']) > 0
            
            # Group if within time window, similar speed, and same direction
            if (time_diff <= VEHICLE_GROUPING_WINDOW and 
                speed_diff <= SPEED_VARIATION_THRESHOLD and 
                same_direction):
                
                # Same vehicle detected again - update existing group
                existing_group['detections'].append(detection_data)
                existing_group['latest_timestamp'] = current_time
                existing_group['latest_speed_mph'] = speed_mph
                existing_group['latest_speed_mps'] = speed_mps
                existing_group['detection_count'] += 1
                
                # Update speed trend analysis
                speeds = [abs(d['radar_data']['speed']) for d in existing_group['detections']]
                existing_group['speed_trend'] = 'decreasing' if speeds[-1] < speeds[0] else 'increasing' if speeds[-1] > speeds[0] else 'steady'
                
                self.grouped_vehicles_count += 1
                
                self.logger.debug(
                    f"🔗 Grouped detection with existing vehicle group {existing_group['group_id']}",
                    details={
                        "group_id": existing_group['group_id'],
                        "detection_count": existing_group['detection_count'],
                        "time_diff_ms": time_diff * 1000,
                        "speed_diff_mph": speed_diff,
                        "speed_trend": existing_group['speed_trend'],
                        "same_direction": same_direction
                    }
                )
                
                return existing_group['group_id']  # Return existing group ID to skip creating new record
        
        # No matching group found - this is a new vehicle
        group_id = f"vehicle_{int(current_time)}_{uuid.uuid4().hex[:4]}"
        
        new_group = {
            'group_id': group_id,
            'detections': [detection_data],
            'latest_timestamp': current_time,
            'latest_speed_mph': speed_mph,
            'latest_speed_mps': speed_mps,
            'created_at': current_time,
            'detection_count': 1,
            'speed_trend': 'initial'
        }
        
        self.recent_vehicle_groups.append(new_group)
        self.single_detections_count += 1
        
        self.logger.debug(
            f"🚗 Created new vehicle group {group_id}",
            details={
                "group_id": group_id,
                "speed_mph": speed_mph,
                "direction": "approaching" if speed_mps < 0 else "departing",
                "total_active_groups": len(self.recent_vehicle_groups)
            }
        )
        
        return None  # New vehicle - proceed with creating consolidated record
    
    def _camera_processing_loop(self):
        """Process camera detections from Redis pub/sub"""
        
        with CorrelationContext.create("camera_processing_session") as ctx:
            self.logger.log_service_event(
                event_type="camera_processing_started",
                message=f"🎥 Starting camera detections processing from channel '{self.camera_channel}'"
            )
            
            camera_events_processed = 0
            
            try:
                while self.running:
                    try:
                        # Get message from camera subscription
                        message = self.camera_pubsub.get_message(timeout=1.0)
                        
                        if message and message['type'] == 'message':
                            # Parse camera detection data
                            camera_data = json.loads(message['data'])
                            
                            # Add to recent detections cache with timestamp
                            camera_entry = {
                                'timestamp': time.time(),
                                'detection_timestamp': camera_data.get('timestamp'),
                                'data': camera_data
                            }
                            
                            self.recent_camera_detections.append(camera_entry)
                            camera_events_processed += 1
                            
                            self.logger.debug(
                                "🎥 Camera detection cached",
                                details={
                                    "image_id": camera_data.get('image_id'),
                                    "vehicle_count": camera_data.get('ai_results', {}).get('detection_count', 0),
                                    "image_path": camera_data.get('image_path'),
                                    "cache_size": len(self.recent_camera_detections)
                                }
                            )
                            
                    except json.JSONDecodeError as e:
                        self.logger.log_error(
                            error_type="camera_data_parse_error",
                            message=f"Failed to parse camera data: {str(e)}",
                            error=str(e)
                        )
                    except Exception as e:
                        self.logger.log_error(
                            error_type="camera_processing_error",
                            message=f"Error processing camera message: {str(e)}",
                            error=str(e)
                        )
                        time.sleep(0.1)
                        
            except Exception as e:
                self.logger.log_error(
                    error_type="camera_processing_loop_error",
                    message=f"Camera processing loop failed: {str(e)}",
                    error=str(e)
                )
            
            self.logger.log_service_event(
                event_type="camera_processing_stopped",
                message="Camera processing stopped",
                details={"total_camera_events_processed": camera_events_processed}
            )
    
    def _find_matching_camera_data(self, radar_timestamp: float, correlation_id: str) -> Optional[Dict[str, Any]]:
        """Find camera detection that matches radar detection by timestamp"""
        
        best_match = None
        min_time_diff = float('inf')
        
        for camera_entry in reversed(self.recent_camera_detections):  # Check most recent first
            camera_timestamp = camera_entry['timestamp']
            time_diff = abs(radar_timestamp - camera_timestamp)
            
            # Check if within correlation window
            if time_diff <= self.camera_correlation_window and time_diff < min_time_diff:
                camera_data = camera_entry['data']
                ai_results = camera_data.get('ai_results', {})
                
                # Only match if camera detected vehicles
                if ai_results.get('detection_count', 0) > 0:
                    best_match = camera_data
                    min_time_diff = time_diff
        
        if best_match:
            self.logger.debug(
                "🎯 Matched radar detection with camera data",
                details={
                    "correlation_id": correlation_id,
                    "time_difference_seconds": min_time_diff,
                    "camera_image_id": best_match.get('image_id'),
                    "camera_vehicle_count": best_match.get('ai_results', {}).get('detection_count', 0)
                }
            )
        
        return best_match
    
    def _get_correlated_camera_data(self, radar_timestamp: float, correlation_id: str) -> Dict[str, Any]:
        """Get camera data correlated with radar detection, or fallback data"""
        
        # Try to find matching camera detection
        matched_camera = self._find_matching_camera_data(radar_timestamp, correlation_id)
        
        if matched_camera:
            # Extract camera data from IMX500 detection
            ai_results = matched_camera.get('ai_results', {})
            detections = ai_results.get('detections', [])
            
            # Extract vehicle types from detections
            vehicle_types = []
            max_confidence = 0.0
            
            for detection in detections:
                if detection.get('class_name'):
                    vehicle_types.append(detection['class_name'])
                confidence = detection.get('confidence', 0.0)
                if confidence > max_confidence:
                    max_confidence = confidence
            
            return {
                "vehicle_count": ai_results.get('detection_count', 0),
                "detection_confidence": max_confidence if max_confidence > 0 else None,
                "vehicle_types": list(set(vehicle_types)) if vehicle_types else None,  # Remove duplicates
                "image_path": matched_camera.get('image_path'),
                "image_id": matched_camera.get('image_id'),
                "inference_time_ms": ai_results.get('inference_time_ms'),
                "recent_summary": {"count": ai_results.get('detection_count', 0)},
                "correlation_time_diff": abs(radar_timestamp - matched_camera.get('timestamp', 0))
            }
        else:
            # Fallback to radar-based estimation
            return {
                "vehicle_count": 1,  # Radar detected something
                "detection_confidence": None,
                "vehicle_types": None,
                "image_path": None,
                "image_id": None,
                "inference_time_ms": None,
                "recent_summary": {"count": 1},
                "correlation_time_diff": None,
                "fallback_reason": "no_camera_correlation"
            }
    
    def _get_consolidation_sources(self, consolidated_data: Dict[str, Any]) -> List[str]:
        """Determine data sources used in consolidation"""
        sources = ["radar"]
        
        camera_data = consolidated_data.get('camera_data', {})
        if camera_data.get('image_path') and camera_data.get('correlation_time_diff') is not None:
            sources.append("camera")
        
        weather_data = consolidated_data.get('weather_data', {})
        if weather_data:
            sources.append("weather")
        
        return sources
    
    def _get_consolidation_method(self, consolidated_data: Dict[str, Any]) -> str:
        """Determine consolidation method used"""
        sources = self._get_consolidation_sources(consolidated_data)
        
        if len(sources) == 1:
            return "radar_only"
        elif "camera" in sources:
            return "radar_camera_correlated"
        else:
            return "radar_weather_only"
    
    def _process_radar_data_enhanced(self, message_id: str, fields: Dict[str, Any]):
        """Process radar stream data and create consolidated traffic event"""
        
        try:
            # Extract radar data from stream fields
            speed = float(fields.get('speed', 0))
            speed_mps = float(fields.get('speed_mps', 0))
            correlation_id = fields.get('correlation_id', str(uuid.uuid4())[:8])
            detection_id = fields.get('detection_id', correlation_id)
            alert_level = fields.get('alert_level', 'normal')
            timestamp = float(fields.get('_timestamp', time.time()))
            
            with CorrelationContext.create(correlation_id) as ctx:
                # Log radar detection business event
                self.logger.log_business_event(
                    event_name="radar_detection_processed",
                    event_data={
                        "business_context": "traffic_monitoring",
                        "message": f"🎯 Radar detected vehicle at {speed:.1f} mph ({speed_mps:.1f} m/s)",
                        "correlation_id": correlation_id,
                        "detection_id": detection_id,
                        "speed_mph": speed,
                        "speed_mps": speed_mps,
                        "alert_level": alert_level,
                        "message_id": message_id,
                        "source": "radar_stream"
                    }
                )
                
                # Create consolidated event data
                consolidated_data = {
                    "consolidation_id": f"consolidated_{detection_id}_{int(timestamp)}",
                    "correlation_id": correlation_id,
                    "timestamp": timestamp,
                    "trigger_source": "radar",
                    
                    # Radar data
                    "radar_data": {
                        "speed": speed,
                        "speed_mps": speed_mps,
                        "alert_level": alert_level,
                        "detection_id": detection_id,
                        "confidence": 0.85,  # Radar generally reliable
                        "direction": "approaching" if speed < 0 else "receding"  # Negative = approaching sensor
                    },
                    
                    # Weather data (fetch current conditions)
                    "weather_data": self._get_current_weather_data(),
                    
                    # Camera data (correlate with IMX500 detections)
                    "camera_data": self._get_correlated_camera_data(timestamp, correlation_id),
                    
                    # Processing metadata  
                    "processing_metadata": {
                        "processor_version": "consolidator_v2.1.0",
                        "processing_time": datetime.now().isoformat(),
                        "data_sources": self._get_consolidation_sources(consolidated_data),
                        "consolidation_method": self._get_consolidation_method(consolidated_data)
                    }
                }
                
                # Check if this detection should be grouped with recent detections (same vehicle)
                existing_group_id = self._group_vehicle_detections(consolidated_data)
                
                if existing_group_id is not None:
                    # This is likely the same vehicle detected multiple times - skip storing duplicate
                    self.logger.log_business_event(
                        event_name="vehicle_detection_grouped",
                        event_data={
                            "business_context": "traffic_monitoring",
                            "message": f"🔗 Grouped duplicate detection with existing vehicle {existing_group_id}",
                            "correlation_id": correlation_id,
                            "detection_id": detection_id,
                            "existing_group_id": existing_group_id,
                            "speed_mph": speed,
                            "alert_level": alert_level,
                            "action": "skip_database_storage"
                        }
                    )
                    return  # Skip storing this detection - it's a duplicate of same vehicle
                
                # New vehicle - store consolidated data for database persistence
                self._store_consolidated_data(consolidated_data)
                
                # Update statistics
                self._update_radar_statistics(speed, alert_level)
                
        except Exception as e:
            self.logger.log_error(
                error_type="radar_data_processing_failed",
                message=f"Failed to process radar data: {str(e)}",
                error=str(e),
                details={"message_id": message_id, "fields": fields}
            )
            raise e
    
    # Legacy pub/sub message handling removed - now using stream consumption
    
    def _process_imx500_capture_event_enhanced(self, event_data: Dict[str, Any], correlation_id: str):
        """Enhanced IMX500 capture event processing with correlation tracking"""
        
        try:
            vehicle_count = event_data.get('vehicle_detections', 0)
            primary_vehicle = event_data.get('primary_vehicle')
            inference_time = event_data.get('inference_time_ms', 0)
            image_id = event_data.get('image_id')
            confidence_score = event_data.get('confidence_score', 0.0)
            
            if vehicle_count > 0:
                # Log business event with correlation
                self.logger.log_business_event(
                    event_name="imx500_vehicle_detected",
                    event_data={
                        "business_context": "traffic_monitoring",
                        "message": f"🚗 IMX500 AI detected {vehicle_count} vehicles (primary: {primary_vehicle})",
                        "correlation_id": correlation_id,
                        "vehicle_count": vehicle_count,
                        "primary_vehicle": primary_vehicle,
                        "inference_time_ms": inference_time,
                        "confidence_score": confidence_score,
                        "image_id": image_id,
                        "ai_processor": "imx500_on_chip"
                    }
                )
                
                # Log performance metrics
                self.logger.debug(
                    f"IMX500 AI inference completed in {inference_time:.1f}ms (confidence: {confidence_score:.2f})"
                )
                
                # Add to recent detections for real-time stats
                detection_summary = {
                    'timestamp': time.time(),
                    'correlation_id': correlation_id,
                    'vehicle_count': vehicle_count,
                    'primary_vehicle': primary_vehicle,
                    'inference_time_ms': inference_time,
                    'confidence_score': confidence_score,
                    'image_id': image_id,
                    'source': 'imx500_on_chip'
                }
                
                self.recent_detections.append(detection_summary)
                
                # Update hourly statistics
                with performance_monitor("stats_update"):
                    hour_key = datetime.now().strftime('%Y-%m-%d_%H')
                    self.hourly_stats[hour_key]['total_vehicles'] += vehicle_count
                    self.hourly_stats[hour_key]['detection_count'] += 1
                    
                    if primary_vehicle:
                        self.hourly_stats[hour_key]['vehicle_types'][primary_vehicle] += 1
                    
                    # Update confidence average
                    current_avg = self.hourly_stats[hour_key]['avg_confidence']
                    current_count = self.hourly_stats[hour_key]['detection_count']
                    new_avg = ((current_avg * (current_count - 1)) + confidence_score) / current_count
                    self.hourly_stats[hour_key]['avg_confidence'] = new_avg
                
        except Exception as e:
            self.logger.log_error(
                error_type="imx500_processing_error",
                message="Error processing IMX500 capture event",
                error=str(e),
                details={"correlation_id": correlation_id, "event_data": event_data}
            )
    
    def _process_radar_motion_event_enhanced(self, event_data: Dict[str, Any], correlation_id: str):
        """Enhanced radar motion event processing with correlation propagation"""
        
        try:
            speed = event_data.get('speed', 0)
            magnitude = event_data.get('magnitude', 0)
            direction = event_data.get('direction', 'unknown')
            timestamp = event_data.get('timestamp', time.time())
            alert_level = event_data.get('alert_level', 'normal')
            detection_id = event_data.get('detection_id')
            
            # Log business event with correlation from radar service
            self.logger.log_business_event(
                event_name="radar_motion_consolidation",
                event_data={
                    "business_context": "traffic_monitoring", 
                    "message": f"🎯 Consolidating radar motion: {speed} mph (alert: {alert_level})",
                    "correlation_id": correlation_id,
                    "detection_id": detection_id,
                    "speed_mph": speed,
                    "magnitude": magnitude,
                    "direction": direction,
                    "alert_level": alert_level,
                    "radar_timestamp": timestamp
                }
            )
            
            # Trigger comprehensive data collection with correlation
            with performance_monitor("comprehensive_data_collection"):
                consolidated_data = self._collect_comprehensive_data_enhanced(event_data, correlation_id)
            
            if consolidated_data:
                self.logger.log_business_event(
                    event_name="data_consolidation_complete",
                    event_data={
                        "business_context": "traffic_monitoring",
                        "message": "📊 Comprehensive vehicle data consolidation completed",
                        "correlation_id": correlation_id,
                        "consolidated_sources": consolidated_data.get('sources', []),
                        "total_data_points": len(consolidated_data.get('detections', [])),
                        "consolidation_confidence": consolidated_data.get('confidence', 0.0)
                    }
                )
            
        except Exception as e:
            self.logger.log_error(
                error_type="radar_consolidation_error",
                message="Error processing radar motion event for consolidation",
                error=str(e),
                details={"correlation_id": correlation_id, "event_data": event_data}
            )
    
    def _collect_comprehensive_data_enhanced(self, trigger_event: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
        """Enhanced comprehensive data collection with correlation tracking"""
        
        try:
            collection_start = time.time()
            
            self.logger.debug(
                f"Starting comprehensive data collection for correlation: {correlation_id}",
                details={"trigger_event_type": trigger_event.get('event_type')}
            )
            
            consolidated_data = {
                'correlation_id': correlation_id,
                'trigger_event': trigger_event,
                'collection_timestamp': time.time(),
                'sources': [],
                'detections': [],
                'confidence': 0.0
            }
            
            # Collect recent radar data
            with performance_monitor("radar_data_collection"):
                radar_data = self._get_recent_radar_data(correlation_id)
                if radar_data:
                    consolidated_data['sources'].append('radar')
                    consolidated_data['detections'].extend(radar_data)
            
            # Collect recent IMX500 AI detections
            with performance_monitor("imx500_data_collection"):
                imx500_data = self._get_recent_imx500_data(correlation_id)
                if imx500_data:
                    consolidated_data['sources'].append('imx500_ai')
                    consolidated_data['detections'].extend(imx500_data)
            
            # Calculate consolidation confidence
            consolidated_data['confidence'] = self._calculate_consolidation_confidence(consolidated_data)
            
            # Store consolidated data
            with performance_monitor("consolidated_data_storage"):
                self._store_consolidated_data(consolidated_data)
            
            collection_time = time.time() - collection_start
            
            self.logger.debug(
                f"Comprehensive data collection completed in {collection_time*1000:.2f}ms",
                details={
                    "correlation_id": correlation_id,
                    "sources": consolidated_data['sources'],
                    "detection_count": len(consolidated_data['detections']),
                    "confidence": consolidated_data['confidence']
                }
            )
            
            return consolidated_data
            
        except Exception as e:
            self.logger.log_error(
                error_type="data_collection_error",
                message="Error during comprehensive data collection",
                error=str(e),
                details={"correlation_id": correlation_id}
            )
            return {}
    
    def _get_recent_radar_data(self, correlation_id: str) -> List[Dict[str, Any]]:
        """Get recent radar data with correlation context"""
        try:
            # Query Redis for recent radar detections
            radar_keys = self.redis_client.keys("radar_data:*")
            recent_radar = []
            
            for key in radar_keys[-10:]:  # Last 10 radar entries
                data = self.redis_client.hgetall(key)
                if data:
                    data['correlation_id'] = correlation_id
                    recent_radar.append(data)
            
            return recent_radar
        except Exception as e:
            self.logger.debug(f"Error collecting radar data: {e}")
            return []
    
    def _get_recent_imx500_data(self, correlation_id: str) -> List[Dict[str, Any]]:
        """Get recent IMX500 AI detection data with correlation context"""
        try:
            # Get recent detections from our in-memory cache
            recent_imx500 = []
            for detection in list(self.recent_detections)[-5:]:  # Last 5 detections
                detection_copy = detection.copy()
                detection_copy['correlation_id'] = correlation_id
                recent_imx500.append(detection_copy)
            
            return recent_imx500
        except Exception as e:
            self.logger.debug(f"Error collecting IMX500 data: {e}")
            return []
    
    def _calculate_consolidation_confidence(self, consolidated_data: Dict[str, Any]) -> float:
        """Calculate confidence score for consolidated data"""
        try:
            sources = consolidated_data.get('sources', [])
            detections = consolidated_data.get('detections', [])
            
            # Base confidence on number of sources and detections
            source_confidence = len(sources) * 0.3  # Each source adds 30%
            detection_confidence = min(len(detections) * 0.1, 0.4)  # Up to 40% from detections
            
            return min(source_confidence + detection_confidence, 1.0)
        except Exception:
            return 0.0
    
    def _store_consolidated_data(self, consolidated_data: Dict[str, Any]):
        """Store consolidated data in FIFO stream for database persistence"""
        try:
            correlation_id = consolidated_data.get('correlation_id')
            
            # Add to standardized FIFO stream for database persistence
            stream_name = "traffic:consolidated"
            message_data = {
                'data': json.dumps(consolidated_data),
                'correlation_id': correlation_id,
                'timestamp': time.time()
            }
            
            # FIFO: Add to Redis stream for persistence service to consume
            message_id = self.redis_client.xadd(stream_name, message_data)
            
            self.logger.log_business_event(
                event_name="consolidated_data_queued", 
                event_data={
                    "business_context": "traffic_monitoring",
                    "message": f"📦 Consolidated data queued for persistence (FIFO)",
                    'correlation_id': correlation_id,
                    'consolidation_id': consolidated_data.get('consolidation_id'),
                    'stream_message_id': message_id,
                    'stream_name': stream_name
                }
            )
            
        except Exception as e:
            self.logger.log_error(
                error_type="data_storage_error",
                message="Error storing consolidated data to FIFO stream",
                error=str(e),
                details={'correlation_id': consolidated_data.get('correlation_id')}
            )
    
    def _get_current_weather_data(self) -> Dict[str, Any]:
        """Get current weather conditions from available sources"""
        try:
            weather_data = {}
            
            # Try to get DHT22 sensor data
            try:
                dht22_data = self.redis_client.hgetall("weather:dht22")
                if dht22_data:
                    weather_data["dht22"] = {
                        "temperature": float(dht22_data.get("temperature", 0)),
                        "humidity": float(dht22_data.get("humidity", 0)),
                        "timestamp": dht22_data.get("timestamp")
                    }
            except (ValueError, TypeError):
                pass
            
            # Try to get airport weather data
            try:
                airport_data = self.redis_client.hgetall("weather:airport:latest")
                if airport_data:
                    weather_data["airport"] = airport_data
            except Exception:
                pass
            
            return weather_data
            
        except Exception as e:
            self.logger.debug(f"Error collecting weather data: {e}")
            return {}
    
    def _update_radar_statistics(self, speed: float, alert_level: str):
        """Update radar detection statistics"""
        try:
            hour_key = datetime.now().strftime('%Y-%m-%d_%H')
            
            # Update hourly stats
            self.hourly_stats[hour_key]['total_vehicles'] += 1
            self.hourly_stats[hour_key]['detection_count'] += 1
            
            # Track speed statistics
            if 'speed_sum' not in self.hourly_stats[hour_key]:
                self.hourly_stats[hour_key]['speed_sum'] = 0
                self.hourly_stats[hour_key]['speed_count'] = 0
                
            self.hourly_stats[hour_key]['speed_sum'] += speed
            self.hourly_stats[hour_key]['speed_count'] += 1
            
            # Track alert levels
            if 'alert_levels' not in self.hourly_stats[hour_key]:
                self.hourly_stats[hour_key]['alert_levels'] = defaultdict(int)
                
            self.hourly_stats[hour_key]['alert_levels'][alert_level] += 1
            
        except Exception as e:
            self.logger.debug(f"Error updating radar statistics: {e}")
    
    def _check_new_vehicle_detections_enhanced(self):
        """Legacy method - no longer needed with stream consumption"""
        pass
    
    def _stats_update_loop_enhanced(self):
        """Enhanced statistics update loop with correlation tracking"""
        
        with CorrelationContext.create("stats_update_session") as ctx:
            self.logger.log_service_event(
                event_type="stats_thread_started", 
                message="Statistics update thread started"
            )
            
            while self.running:
                try:
                    # Update statistics without excessive performance logging
                    self._update_statistics(ctx)
                    time.sleep(self.stats_update_interval)
                    
                except Exception as e:
                    self.logger.log_error(
                        error_type="stats_update_error",
                        message="Error in statistics update loop",
                        error=str(e)
                    )
                    time.sleep(self.stats_update_interval)
    
    def _cleanup_loop_enhanced(self):
        """Enhanced cleanup loop with correlation tracking"""
        
        with CorrelationContext.create("cleanup_session") as ctx:
            self.logger.log_service_event(
                event_type="cleanup_thread_started",
                message="Data cleanup thread started"
            )
            
            while self.running:
                try:
                    with performance_monitor("cleanup_cycle"):
                        cleanup_count = self._cleanup_old_data(ctx)
                    
                    if cleanup_count > 0:
                        self.logger.debug(
                            f"Cleaned up {cleanup_count} old data entries"
                        )
                    
                    time.sleep(3600)  # Run cleanup every hour
                    
                except Exception as e:
                    self.logger.log_error(
                        error_type="cleanup_error", 
                        message="Error in cleanup loop",
                        error=str(e)
                    )
                    time.sleep(3600)
    
    def _update_statistics(self, correlation_id: str):
        """Update service statistics"""
        try:
            current_time = time.time()
            uptime = current_time - self.startup_time if self.startup_time else 0
            
            # Calculate performance metrics
            avg_processing_time = 0
            if self.processing_times:
                avg_processing_time = sum(self.processing_times) / len(self.processing_times)
            
            recent_detection_count = len(self.recent_detections)
            
            # Log statistics
            self.logger.debug(
                f"📊 Service statistics update",
                details={
                    "correlation_id": correlation_id,
                    "uptime_seconds": uptime,
                    "total_events_processed": self.event_count,
                    "recent_detections": recent_detection_count,
                    "avg_processing_time_ms": avg_processing_time * 1000,
                    "hourly_stats_count": len(self.hourly_stats)
                }
            )
            
        except Exception as e:
            self.logger.log_error(
                error_type="stats_calculation_error",
                message="Error calculating statistics",
                error=str(e)
            )
    
    def _cleanup_old_data(self, correlation_id: str) -> int:
        """Clean up old data entries"""
        try:
            cleanup_count = 0
            
            # Clean up old hourly stats (keep last 48 hours)
            cutoff_time = datetime.now() - timedelta(hours=48)
            cutoff_key = cutoff_time.strftime('%Y-%m-%d_%H')
            
            keys_to_remove = []
            for key in self.hourly_stats.keys():
                if key < cutoff_key:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.hourly_stats[key]
                cleanup_count += 1
            
            return cleanup_count
            
        except Exception as e:
            self.logger.log_error(
                error_type="cleanup_execution_error",
                message="Error during data cleanup",
                error=str(e),
                details={"correlation_id": correlation_id}
            )
            return 0
    
    def _log_processing_stats(self, events_processed: int, correlation_id: str):
        """Log periodic processing statistics"""
        
        uptime = time.time() - self.startup_time if self.startup_time else 0
        avg_processing = sum(self.processing_times) / len(self.processing_times) if self.processing_times else 0
        
        # Calculate vehicle grouping efficiency
        total_vehicle_detections = self.grouped_vehicles_count + self.single_detections_count
        grouping_efficiency = (self.grouped_vehicles_count / total_vehicle_detections * 100) if total_vehicle_detections > 0 else 0
        
        self.logger.log_service_event(
            event_type="periodic_processing_stats",
            message="📊 Vehicle consolidator processing statistics",
            details={
                "correlation_id": correlation_id,
                "uptime_hours": uptime / 3600,
                "events_processed_5min": events_processed,
                "total_events": self.event_count,
                "avg_processing_time_ms": avg_processing * 1000,
                "recent_detections_count": len(self.recent_detections),
                "hourly_stats_periods": len(self.hourly_stats),
                # Vehicle Grouping Statistics
                "vehicle_grouping": {
                    "active_groups": len(self.recent_vehicle_groups),
                    "grouped_detections": self.grouped_vehicles_count,
                    "unique_vehicles": self.single_detections_count,
                    "total_radar_detections": total_vehicle_detections,
                    "grouping_efficiency_percent": round(grouping_efficiency, 1),
                    "duplicate_filter_rate": f"{self.grouped_vehicles_count}/{total_vehicle_detections}" if total_vehicle_detections > 0 else "0/0"
                }
            }
        )
    
    def stop(self):
        """Enhanced service shutdown with correlation tracking"""
        
        with CorrelationContext.create("service_shutdown") as ctx:
            self.logger.log_service_event(
                event_type="service_shutdown_initiated",
                message="🛑 Initiating vehicle consolidator shutdown"
            )
            
            self.running = False
            
            # Stop background threads
            if self.stats_thread and self.stats_thread.is_alive():
                self.stats_thread.join(timeout=5)
                self.logger.debug("Statistics thread stopped")
            
            if self.cleanup_thread and self.cleanup_thread.is_alive():
                self.cleanup_thread.join(timeout=5)
                self.logger.debug("Cleanup thread stopped")
            
            if self.camera_thread and self.camera_thread.is_alive():
                self.camera_thread.join(timeout=5)
                self.logger.debug("Camera processing thread stopped")
            
            # Close camera subscription
            if self.camera_pubsub:
                try:
                    self.camera_pubsub.close()
                    self.logger.debug("Camera Redis subscription closed")
                except Exception as e:
                    self.logger.debug(f"Error closing camera subscription: {e}")
            
            # Close camera subscription
            if self.camera_pubsub:
                try:
                    self.camera_pubsub.close()
                    self.logger.debug("Camera subscription closed")
                except Exception as e:
                    self.logger.log_error(
                        error_type="camera_pubsub_close_error",
                        message="Error closing camera subscription",
                        error=str(e)
                    )
            
            # Close Redis connections
            if self.redis_client:
                try:
                    self.redis_client.close()
                    self.logger.debug("Redis connection closed")
                except Exception as e:
                    self.logger.log_error(
                        error_type="redis_close_error",
                        message="Error closing Redis connection",
                        error=str(e)
                    )
            
            # Log final statistics
            if self.startup_time:
                uptime = time.time() - self.startup_time
                avg_processing = sum(self.processing_times) / len(self.processing_times) if self.processing_times else 0
                
                self.logger.log_service_event(
                    event_type="service_shutdown_complete",
                    message="✅ Vehicle consolidator shutdown complete",
                    details={
                        "total_uptime_seconds": uptime,
                        "total_events_processed": self.event_count,
                        "avg_processing_time_ms": avg_processing * 1000,
                        "final_detection_count": len(self.recent_detections)
                    }
                )


def main():
    """Main service entry point with enhanced error handling"""
    
    # Read configuration from environment
    redis_host = os.environ.get('REDIS_HOST', 'redis')
    redis_port = int(os.environ.get('REDIS_PORT', '6379'))
    data_retention_hours = int(os.environ.get('DATA_RETENTION_HOURS', '24'))
    stats_interval = int(os.environ.get('STATS_UPDATE_INTERVAL', '60'))
    
    # Create enhanced consolidator service
    consolidator = VehicleDetectionConsolidatorEnhanced(
        redis_host=redis_host,
        redis_port=redis_port,
        data_retention_hours=data_retention_hours,
        stats_update_interval=stats_interval
    )
    
    try:
        consolidator.start()
    except KeyboardInterrupt:
        print("\nReceived interrupt signal...")
    except Exception as e:
        print(f"Service failed: {e}")
    finally:
        consolidator.stop()


if __name__ == '__main__':
    main()
