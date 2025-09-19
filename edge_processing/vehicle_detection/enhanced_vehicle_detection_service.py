#!/usr/bin/env python3
"""
Enhanced Vehicle Detection Service with Redis Integration
Extends the original vehicle detection service with Redis storage and improved classification

Features:
- Enhanced vehicle type classification (pedestrians, bicycles, motorcycles, cars, trucks, etc.)
- Redis integration for storing detection results and image paths
- Improved detection pipeline with image analysis triggering
- Performance metrics and statistics
"""

import cv2
import numpy as np
import time
import logging
import os
import uuid
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, asdict

# Import original vehicle detection service
try:
    from .vehicle_detection_service import VehicleDetectionService as OriginalVehicleDetectionService
    from .vehicle_detection_service import VehicleDetection as OriginalVehicleDetection
    ORIGINAL_SERVICE_AVAILABLE = True
except ImportError:
    try:
        from vehicle_detection_service import VehicleDetectionService as OriginalVehicleDetectionService
        from vehicle_detection_service import VehicleDetection as OriginalVehicleDetection
        ORIGINAL_SERVICE_AVAILABLE = True
    except ImportError:
        ORIGINAL_SERVICE_AVAILABLE = False
        logging.warning("Original vehicle detection service not available")

# Redis and data models
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.warning("Redis not available - vehicle detection will work in standalone mode")

# Import our Redis models
try:
    from ..redis_models import (
        VehicleDetection, VehicleType, BoundingBox, RedisDataManager, RedisKeys
    )
    MODELS_AVAILABLE = True
except ImportError:
    try:
        from redis_models import (
            VehicleDetection, VehicleType, BoundingBox, RedisDataManager, RedisKeys
        )
        MODELS_AVAILABLE = True
    except ImportError:
        MODELS_AVAILABLE = False
        logging.warning("Redis models not available - using fallback data structures")

logger = logging.getLogger(__name__)

