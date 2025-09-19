#!/usr/bin/env python3
"""
Redis Data Models for Image Processing System
Defines consistent data structures and Redis key patterns for image analysis pipeline
"""

import json
import time
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Union, Any
from enum import Enum

class VehicleType(Enum):
    """Supported vehicle classification types"""
    PEDESTRIAN = "pedestrian"
    BICYCLE = "bicycle"
    MOTORCYCLE = "motorcycle"
    CAR = "car"
    TRUCK = "truck"
    BUS = "bus"
    VAN = "van"
    DELIVERY_TRUCK = "delivery_truck"
    EMERGENCY_VEHICLE = "emergency_vehicle"
    UNKNOWN = "unknown"

class SkyCondition(Enum):
    """Sky condition classifications"""
    CLEAR = "clear"
    PARTLY_CLOUDY = "partly_cloudy"
    OVERCAST = "overcast"
    STORMY = "stormy"
    NIGHT_CLEAR = "night_clear"
    NIGHT_CLOUDY = "night_cloudy"
    DAWN_DUSK = "dawn_dusk"
    UNKNOWN = "unknown"

@dataclass
class BoundingBox:
    """Bounding box coordinates for detected objects"""
    x: int
    y: int
    width: int
    height: int
    confidence: float

@dataclass
class VehicleDetection:
    """Single vehicle detection result"""
    detection_id: str
    vehicle_type: VehicleType
    confidence: float
    bounding_box: BoundingBox
    timestamp: float
    additional_metadata: Optional[Dict] = None

@dataclass
class SkyAnalysis:
    """Sky condition analysis result"""
    analysis_id: str
    condition: SkyCondition
    confidence: float
    timestamp: float
    light_level: Optional[float] = None  # 0.0 (dark) to 1.0 (bright)
    cloud_coverage: Optional[float] = None  # 0.0 (clear) to 1.0 (overcast)
    additional_metadata: Optional[Dict] = None

@dataclass
class ImageAnalysisResult:
    """Complete image analysis result combining vehicle detection and sky analysis"""
    image_id: str
    image_path: str
    timestamp: float
    trigger_source: str  # "radar", "manual", "scheduled"
    vehicle_detections: List[VehicleDetection]
    sky_analysis: SkyAnalysis
    processing_time_ms: float
    image_metadata: Optional[Dict] = None

@dataclass
class ConsolidatedImageData:
    """Consolidated image data for API consumption"""
    consolidation_id: str
    timestamp: float
    image_analysis: ImageAnalysisResult
    weather_data: Optional[Dict] = None  # From DHT22 or other weather services
    system_metrics: Optional[Dict] = None
    additional_context: Optional[Dict] = None

class RedisKeys:
    """Redis key patterns for image processing system"""
    
    # Motion trigger events
    MOTION_TRIGGER = "motion:trigger:{timestamp}"
    
    # Image analysis results
    IMAGE_ANALYSIS_PENDING = "image:analysis:pending"  # Queue
    IMAGE_ANALYSIS_RESULT = "image:analysis:result:{image_id}"
    IMAGE_ANALYSIS_LATEST = "image:analysis:latest"
    
    # Vehicle detections
    VEHICLE_DETECTION = "vehicle:detection:{detection_id}"
    VEHICLE_DETECTIONS_BY_IMAGE = "vehicle:detections:image:{image_id}"
    
    # Sky analysis
    SKY_ANALYSIS = "sky:analysis:{analysis_id}"
    SKY_ANALYSIS_BY_IMAGE = "sky:analysis:image:{image_id}"
    
    # Consolidated data
    CONSOLIDATED_DATA = "consolidated:image:{consolidation_id}"
    CONSOLIDATED_DATA_LATEST = "consolidated:image:latest"
    CONSOLIDATED_DATA_QUEUE = "consolidated:image:queue"
    
    # System status and health
    IMAGE_SERVICE_STATUS = "status:image_service"
    VEHICLE_SERVICE_STATUS = "status:vehicle_service"
    SKY_SERVICE_STATUS = "status:sky_service"
    
    # Statistics and metrics
    DAILY_VEHICLE_COUNT = "stats:vehicles:daily:{date}"
    HOURLY_SKY_CONDITIONS = "stats:sky:hourly:{date_hour}"
    
    @staticmethod
    def format_key(pattern: str, **kwargs) -> str:
        """Format a key pattern with provided arguments"""
        return pattern.format(**kwargs)

