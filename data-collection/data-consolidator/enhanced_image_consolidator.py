#!/usr/bin/env python3
"""
Enhanced Data Consolidator for Image Analysis System
Extends the original data consolidator to handle image analysis results from Redis

Features:
- Pulls image analysis results from Redis
- Consolidates vehicle detections, sky analysis, and weather data
- Integrates with existing sensor data (DHT22, etc.)
- Prepares data for API consumption
- Maintains historical data and statistics
"""

import sys
import time
import logging
import json
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Any
import threading

# Import base consolidator
try:
    from .data_consolidator import DataConsolidator as BaseConsolidator, ConsolidatedRecord
    BASE_CONSOLIDATOR_AVAILABLE = True
except ImportError:
    try:
        from data_consolidator import DataConsolidator as BaseConsolidator, ConsolidatedRecord
        BASE_CONSOLIDATOR_AVAILABLE = True
    except ImportError:
        BASE_CONSOLIDATOR_AVAILABLE = False
        logging.warning("Base data consolidator not available")

# Redis and data models
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.warning("Redis not available - consolidator will work in standalone mode")

# Import our Redis models and services
try:
    sys.path.append(str(Path(__file__).parent.parent))
    from edge_processing.redis_models import (
        ConsolidatedImageData, ImageAnalysisResult, VehicleType, SkyCondition,
        RedisDataManager, RedisKeys
    )
    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False
    logging.warning("Redis models not available - using fallback data structures")

logger = logging.getLogger(__name__)

@dataclass
class EnhancedConsolidatedRecord:
    """Enhanced consolidated record including image analysis data"""
    consolidation_id: str
    timestamp: float
    
    # Image analysis data
    image_analysis: Optional[Dict] = None
    vehicle_detections: List[Dict] = None
    sky_analysis: Optional[Dict] = None
    
    # Traditional sensor data
    weather_data: Optional[Dict] = None
    speed_measurements: List[Dict] = None
    system_metrics: Optional[Dict] = None
    
    # Additional context
    trigger_source: Optional[str] = None
    processing_metadata: Optional[Dict] = None