class EnhancedVehicleDetectionService:
    """
    Enhanced vehicle detection service with Redis integration
    Extends original functionality with improved classification and data storage
    """
    
    def __init__(self,
                 redis_host: str = "localhost",
                 redis_port: int = 6379,
                 redis_db: int = 0,
                 enable_redis: bool = True,
                 confidence_threshold: float = 0.5,
                 **kwargs):
        
        self.redis_enabled = enable_redis and REDIS_AVAILABLE and MODELS_AVAILABLE
        self.redis_manager = None
        self.confidence_threshold = confidence_threshold
        
        # Initialize Redis connection if available
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
                self.redis_client.ping()  # Test connection
                self.redis_manager = RedisDataManager(self.redis_client)
                logger.info(f"Enhanced vehicle detection connected to Redis: {redis_host}:{redis_port}")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}. Running in standalone mode.")
                self.redis_enabled = False
        
        # Initialize original vehicle detection service if available
        self.original_service = None
        if ORIGINAL_SERVICE_AVAILABLE:
            try:
                self.original_service = OriginalVehicleDetectionService(**kwargs)
                logger.info("Original vehicle detection service initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize original service: {e}")
        
        # Enhanced vehicle type mapping (COCO + custom classes)
        self.vehicle_type_mapping = {
            # COCO standard classes
            1: VehicleType.PEDESTRIAN,  # person
            2: VehicleType.BICYCLE,     # bicycle
            3: VehicleType.CAR,         # car
            4: VehicleType.MOTORCYCLE,  # motorcycle
            6: VehicleType.BUS,         # bus
            7: VehicleType.TRUCK,       # truck
            
            # Extended classifications
            5: VehicleType.CAR,         # airplane (misclassified as car)
            8: VehicleType.TRUCK,       # boat (edge case)
            
            # Custom mappings for better classification
            0: VehicleType.UNKNOWN,     # background/unknown
        }
        
        # Performance tracking
        self.total_detections = 0
        self.total_images_processed = 0
        self.avg_processing_time = 0.0
        self.vehicle_counts = {vtype: 0 for vtype in VehicleType}
        
        logger.info("Enhanced Vehicle Detection Service initialized")
    
    def analyze_image(self, image_path: str, image_id: Optional[str] = None, trigger_source: str = "manual") -> Optional[Dict]:
        """
        Analyze an image for vehicle detections with Redis storage
        
        Args:
            image_path: Path to the image file
            image_id: Optional image identifier
            trigger_source: Source that triggered the analysis
            
        Returns:
            Dictionary with detection results or None if analysis fails
        """
        start_time = time.time()
        
        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return None
        
        try:
            # Load and validate image
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"Failed to load image: {image_path}")
                return None
            
            # Perform vehicle detection
            detections = self._detect_vehicles(image, image_path)
            
            # Calculate processing time
            processing_time = (time.time() - start_time) * 1000
            
            # Create result data
            result_data = {
                "image_id": image_id or f"img_{int(time.time())}",
                "image_path": image_path,
                "timestamp": time.time(),
                "trigger_source": trigger_source,
                "vehicle_detections": detections,
                "processing_time_ms": processing_time,
                "detection_count": len(detections),
                "image_metadata": {
                    "image_size": f"{image.shape[1]}x{image.shape[0]}",
                    "confidence_threshold": self.confidence_threshold,
                    "detection_version": "2.0"
                }
            }
            
            # Store in Redis if available
            if self.redis_enabled and MODELS_AVAILABLE:
                try:
                    # Store individual detections
                    for detection_data in detections:
                        detection = self._create_redis_detection(detection_data, result_data["image_id"])
                        self.redis_manager.store_vehicle_detection(detection, result_data["image_id"])
                        
                        # Update statistics
                        self.redis_manager.increment_vehicle_count(detection.vehicle_type)
                    
                    logger.info(f"Stored {len(detections)} vehicle detections in Redis")
                except Exception as e:
                    logger.warning(f"Failed to store detections in Redis: {e}")
            
            # Update performance metrics
            self._update_performance_metrics(processing_time, len(detections))
            
            logger.info(f"Vehicle detection completed: {len(detections)} vehicles found "
                       f"(processing: {processing_time:.1f}ms)")
            
            return result_data
            
        except Exception as e:
            logger.error(f"Vehicle detection failed for {image_path}: {e}")
            return None
    
    def _detect_vehicles(self, image: np.ndarray, image_path: str) -> List[Dict]:
        """
        Perform vehicle detection on image
        
        Args:
            image: OpenCV image array
            image_path: Path to the image file (for original service)
            
        Returns:
            List of detection dictionaries
        """
        detections = []
        
        if self.original_service:
            # Use original service for detection
            try:
                # The original service expects to work with camera frames
                # We'll adapt it to work with static images
                original_detections = self._detect_with_original_service(image)
                
                for det in original_detections:
                    detection_dict = {
                        "detection_id": str(uuid.uuid4()),
                        "vehicle_type": self._enhance_vehicle_classification(det.vehicle_type, det.bbox, image),
                        "confidence": det.confidence,
                        "bounding_box": {
                            "x": det.bbox[0],
                            "y": det.bbox[1],
                            "width": det.bbox[2],
                            "height": det.bbox[3]
                        },
                        "timestamp": time.time(),
                        "additional_metadata": {
                            "original_type": det.vehicle_type,
                            "frame_id": getattr(det, 'frame_id', 0)
                        }
                    }
                    detections.append(detection_dict)
                    
            except Exception as e:
                logger.error(f"Original service detection failed: {e}")
                # Fall back to simple detection
                detections = self._simple_vehicle_detection(image)
        else:
            # Use fallback detection method
            detections = self._simple_vehicle_detection(image)
        
        return detections
    
    def _detect_with_original_service(self, image: np.ndarray) -> List:
        """Use original service for detection (adapted for static images)"""
        # This is a simplified adapter - in practice you might need to
        # modify the original service to accept static images
        
        # For now, return empty list as placeholder
        # The original service is designed for real-time camera feeds
        logger.warning("Original service detection not implemented for static images")
        return []
    
    def _simple_vehicle_detection(self, image: np.ndarray) -> List[Dict]:
        """
        Simple fallback vehicle detection using OpenCV
        This is a basic implementation for when the original service is unavailable
        """
        detections = []
        
        try:
            # Use a simple background subtraction or edge detection approach
            # This is a placeholder implementation
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Simple blob detection as placeholder
            # In practice, you'd use a proper ML model here
            blur = cv2.GaussianBlur(gray, (21, 21), 0)
            thresh = cv2.threshold(blur, 60, 255, cv2.THRESH_BINARY)[1]
            
            # Find contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 5000:  # Minimum area threshold
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # Simple aspect ratio check for vehicle-like shapes
                    aspect_ratio = w / h
                    if 0.5 <= aspect_ratio <= 3.0:
                        detection = {
                            "detection_id": str(uuid.uuid4()),
                            "vehicle_type": VehicleType.UNKNOWN.value,
                            "confidence": 0.6,  # Lower confidence for simple detection
                            "bounding_box": {
                                "x": int(x),
                                "y": int(y),
                                "width": int(w),
                                "height": int(h)
                            },
                            "timestamp": time.time(),
                            "additional_metadata": {
                                "detection_method": "simple_opencv",
                                "contour_area": float(area),
                                "aspect_ratio": float(aspect_ratio)
                            }
                        }
                        detections.append(detection)
            
        except Exception as e:
            logger.error(f"Simple vehicle detection failed: {e}")
        
        return detections
    
    def _enhance_vehicle_classification(self, original_type: str, bbox: Tuple, image: np.ndarray) -> str:
        """
        Enhance vehicle type classification using additional analysis
        
        Args:
            original_type: Original classification from detection
            bbox: Bounding box coordinates
            image: Original image
            
        Returns:
            Enhanced vehicle type classification
        """
        try:
            # Extract region of interest
            x, y, w, h = bbox
            roi = image[y:y+h, x:x+w]
            
            if roi.size == 0:
                return original_type
            
            # Analyze size and aspect ratio for better classification
            aspect_ratio = w / h
            area = w * h
            
            # Size-based classification enhancement
            if area < 2000:  # Small objects
                if aspect_ratio > 0.3 and aspect_ratio < 0.8:
                    return VehicleType.PEDESTRIAN.value
                elif aspect_ratio > 1.2:
                    return VehicleType.BICYCLE.value
            elif area > 50000:  # Large objects
                if aspect_ratio > 2.0:
                    return VehicleType.TRUCK.value
                elif aspect_ratio > 1.5:
                    return VehicleType.BUS.value
            
            # Color analysis for additional classification hints
            avg_color = np.mean(roi, axis=(0, 1))
            brightness = np.mean(avg_color)
            
            # Use original type as fallback with potential enhancement
            enhanced_type = original_type
            
            # Map common vehicle types to our enhanced enum
            type_mapping = {
                "car": VehicleType.CAR.value,
                "truck": VehicleType.TRUCK.value,
                "bus": VehicleType.BUS.value,
                "motorcycle": VehicleType.MOTORCYCLE.value,
                "bicycle": VehicleType.BICYCLE.value,
                "person": VehicleType.PEDESTRIAN.value,
                "vehicle": VehicleType.CAR.value,  # Default vehicle -> car
            }
            
            enhanced_type = type_mapping.get(original_type.lower(), VehicleType.UNKNOWN.value)
            
            return enhanced_type
            
        except Exception as e:
            logger.warning(f"Vehicle classification enhancement failed: {e}")
            return original_type
    
    def _create_redis_detection(self, detection_data: Dict, image_id: str) -> 'VehicleDetection':
        """Create Redis VehicleDetection object from detection data"""
        if not MODELS_AVAILABLE:
            raise ValueError("Redis models not available")
        
        bbox = BoundingBox(
            x=detection_data["bounding_box"]["x"],
            y=detection_data["bounding_box"]["y"],
            width=detection_data["bounding_box"]["width"],
            height=detection_data["bounding_box"]["height"],
            confidence=detection_data["confidence"]
        )
        
        return VehicleDetection(
            detection_id=detection_data["detection_id"],
            vehicle_type=VehicleType(detection_data["vehicle_type"]),
            confidence=detection_data["confidence"],
            bounding_box=bbox,
            timestamp=detection_data["timestamp"],
            additional_metadata=detection_data.get("additional_metadata")
        )
    
    def _update_performance_metrics(self, processing_time: float, detection_count: int):
        """Update internal performance tracking"""
        self.total_images_processed += 1
        self.total_detections += detection_count
        self.avg_processing_time = (
            (self.avg_processing_time * (self.total_images_processed - 1) + processing_time) /
            self.total_images_processed
        )
        
        # Update service status in Redis
        if self.redis_enabled:
            try:
                status = {
                    "service": "enhanced_vehicle_detection",
                    "status": "running",
                    "total_images_processed": self.total_images_processed,
                    "total_detections": self.total_detections,
                    "avg_processing_time_ms": self.avg_processing_time,
                    "last_detection": time.time()
                }
                self.redis_manager.update_service_status("vehicle_service", status)
            except Exception as e:
                logger.warning(f"Failed to update service status: {e}")
    
    def get_detections_by_image_id(self, image_id: str) -> List[Dict]:
        """Retrieve vehicle detections for a specific image"""
        if not self.redis_enabled:
            logger.warning("Redis not available - cannot retrieve stored detections")
            return []
        
        try:
            key = RedisKeys.format_key(RedisKeys.VEHICLE_DETECTIONS_BY_IMAGE, image_id=image_id)
            detection_ids = self.redis_client.smembers(key)
            
            detections = []
            for detection_id in detection_ids:
                detection_key = RedisKeys.format_key(RedisKeys.VEHICLE_DETECTION, detection_id=detection_id)
                data = self.redis_client.get(detection_key)
                if data:
                    detections.append(json.loads(data))
            
            return detections
        except Exception as e:
            logger.error(f"Failed to retrieve detections for image {image_id}: {e}")
            return []
    
    def get_recent_detections(self, limit: int = 10) -> List[Dict]:
        """Get recent vehicle detections"""
        # This would require maintaining a sorted set of recent detections
        # For now, return empty list as placeholder
        return []
    
    def cleanup(self):
        """Cleanup resources"""
        if self.original_service and hasattr(self.original_service, 'cleanup'):
            self.original_service.cleanup()
        
        if self.redis_enabled and hasattr(self, 'redis_client'):
            try:
                self.redis_client.close()
                logger.info("Enhanced vehicle detection Redis connection closed")
            except Exception as e:
                logger.warning(f"Error closing Redis connection: {e}")