class RedisDataManager:
    """Utility class for managing Redis data operations"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.default_ttl = 86400 * 7  # 7 days default TTL
    
    def store_image_analysis(self, result: ImageAnalysisResult, ttl: Optional[int] = None) -> str:
        """Store complete image analysis result"""
        key = RedisKeys.format_key(RedisKeys.IMAGE_ANALYSIS_RESULT, image_id=result.image_id)
        data = json.dumps(asdict(result), default=self._json_serializer)
        
        pipe = self.redis.pipeline()
        pipe.set(key, data, ex=ttl or self.default_ttl)
        pipe.set(RedisKeys.IMAGE_ANALYSIS_LATEST, data, ex=ttl or self.default_ttl)
        pipe.execute()
        
        return key
    
    def store_vehicle_detection(self, detection: VehicleDetection, image_id: str, ttl: Optional[int] = None) -> str:
        """Store individual vehicle detection"""
        detection_key = RedisKeys.format_key(RedisKeys.VEHICLE_DETECTION, detection_id=detection.detection_id)
        image_detections_key = RedisKeys.format_key(RedisKeys.VEHICLE_DETECTIONS_BY_IMAGE, image_id=image_id)
        
        detection_data = json.dumps(asdict(detection), default=self._json_serializer)
        
        pipe = self.redis.pipeline()
        pipe.set(detection_key, detection_data, ex=ttl or self.default_ttl)
        pipe.sadd(image_detections_key, detection.detection_id)
        pipe.expire(image_detections_key, ttl or self.default_ttl)
        pipe.execute()
        
        return detection_key
    
    def store_sky_analysis(self, analysis: SkyAnalysis, image_id: str, ttl: Optional[int] = None) -> str:
        """Store sky analysis result"""
        analysis_key = RedisKeys.format_key(RedisKeys.SKY_ANALYSIS, analysis_id=analysis.analysis_id)
        image_analysis_key = RedisKeys.format_key(RedisKeys.SKY_ANALYSIS_BY_IMAGE, image_id=image_id)
        
        analysis_data = json.dumps(asdict(analysis), default=self._json_serializer)
        
        pipe = self.redis.pipeline()
        pipe.set(analysis_key, analysis_data, ex=ttl or self.default_ttl)
        pipe.set(image_analysis_key, analysis_data, ex=ttl or self.default_ttl)
        pipe.execute()
        
        return analysis_key
    
    def store_consolidated_data(self, data: ConsolidatedImageData, ttl: Optional[int] = None) -> str:
        """Store consolidated image data"""
        key = RedisKeys.format_key(RedisKeys.CONSOLIDATED_DATA, consolidation_id=data.consolidation_id)
        data_json = json.dumps(asdict(data), default=self._json_serializer)
        
        pipe = self.redis.pipeline()
        pipe.set(key, data_json, ex=ttl or self.default_ttl)
        pipe.set(RedisKeys.CONSOLIDATED_DATA_LATEST, data_json, ex=ttl or self.default_ttl)
        pipe.lpush(RedisKeys.CONSOLIDATED_DATA_QUEUE, data_json)
        pipe.ltrim(RedisKeys.CONSOLIDATED_DATA_QUEUE, 0, 99)  # Keep last 100 records
        pipe.execute()
        
        return key
    
    def get_image_analysis(self, image_id: str) -> Optional[ImageAnalysisResult]:
        """Retrieve image analysis result"""
        key = RedisKeys.format_key(RedisKeys.IMAGE_ANALYSIS_RESULT, image_id=image_id)
        data = self.redis.get(key)
        if data:
            return self._deserialize_image_analysis(json.loads(data))
        return None
    
    def get_latest_image_analysis(self) -> Optional[ImageAnalysisResult]:
        """Get the most recent image analysis"""
        data = self.redis.get(RedisKeys.IMAGE_ANALYSIS_LATEST)
        if data:
            return self._deserialize_image_analysis(json.loads(data))
        return None
    
    def get_consolidated_data(self, consolidation_id: str) -> Optional[ConsolidatedImageData]:
        """Retrieve consolidated data"""
        key = RedisKeys.format_key(RedisKeys.CONSOLIDATED_DATA, consolidation_id=consolidation_id)
        data = self.redis.get(key)
        if data:
            return self._deserialize_consolidated_data(json.loads(data))
        return None
    
    def get_latest_consolidated_data(self) -> Optional[ConsolidatedImageData]:
        """Get the most recent consolidated data"""
        data = self.redis.get(RedisKeys.CONSOLIDATED_DATA_LATEST)
        if data:
            return self._deserialize_consolidated_data(json.loads(data))
        return None
    
    def queue_image_for_analysis(self, image_path: str, trigger_source: str = "manual") -> str:
        """Queue an image for analysis"""
        analysis_request = {
            "image_path": image_path,
            "timestamp": time.time(),
            "trigger_source": trigger_source
        }
        request_data = json.dumps(analysis_request)
        self.redis.lpush(RedisKeys.IMAGE_ANALYSIS_PENDING, request_data)
        return request_data
    
    def get_pending_analysis(self) -> Optional[Dict]:
        """Get next pending image analysis request"""
        data = self.redis.brpop(RedisKeys.IMAGE_ANALYSIS_PENDING, timeout=1)
        if data:
            return json.loads(data[1])
        return None
    
    def update_service_status(self, service_name: str, status: Dict):
        """Update service status/health information"""
        status_key = f"status:{service_name}"
        status_data = json.dumps({
            **status,
            "last_update": time.time()
        }, default=self._json_serializer)
        self.redis.set(status_key, status_data, ex=300)  # 5 minutes TTL
    
    def increment_vehicle_count(self, vehicle_type: VehicleType, date: str = None):
        """Increment daily vehicle count statistics"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        daily_key = RedisKeys.format_key(RedisKeys.DAILY_VEHICLE_COUNT, date=date)
        self.redis.hincrby(daily_key, vehicle_type.value, 1)
        self.redis.expire(daily_key, 86400 * 30)  # Keep for 30 days
    
    def record_sky_condition(self, condition: SkyCondition, date_hour: str = None):
        """Record hourly sky condition statistics"""
        if date_hour is None:
            date_hour = datetime.now().strftime("%Y-%m-%d_%H")
        
        hourly_key = RedisKeys.format_key(RedisKeys.HOURLY_SKY_CONDITIONS, date_hour=date_hour)
        self.redis.hincrby(hourly_key, condition.value, 1)
        self.redis.expire(hourly_key, 86400 * 30)  # Keep for 30 days
    
    @staticmethod
    def _json_serializer(obj):
        """Custom JSON serializer for complex objects"""
        if isinstance(obj, Enum):
            return obj.value
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    @staticmethod
    def _deserialize_image_analysis(data: Dict) -> ImageAnalysisResult:
        """Deserialize image analysis result from JSON"""
        # Convert vehicle detections
        vehicle_detections = []
        for vd_data in data.get('vehicle_detections', []):
            bbox = BoundingBox(**vd_data['bounding_box'])
            vd = VehicleDetection(
                detection_id=vd_data['detection_id'],
                vehicle_type=VehicleType(vd_data['vehicle_type']),
                confidence=vd_data['confidence'],
                bounding_box=bbox,
                timestamp=vd_data['timestamp'],
                additional_metadata=vd_data.get('additional_metadata')
            )
            vehicle_detections.append(vd)
        
        # Convert sky analysis
        sky_data = data['sky_analysis']
        sky_analysis = SkyAnalysis(
            analysis_id=sky_data['analysis_id'],
            condition=SkyCondition(sky_data['condition']),
            confidence=sky_data['confidence'],
            timestamp=sky_data['timestamp'],
            light_level=sky_data.get('light_level'),
            cloud_coverage=sky_data.get('cloud_coverage'),
            additional_metadata=sky_data.get('additional_metadata')
        )
        
        return ImageAnalysisResult(
            image_id=data['image_id'],
            image_path=data['image_path'],
            timestamp=data['timestamp'],
            trigger_source=data['trigger_source'],
            vehicle_detections=vehicle_detections,
            sky_analysis=sky_analysis,
            processing_time_ms=data['processing_time_ms'],
            image_metadata=data.get('image_metadata')
        )
    
    @staticmethod
    def _deserialize_consolidated_data(data: Dict) -> ConsolidatedImageData:
        """Deserialize consolidated data from JSON"""
        image_analysis = RedisDataManager._deserialize_image_analysis(data['image_analysis'])
        
        return ConsolidatedImageData(
            consolidation_id=data['consolidation_id'],
            timestamp=data['timestamp'],
            image_analysis=image_analysis,
            weather_data=data.get('weather_data'),
            system_metrics=data.get('system_metrics'),
            additional_context=data.get('additional_context')
        )