class EnhancedDataConsolidator:
    """
    Enhanced data consolidator for image analysis system
    Pulls data from Redis and consolidates with other sensor data
    """
    
    def __init__(self,
                 redis_host: str = "localhost",
                 redis_port: int = 6379,
                 redis_db: int = 0,
                 enable_redis: bool = True,
                 consolidation_interval: float = 5.0,
                 max_records: int = 1000):
        
        self.redis_enabled = enable_redis and REDIS_AVAILABLE and MODELS_AVAILABLE
        self.redis_manager = None
        self.consolidation_interval = consolidation_interval
        self.max_records = max_records
        
        # Initialize Redis connection
        if self.redis_enabled:
            try:
                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    db=redis_db,
                    decode_responses=True,
                    socket_timeout=5,
                    socket_connect_timeout=5
                )
                self.redis_client.ping()
                self.redis_manager = RedisDataManager(self.redis_client)
                logger.info(f"Enhanced consolidator connected to Redis: {redis_host}:{redis_port}")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}. Running in standalone mode.")
                self.redis_enabled = False
        
        # Initialize base consolidator if available
        self.base_consolidator = None
        if BASE_CONSOLIDATOR_AVAILABLE:
            try:
                self.base_consolidator = BaseConsolidator()
                logger.info("Base data consolidator initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize base consolidator: {e}")
        
        # Data storage
        self.consolidated_records = []
        self.is_running = False
        self.consolidation_thread = None
        
        # Performance tracking
        self.total_consolidations = 0
        self.last_consolidation_time = 0
        self.avg_consolidation_time = 0.0
        
        # Data cache for efficiency
        self.weather_data_cache = {}
        self.cache_ttl = 300  # 5 minutes
        
        logger.info("Enhanced Data Consolidator initialized")
    
    def start_consolidation_service(self):
        """Start the automatic consolidation service"""
        if self.is_running:
            logger.warning("Consolidation service is already running")
            return
        
        self.is_running = True
        self.consolidation_thread = threading.Thread(
            target=self._consolidation_loop,
            daemon=True
        )
        self.consolidation_thread.start()
        logger.info("Enhanced consolidation service started")
    
    def stop_consolidation_service(self):
        """Stop the automatic consolidation service"""
        self.is_running = False
        if self.consolidation_thread:
            self.consolidation_thread.join(timeout=10.0)
        logger.info("Enhanced consolidation service stopped")
    
    def _consolidation_loop(self):
        """Main consolidation loop"""
        logger.info("Starting consolidation loop")
        
        while self.is_running:
            try:
                start_time = time.time()
                
                # Check for new image analysis results to consolidate
                new_consolidations = self._process_pending_consolidations()
                
                if new_consolidations > 0:
                    processing_time = (time.time() - start_time) * 1000
                    logger.info(f"Consolidated {new_consolidations} records in {processing_time:.1f}ms")
                    self._update_performance_metrics(processing_time)
                
                # Sleep until next consolidation cycle
                time.sleep(self.consolidation_interval)
                
            except Exception as e:
                logger.error(f"Error in consolidation loop: {e}")
                time.sleep(self.consolidation_interval)
        
        logger.info("Consolidation loop stopped")
    
    def _process_pending_consolidations(self) -> int:
        """Process pending consolidation requests from Redis"""
        if not self.redis_enabled:
            return 0
        
        consolidations_processed = 0
        
        try:
            # Get pending consolidated data from Redis queue
            queue_length = self.redis_client.llen(RedisKeys.CONSOLIDATED_DATA_QUEUE)
            
            for _ in range(min(queue_length, 10)):  # Process up to 10 at a time
                data = self.redis_client.rpop(RedisKeys.CONSOLIDATED_DATA_QUEUE)
                if data:
                    try:
                        consolidated_data = json.loads(data)
                        record = self._create_enhanced_record(consolidated_data)
                        if record:
                            self._store_consolidated_record(record)
                            consolidations_processed += 1
                    except Exception as e:
                        logger.error(f"Failed to process consolidated data: {e}")
            
        except Exception as e:
            logger.error(f"Failed to process pending consolidations: {e}")
        
        return consolidations_processed
    
    def consolidate_image_analysis(self, image_id: str) -> Optional[EnhancedConsolidatedRecord]:
        """
        Manually consolidate data for a specific image analysis
        
        Args:
            image_id: ID of the image analysis to consolidate
            
        Returns:
            Consolidated record or None if failed
        """
        try:
            if not self.redis_enabled:
                logger.warning("Redis not available - cannot consolidate image analysis")
                return None
            
            # Get image analysis result
            image_analysis = self.redis_manager.get_image_analysis(image_id)
            if not image_analysis:
                logger.warning(f"No image analysis found for ID: {image_id}")
                return None
            
            # Convert to dictionary format for processing
            analysis_dict = asdict(image_analysis) if hasattr(image_analysis, '__dict__') else image_analysis
            
            # Create consolidated record
            record = self._create_enhanced_record({
                "image_analysis": analysis_dict,
                "timestamp": analysis_dict.get("timestamp", time.time())
            })
            
            if record:
                self._store_consolidated_record(record)
                logger.info(f"Manual consolidation completed for image: {image_id}")
            
            return record
            
        except Exception as e:
            logger.error(f"Failed to consolidate image analysis {image_id}: {e}")
            return None
    
    def _create_enhanced_record(self, data: Dict) -> Optional[EnhancedConsolidatedRecord]:
        """Create enhanced consolidated record from data"""
        try:
            consolidation_id = str(uuid.uuid4())
            timestamp = data.get("timestamp", time.time())
            
            # Extract image analysis data
            image_analysis = data.get("image_analysis")
            vehicle_detections = []
            sky_analysis = None
            
            if image_analysis:
                vehicle_detections = image_analysis.get("vehicle_detections", [])
                sky_analysis = image_analysis.get("sky_analysis")
            
            # Get weather data (with caching)
            weather_data = self._get_cached_weather_data(timestamp)
            
            # Get system metrics
            system_metrics = self._get_system_metrics()
            
            # Create enhanced record
            record = EnhancedConsolidatedRecord(
                consolidation_id=consolidation_id,
                timestamp=timestamp,
                image_analysis=image_analysis,
                vehicle_detections=vehicle_detections,
                sky_analysis=sky_analysis,
                weather_data=weather_data,
                speed_measurements=[],  # TODO: Integrate with speed measurements
                system_metrics=system_metrics,
                trigger_source=image_analysis.get("trigger_source") if image_analysis else None,
                processing_metadata={
                    "consolidation_version": "2.0",
                    "consolidation_timestamp": time.time(),
                    "data_sources": {
                        "image_analysis": image_analysis is not None,
                        "weather_data": weather_data is not None,
                        "system_metrics": system_metrics is not None
                    }
                }
            )
            
            return record
            
        except Exception as e:
            logger.error(f"Failed to create enhanced record: {e}")
            return None
    
    def _get_cached_weather_data(self, timestamp: float) -> Optional[Dict]:
        """Get weather data with caching"""
        current_time = time.time()
        
        # Check cache first
        if "data" in self.weather_data_cache and "timestamp" in self.weather_data_cache:
            cache_age = current_time - self.weather_data_cache["timestamp"]
            if cache_age < self.cache_ttl:
                return self.weather_data_cache["data"]
        
        # Fetch fresh weather data
        weather_data = self._fetch_weather_data()
        
        # Update cache
        self.weather_data_cache = {
            "data": weather_data,
            "timestamp": current_time
        }
        
        return weather_data
    
    def _fetch_weather_data(self) -> Optional[Dict]:
        """Fetch current weather data from Redis"""
        if not self.redis_enabled:
            return None
        
        try:
            # Get DHT22 weather data
            dht22_key = "weather:dht22"  # From DHT22 service
            weather_data = self.redis_client.get(dht22_key)
            
            if weather_data:
                return json.loads(weather_data)
            
        except Exception as e:
            logger.warning(f"Failed to fetch weather data: {e}")
        
        return None
    
    def _get_system_metrics(self) -> Optional[Dict]:
        """Get current system metrics"""
        try:
            # Try to import psutil for system metrics
            try:
                import psutil
                return {
                    "cpu_percent": psutil.cpu_percent(interval=1),
                    "memory_percent": psutil.virtual_memory().percent,
                    "disk_percent": psutil.disk_usage('/').percent,
                    "timestamp": time.time()
                }
            except ImportError:
                # psutil not available, use basic metrics
                logger.debug("psutil not available, using basic system metrics")
                return {
                    "cpu_percent": None,
                    "memory_percent": None,
                    "disk_percent": None,
                    "timestamp": time.time(),
                    "note": "psutil not available"
                }
        except Exception as e:
            logger.warning(f"Failed to get system metrics: {e}")
            return None
    
    def _store_consolidated_record(self, record: EnhancedConsolidatedRecord):
        """Store consolidated record"""
        # Add to local storage
        self.consolidated_records.append(record)
        
        # Maintain max records limit
        if len(self.consolidated_records) > self.max_records:
            self.consolidated_records = self.consolidated_records[-self.max_records:]
        
        # Store in Redis if available
        if self.redis_enabled:
            try:
                # Convert to dictionary for JSON serialization
                record_dict = asdict(record)
                
                # Store latest consolidated data
                latest_key = "consolidated:latest"
                self.redis_client.set(
                    latest_key,
                    json.dumps(record_dict, default=self._json_serializer),
                    ex=3600  # 1 hour TTL
                )
                
                # Store in time-series format for API consumption
                api_key = f"api:consolidated:{record.consolidation_id}"
                self.redis_client.set(
                    api_key,
                    json.dumps(record_dict, default=self._json_serializer),
                    ex=86400  # 24 hours TTL
                )
                
            except Exception as e:
                logger.warning(f"Failed to store record in Redis: {e}")
        
        # Store in base consolidator if available
        if self.base_consolidator:
            try:
                self.base_consolidator.consolidate_data(
                    vehicle_detections=record.vehicle_detections,
                    speed_measurements=record.speed_measurements,
                    system_metrics=record.system_metrics
                )
            except Exception as e:
                logger.warning(f"Failed to store in base consolidator: {e}")
    
    def _update_performance_metrics(self, processing_time: float):
        """Update performance tracking"""
        self.total_consolidations += 1
        self.last_consolidation_time = time.time()
        self.avg_consolidation_time = (
            (self.avg_consolidation_time * (self.total_consolidations - 1) + processing_time) /
            self.total_consolidations
        )
    
    def get_latest_consolidated_data(self) -> Optional[EnhancedConsolidatedRecord]:
        """Get the most recent consolidated record"""
        if self.consolidated_records:
            return self.consolidated_records[-1]
        return None
    
    def get_consolidated_data_since(self, since_timestamp: float) -> List[EnhancedConsolidatedRecord]:
        """Get consolidated data since a specific timestamp"""
        return [
            record for record in self.consolidated_records
            if record.timestamp >= since_timestamp
        ]
    
    def get_consolidated_data_for_api(self, limit: int = 50) -> List[Dict]:
        """Get consolidated data formatted for API consumption"""
        records = self.consolidated_records[-limit:] if limit else self.consolidated_records
        
        api_data = []
        for record in records:
            api_record = {
                "id": record.consolidation_id,
                "timestamp": record.timestamp,
                "datetime": datetime.fromtimestamp(record.timestamp, tz=timezone.utc).isoformat(),
                "image_analysis": record.image_analysis,
                "vehicle_count": len(record.vehicle_detections) if record.vehicle_detections else 0,
                "sky_condition": record.sky_analysis.get("condition") if record.sky_analysis else None,
                "weather": record.weather_data,
                "system_metrics": record.system_metrics,
                "trigger_source": record.trigger_source
            }
            api_data.append(api_record)
        
        return api_data
    
    def export_consolidated_data(self, filename: str, format: str = "json") -> bool:
        """Export consolidated data to file"""
        try:
            if format.lower() == "json":
                data = []
                for record in self.consolidated_records:
                    data.append(asdict(record))
                
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2, default=self._json_serializer)
                
                logger.info(f"Exported {len(data)} enhanced records to {filename}")
                return True
            else:
                logger.error(f"Unsupported export format: {format}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to export data: {e}")
            return False
    
    def get_statistics(self) -> Dict:
        """Get consolidation statistics"""
        total_records = len(self.consolidated_records)
        
        if total_records == 0:
            return {
                "total_records": 0,
                "avg_consolidation_time_ms": 0,
                "records_per_hour": 0,
                "last_consolidation": None
            }
        
        # Calculate records per hour
        if total_records > 1:
            time_span = self.consolidated_records[-1].timestamp - self.consolidated_records[0].timestamp
            records_per_hour = (total_records / max(time_span / 3600, 1))
        else:
            records_per_hour = 0
        
        return {
            "total_records": total_records,
            "avg_consolidation_time_ms": self.avg_consolidation_time,
            "records_per_hour": records_per_hour,
            "last_consolidation": self.last_consolidation_time,
            "is_running": self.is_running
        }
    
    @staticmethod
    def _json_serializer(obj):
        """Custom JSON serializer for complex objects"""
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        elif hasattr(obj, 'value'):  # Enum
            return obj.value
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    def cleanup(self):
        """Cleanup resources"""
        self.stop_consolidation_service()
        
        if self.redis_enabled and hasattr(self, 'redis_client'):
            try:
                self.redis_client.close()
                logger.info("Enhanced consolidator Redis connection closed")
            except Exception as e:
                logger.warning(f"Error closing Redis connection: {e}")

