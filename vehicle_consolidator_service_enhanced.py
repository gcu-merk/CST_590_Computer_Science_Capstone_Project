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
                exception=RuntimeError("Redis not available")
            )
            raise RuntimeError("Redis required for vehicle detection data consolidation")
        
        # Verify Redis models are available
        if RedisDataManager is None:
            self.logger.log_error(
                error_type="missing_redis_models",
                message="RedisDataManager not available - consolidator cannot start",
                exception=RuntimeError("Redis models not available")
            )
            raise RuntimeError("Redis models not available")
        
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.data_retention_hours = data_retention_hours
        self.stats_update_interval = stats_update_interval
        
        # Redis connection
        self.redis_client = None
        self.pubsub = None
        self.data_manager = None
        
        # Service state
        self.running = False
        self.stats_thread = None
        self.cleanup_thread = None
        
        # Statistics tracking
        self.hourly_stats = defaultdict(lambda: {
            'total_vehicles': 0,
            'vehicle_types': defaultdict(int),
            'avg_confidence': 0.0,
            'detection_count': 0
        })
        
        self.recent_detections = deque(maxlen=1000)  # Last 1000 detections
        
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
                    
                    # Setup pub/sub for real-time events
                    self.pubsub = self.redis_client.pubsub()
                    self.pubsub.subscribe("traffic_events")
                
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
                    exception=e,
                    details={
                        "redis_host": self.redis_host,
                        "redis_port": self.redis_port
                    }
                )
                return False
    
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
                    exception=RuntimeError("Redis connection failed")
                )
                return False
            
            self.running = True
            self.startup_time = time.time()
            
            # Start background threads with error handling
            try:
                self.stats_thread = threading.Thread(target=self._stats_update_loop_enhanced, daemon=True)
                self.cleanup_thread = threading.Thread(target=self._cleanup_loop_enhanced, daemon=True)
                
                self.stats_thread.start()
                self.cleanup_thread.start()
                
                self.logger.log_service_event(
                    event_type="background_threads_started",
                    message="Background processing threads started successfully",
                    details={
                        "stats_thread_id": self.stats_thread.ident,
                        "cleanup_thread_id": self.cleanup_thread.ident
                    }
                )
                
                # Main event processing loop
                self._process_vehicle_events_enhanced()
                
            except KeyboardInterrupt:
                self.logger.log_service_event(
                    event_type="shutdown_requested",
                    message="Shutdown requested by user (Ctrl+C)"
                )
            except Exception as e:
                self.logger.log_error(
                    error_type="service_runtime_error",
                    message="Consolidator service encountered runtime error",
                    exception=e
                )
            finally:
                self.stop()
            
            return True
    
    def _process_vehicle_events_enhanced(self):
        """Enhanced event processing with correlation tracking and performance monitoring"""
        
        with CorrelationContext.create("event_processing_session") as ctx:
            self.logger.log_service_event(
                event_type="event_processing_started",
                message="Starting enhanced vehicle detection event processing from IMX500 and radar"
            )
            
            events_processed = 0
            last_stats_log = time.time()
            
            while self.running:
                try:
                    processing_start = time.time()
                    
                    # Listen for Redis pub/sub messages
                    message = self.pubsub.get_message(timeout=1.0)
                    
                    if message and message['type'] == 'message':
                        with performance_monitor("event_message_processing"):
                            self._handle_redis_message_enhanced(message)
                            events_processed += 1
                            self.event_count += 1
                    
                    # Check for new vehicle detections directly
                    with performance_monitor("detection_polling"):
                        self._check_new_vehicle_detections_enhanced()
                    
                    # Log periodic statistics (every 5 minutes)
                    if time.time() - last_stats_log > 300:
                        self._log_processing_stats(events_processed, ctx.correlation_id)
                        last_stats_log = time.time()
                        events_processed = 0
                    
                    # Track processing performance
                    processing_time = time.time() - processing_start
                    self.processing_times.append(processing_time)
                    
                    # Keep only last 1000 processing times
                    if len(self.processing_times) > 1000:
                        self.processing_times = self.processing_times[-1000:]
                    
                    time.sleep(0.1)  # Small delay to prevent CPU spinning
                    
                except Exception as e:
                    self.logger.log_error(
                        error_type="event_processing_error",
                        message="Error in event processing loop",
                        exception=e,
                        details={"events_processed": events_processed}
                    )
                    time.sleep(1)
            
            self.logger.log_service_event(
                event_type="event_processing_stopped",
                message="Vehicle detection event processing stopped",
                details={"total_events_processed": events_processed}
            )
    
    def _handle_redis_message_enhanced(self, message):
        """Enhanced Redis message handling with correlation tracking"""
        
        try:
            event_data = json.loads(message['data'])
            
            # Extract or create correlation ID
            correlation_id = event_data.get('correlation_id', str(uuid.uuid4())[:8])
            
            with CorrelationContext.create("event_processing", correlation_id) as ctx:
                event_type = event_data.get('event_type')
                
                self.logger.log_debug(
                    f"Processing event: {event_type}",
                    details={"event_data": event_data}
                )
                
                if event_type == 'imx500_ai_capture':
                    self._process_imx500_capture_event_enhanced(event_data, correlation_id)
                elif event_type == 'radar_motion_detected':
                    self._process_radar_motion_event_enhanced(event_data, correlation_id)
                else:
                    self.logger.log_debug(f"Unknown event type: {event_type}")
                    
        except json.JSONDecodeError:
            self.logger.log_warning(
                warning_type="invalid_json_message",
                message="Invalid JSON in Redis message",
                details={"raw_message": str(message.get('data', '')[:100])}
            )
        except Exception as e:
            self.logger.log_error(
                error_type="message_handling_error",
                message="Error handling Redis message",
                exception=e,
                details={"message_type": message.get('type')}
            )
    
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
                    event_type="imx500_vehicle_detected",
                    business_context="traffic_monitoring",
                    message=f"🚗 IMX500 AI detected {vehicle_count} vehicles (primary: {primary_vehicle})",
                    details={
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
                self.logger.log_debug(
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
                exception=e,
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
                event_type="radar_motion_consolidation",
                business_context="traffic_monitoring", 
                message=f"🎯 Consolidating radar motion: {speed} mph (alert: {alert_level})",
                details={
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
                    event_type="data_consolidation_complete",
                    business_context="traffic_monitoring",
                    message="📊 Comprehensive vehicle data consolidation completed",
                    details={
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
                exception=e,
                details={"correlation_id": correlation_id, "event_data": event_data}
            )
    
    def _collect_comprehensive_data_enhanced(self, trigger_event: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
        """Enhanced comprehensive data collection with correlation tracking"""
        
        try:
            collection_start = time.time()
            
            self.logger.log_debug(
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
            
            self.logger.log_debug(
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
                exception=e,
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
            self.logger.log_debug(f"Error collecting radar data: {e}")
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
            self.logger.log_debug(f"Error collecting IMX500 data: {e}")
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
        """Store consolidated data with correlation tracking"""
        try:
            correlation_id = consolidated_data.get('correlation_id')
            
            # Store in Redis with TTL
            key = f"consolidated_data:{correlation_id}:{int(time.time())}"
            self.redis_client.hset(key, mapping={
                'data': json.dumps(consolidated_data),
                'timestamp': time.time(),
                'correlation_id': correlation_id
            })
            self.redis_client.expire(key, self.data_retention_hours * 3600)
            
        except Exception as e:
            self.logger.log_error(
                error_type="data_storage_error",
                message="Error storing consolidated data",
                exception=e
            )
    
    def _check_new_vehicle_detections_enhanced(self):
        """Enhanced detection polling with performance monitoring"""
        try:
            # This would poll for new detections in Redis
            # Implementation depends on specific Redis key patterns
            pass
        except Exception as e:
            self.logger.log_debug(f"Error checking new detections: {e}")
    
    def _stats_update_loop_enhanced(self):
        """Enhanced statistics update loop with correlation tracking"""
        
        with CorrelationContext.create("stats_update_session") as ctx:
            self.logger.log_service_event(
                event_type="stats_thread_started", 
                message="Statistics update thread started"
            )
            
            while self.running:
                try:
                    with performance_monitor("stats_update_cycle"):
                        self._update_statistics(ctx.correlation_id)
                    
                    time.sleep(self.stats_update_interval)
                    
                except Exception as e:
                    self.logger.log_error(
                        error_type="stats_update_error",
                        message="Error in statistics update loop",
                        exception=e
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
                        cleanup_count = self._cleanup_old_data(ctx.correlation_id)
                    
                    if cleanup_count > 0:
                        self.logger.log_debug(
                            f"Cleaned up {cleanup_count} old data entries"
                        )
                    
                    time.sleep(3600)  # Run cleanup every hour
                    
                except Exception as e:
                    self.logger.log_error(
                        error_type="cleanup_error", 
                        message="Error in cleanup loop",
                        exception=e
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
            self.logger.log_debug(
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
                exception=e
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
                exception=e,
                details={"correlation_id": correlation_id}
            )
            return 0
    
    def _log_processing_stats(self, events_processed: int, correlation_id: str):
        """Log periodic processing statistics"""
        
        uptime = time.time() - self.startup_time if self.startup_time else 0
        avg_processing = sum(self.processing_times) / len(self.processing_times) if self.processing_times else 0
        
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
                "hourly_stats_periods": len(self.hourly_stats)
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
                self.logger.log_debug("Statistics thread stopped")
            
            if self.cleanup_thread and self.cleanup_thread.is_alive():
                self.cleanup_thread.join(timeout=5)
                self.logger.log_debug("Cleanup thread stopped")
            
            # Close Redis connections
            if self.pubsub:
                try:
                    self.pubsub.close()
                    self.logger.log_debug("Redis pub/sub closed")
                except Exception as e:
                    self.logger.log_error(
                        error_type="pubsub_close_error",
                        message="Error closing Redis pub/sub",
                        exception=e
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