# Example usage and testing functions
def example_usage():
    """Example of how to use the Redis data models"""
    import redis
    
    # Create Redis connection (adjust host/port as needed)
    r = redis.Redis(host='localhost', port=6379, db=0)
    manager = RedisDataManager(r)
    
    # Example vehicle detection
    bbox = BoundingBox(x=100, y=150, width=200, height=300, confidence=0.95)
    detection = VehicleDetection(
        detection_id="det_123",
        vehicle_type=VehicleType.CAR,
        confidence=0.92,
        bounding_box=bbox,
        timestamp=time.time()
    )
    
    # Example sky analysis
    sky = SkyAnalysis(
        analysis_id="sky_456",
        condition=SkyCondition.PARTLY_CLOUDY,
        confidence=0.88,
        timestamp=time.time(),
        light_level=0.7,
        cloud_coverage=0.3
    )
    
    # Create complete image analysis result
    result = ImageAnalysisResult(
        image_id="img_789",
        image_path="/path/to/image.jpg",
        timestamp=time.time(),
        trigger_source="radar",
        vehicle_detections=[detection],
        sky_analysis=sky,
        processing_time_ms=150.5
    )
    
    # Store in Redis
    manager.store_image_analysis(result)
    print(f"Stored image analysis: {result.image_id}")
    
    # Retrieve and verify
    retrieved = manager.get_image_analysis(result.image_id)
    print(f"Retrieved: {retrieved.image_id if retrieved else 'None'}")

if __name__ == "__main__":
    example_usage()