def main():
    """Main function for testing the enhanced data consolidator"""
    import argparse
    import signal
    
    parser = argparse.ArgumentParser(description="Enhanced Data Consolidator")
    parser.add_argument("--redis-host", type=str, default="localhost", help="Redis host")
    parser.add_argument("--redis-port", type=int, default=6379, help="Redis port")
    parser.add_argument("--no-redis", action="store_true", help="Disable Redis integration")
    parser.add_argument("--interval", type=float, default=5.0, help="Consolidation interval")
    parser.add_argument("--export", type=str, help="Export data to file")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize consolidator
    consolidator = EnhancedDataConsolidator(
        redis_host=args.redis_host,
        redis_port=args.redis_port,
        enable_redis=not args.no_redis,
        consolidation_interval=args.interval
    )
    
    def signal_handler(signum, frame):
        logger.info("Shutdown signal received")
        consolidator.cleanup()
        exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        consolidator.start_consolidation_service()
        
        print("Enhanced Data Consolidator is running...")
        print("Statistics:", consolidator.get_statistics())
        print("Press Ctrl+C to stop")
        
        # Keep running
        while consolidator.is_running:
            time.sleep(1)
            
            # Show periodic statistics
            if int(time.time()) % 30 == 0:  # Every 30 seconds
                stats = consolidator.get_statistics()
                print(f"Stats: {stats['total_records']} records, "
                      f"{stats['records_per_hour']:.1f}/hour")
        
        # Export data if requested
        if args.export:
            consolidator.export_consolidated_data(args.export)
    
    finally:
        consolidator.cleanup()

if __name__ == "__main__":
    main()