def analyze_image_standalone(image_path: str) -> Optional[Dict]:
    """
    Standalone function to analyze a single image
    Useful for testing and manual analysis
    """
    service = EnhancedVehicleDetectionService(enable_redis=False)
    return service.analyze_image(image_path)

def main():
    """Main function for testing the enhanced vehicle detection service"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Vehicle Detection Service")
    parser.add_argument("--image", type=str, help="Path to image for analysis")
    parser.add_argument("--redis-host", type=str, default="localhost", help="Redis host")
    parser.add_argument("--redis-port", type=int, default=6379, help="Redis port")
    parser.add_argument("--no-redis", action="store_true", help="Disable Redis integration")
    parser.add_argument("--confidence", type=float, default=0.5, help="Detection confidence threshold")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize service
    service = EnhancedVehicleDetectionService(
        redis_host=args.redis_host,
        redis_port=args.redis_port,
        enable_redis=not args.no_redis,
        confidence_threshold=args.confidence
    )
    
    try:
        if args.image:
            # Analyze single image
            result = service.analyze_image(args.image)
            if result:
                print(f"\nVehicle Detection Results:")
                print(f"Detections: {result['detection_count']}")
                print(f"Processing Time: {result['processing_time_ms']:.1f}ms")
                for i, detection in enumerate(result['vehicle_detections']):
                    print(f"  {i+1}. {detection['vehicle_type']} "
                          f"(confidence: {detection['confidence']:.2f})")
            else:
                print("Detection failed")
        else:
            print("Enhanced Vehicle Detection Service is running. Use --image to analyze a specific image.")
    
    finally:
        service.cleanup()

if __name__ == "__main__":
    main()