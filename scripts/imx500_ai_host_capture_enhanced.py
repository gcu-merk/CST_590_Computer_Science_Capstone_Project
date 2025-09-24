#!/usr/bin/env python3
"""
IMX500 AI-Enabled Host Camera Capture Service - ENHANCED
Leverages Sony IMX500's on-chip AI processing for real-time vehicle detection
WITH CENTRALIZED LOGGING AND CORRELATION TRACKING

This service replaces the traditional rpicam-still approach with picamera2 + IMX500 AI
to utilize the sensor's built-in neural network processor for sub-100ms vehicle detection.

Key Benefits:
- Sub-100ms inference directly on sensor (vs seconds in software)
- Zero CPU usage for AI processing (dedicated AI chip)
- Real-time object detection with 4K image capture
- Outputs both high-resolution images AND AI detection results
- Centralized logging with correlation tracking
- Performance monitoring and error tracking

Architecture:
IMX500 Sensor -> On-Chip AI (Vehicle Detection) -> Host Python Service -> Redis + Shared Volume -> Docker (Sky Analysis Only)
"""

import os
import sys
import time
import json
import signal
import threading
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List
import uuid

# Add edge_processing to path for shared_logging
sys.path.insert(0, str(Path(__file__).parent.parent / "edge_processing"))
from shared_logging import ServiceLogger, CorrelationContext

# IMX500 AI Camera imports
try:
    from picamera2 import Picamera2
    from picamera2.devices.imx500 import IMX500
    PICAMERA2_AVAILABLE = True
except ImportError:
    PICAMERA2_AVAILABLE = False
    print("WARNING: picamera2 not available. Install with: pip install picamera2")

# Redis for real-time data distribution and correlation tracking
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("WARNING: Redis not available. Install with: pip install redis")

# Initialize centralized logging
service_logger = ServiceLogger(
    service_name="imx500-camera-service",
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    log_dir=os.getenv("LOG_DIR", "/mnt/storage/logs/applications"),
    enable_correlation=True
)
logger = service_logger.logger


class IMX500AIHostCapture:
    """
    Enhanced Host service that leverages IMX500's on-chip AI for vehicle detection
    WITH centralized logging and correlation tracking
    """
    
    def __init__(self,
                 capture_dir: str = "/mnt/storage/camera_capture",
                 ai_model_path: str = "/usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk",
                 capture_interval: float = 1.0,
                 confidence_threshold: float = 0.5,
                 max_images: int = 100,
                 redis_host: str = "localhost",
                 redis_port: int = 6379,
                 street_roi: dict = None,
                 enable_radar_gpio: bool = True):
        
        if not PICAMERA2_AVAILABLE:
            logger.error("picamera2 not available - required for IMX500 AI processing")
            raise RuntimeError("picamera2 not available - required for IMX500 AI processing")
        
        self.capture_dir = Path(capture_dir)
        self.ai_model_path = ai_model_path
        self.capture_interval = capture_interval
        self.confidence_threshold = confidence_threshold
        self.max_images = max_images
        
        # Street Region of Interest (ROI) for filtering out parked cars in driveways
        # and cars on cross street at top of image
        # Default ROI covers the center 70% horizontally and excludes top cross street
        self.street_roi = street_roi or {
            "x_start": 0.15,  # 15% from left edge
            "x_end": 0.85,    # 85% from left edge (center 70%)
            "y_start": 0.5,   # 50% from top (exclude cross street at top)
            "y_end": 0.9      # 90% from top (exclude sky, include main street only)
        }
        
        # Radar GPIO Integration
        self.enable_radar_gpio = enable_radar_gpio
        self.radar_gpio_pins = {
            "host_interrupt": 23,  # Orange wire - Host interrupt from radar
            "reset": 24,           # Yellow wire - Reset radar
            "low_alert": 5,        # Blue wire - Low speed/range alert (Pin 29)
            "high_alert": 6        # Purple wire - High speed/range alert (Pin 31)
        }
        self.radar_gpio_initialized = False
        
        # Radar-triggered capture mode
        self.radar_triggered_mode = False
        self.radar_last_trigger = 0
        
        # Directory structure
        self.live_dir = self.capture_dir / "live"
        self.ai_results_dir = self.capture_dir / "ai_results"
        self.metadata_dir = self.capture_dir / "metadata"
        
        # Initialize directories
        for dir_path in [self.live_dir, self.ai_results_dir, self.metadata_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Camera and AI setup
        self.camera = None
        self.imx500 = None
        self.running = False
        
        # Redis setup for correlation tracking
        self.redis_client = None
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
                self.redis_client.ping()
                logger.info("Connected to Redis for correlation tracking", extra={
                    "redis_host": redis_host,
                    "redis_port": redis_port,
                    "business_event": "redis_connection_established"
                })
            except Exception as e:
                logger.warning("Redis connection failed - continuing without correlation", extra={
                    "error": str(e),
                    "redis_host": redis_host,
                    "redis_port": redis_port
                })
                self.redis_client = None
        
        # Vehicle class mapping for SSD MobileNetV2 model
        self.vehicle_classes = {
            2: "car",           # COCO class ID 2
            3: "motorcycle",    # COCO class ID 3  
            5: "bus",           # COCO class ID 5
            7: "truck",         # COCO class ID 7
        }
        
        # Performance monitoring
        self.capture_stats = {
            "total_captures": 0,
            "successful_captures": 0,
            "vehicles_detected": 0,
            "avg_inference_time_ms": 0.0,
            "avg_processing_time_ms": 0.0
        }
        
        logger.info("IMX500 AI Host Capture service initialized", extra={
            "business_event": "service_initialization",
            "ai_model_path": self.ai_model_path,
            "confidence_threshold": self.confidence_threshold,
            "capture_interval": self.capture_interval,
            "street_roi": self.street_roi,
            "radar_gpio_enabled": self.enable_radar_gpio
        })
    
    def initialize_camera(self) -> bool:
        """Initialize IMX500 camera with AI model"""
        try:
            # Check if AI model exists
            if not os.path.exists(self.ai_model_path):
                logger.error("AI model file not found", extra={
                    "ai_model_path": self.ai_model_path,
                    "business_event": "initialization_failure",
                    "failure_type": "model_not_found"
                })
                return False
            
            logger.info("Initializing IMX500 AI camera", extra={
                "business_event": "camera_initialization_start",
                "ai_model_path": self.ai_model_path
            })
            
            # Initialize camera
            self.camera = Picamera2()
            
            # Load AI model onto IMX500 sensor
            self.imx500 = IMX500(self.ai_model_path)
            logger.info("AI model loaded successfully onto IMX500 sensor", extra={
                "business_event": "ai_model_loaded",
                "ai_model_path": self.ai_model_path
            })
            
            # Configure camera for high-resolution capture with AI
            config = self.camera.create_still_configuration(
                main={"size": (4056, 3040), "format": "RGB888"},
                controls={"FrameRate": 1.0}  # 1 FPS for high-quality AI processing
            )
            
            self.camera.configure(config)
            
            # Start camera
            self.camera.start()
            
            logger.info("IMX500 camera initialized successfully", extra={
                "business_event": "camera_initialization_success",
                "resolution": "4056x3040",
                "format": "RGB888",
                "frame_rate": 1.0
            })
            
            return True
            
        except Exception as e:
            logger.error("Failed to initialize IMX500 camera", extra={
                "business_event": "camera_initialization_failure",
                "error": str(e),
                "error_type": type(e).__name__,
                "traceback": str(e)
            })
            return False
    
    def capture_with_ai_analysis(self) -> Optional[Dict[str, Any]]:
        """
        Capture image and get AI detection results from IMX500 on-chip processor
        Returns both image data and vehicle detection results
        """
        try:
            start_time = time.time()
            timestamp = datetime.now()
            
            # Generate unique IDs
            image_id = f"img_{int(timestamp.timestamp())}"
            capture_id = str(uuid.uuid4())
            
            # Set correlation context for this capture
            with CorrelationContext.set_correlation_id(capture_id):
                logger.debug("Starting IMX500 capture with AI analysis", extra={
                    "business_event": "capture_start",
                    "image_id": image_id,
                    "capture_id": capture_id
                })
                
                # Capture high-resolution image with AI processing
                capture_start = time.time()
                
                # Capture image array and request metadata with AI results
                image_array = self.camera.capture_array("main")
                metadata = self.camera.capture_metadata()
                
                # Get AI inference results from camera
                ai_outputs = self.imx500.get_outputs(metadata)
                
                capture_time = (time.time() - capture_start) * 1000  # Convert to ms
                
                # Process AI detection results
                detections = self._process_ai_detections(ai_outputs, image_array.shape)
                
                # Calculate inference timing
                inference_time = metadata.get("ai_inference_time_ms", 0) if metadata else 0
                
                # Filter detections by street ROI
                street_detections = self._filter_street_detections(detections, image_array.shape)
                
                # Find primary vehicle (highest confidence * area in street ROI)
                primary_vehicle = self._find_primary_vehicle(street_detections)
                
                # Update performance stats
                self.capture_stats["total_captures"] += 1
                self.capture_stats["successful_captures"] += 1
                if street_detections:
                    self.capture_stats["vehicles_detected"] += len(street_detections)
                
                # Running average for inference time
                current_avg = self.capture_stats["avg_inference_time_ms"]
                total_captures = self.capture_stats["successful_captures"]
                self.capture_stats["avg_inference_time_ms"] = (
                    (current_avg * (total_captures - 1) + inference_time) / total_captures
                )
                
                # Save image if vehicles detected
                image_path = None
                if street_detections:
                    image_filename = f"{timestamp.strftime('%Y%m%d_%H%M%S')}_{image_id}.jpg"
                    image_path = self.live_dir / image_filename
                    
                    # Save high-quality image
                    self.camera.capture_file(str(image_path))
                
                # Create result package
                result_package = {
                    "timestamp": timestamp.isoformat(),
                    "image_id": image_id,
                    "capture_id": capture_id,
                    "image_path": str(image_path) if image_path else None,
                    "ai_results": {
                        "detection_count": len(street_detections),
                        "street_detection_count": len(street_detections),
                        "total_detection_count": len(detections),
                        "detections": street_detections,
                        "primary_vehicle": primary_vehicle,
                        "inference_time_ms": inference_time,
                        "capture_time_ms": capture_time,
                        "confidence_threshold": self.confidence_threshold,
                        "street_roi": self.street_roi
                    },
                    "metadata": {
                        "image_shape": image_array.shape,
                        "model_path": self.ai_model_path,
                        "camera_settings": metadata if metadata else {}
                    }
                }
                
                # Log detection results with performance metrics
                if street_detections:
                    logger.info("Vehicle detection completed", extra={
                        "business_event": "vehicle_detection_success",
                        "image_id": image_id,
                        "capture_id": capture_id,
                        "vehicle_count": len(street_detections),
                        "primary_vehicle_type": primary_vehicle.get("vehicle_type") if primary_vehicle else None,
                        "inference_time_ms": inference_time,
                        "capture_time_ms": capture_time,
                        "total_processing_time_ms": (time.time() - start_time) * 1000,
                        "image_saved": image_path is not None
                    })
                else:
                    logger.debug("No vehicles detected in street ROI", extra={
                        "business_event": "no_vehicles_detected",
                        "image_id": image_id,
                        "capture_id": capture_id,
                        "total_detections": len(detections),
                        "inference_time_ms": inference_time
                    })
                
                # Publish results to Redis with correlation context
                if self.redis_client:
                    self._publish_ai_results(result_package)
                
                return result_package
                
        except Exception as e:
            self.capture_stats["total_captures"] += 1
            logger.error("Capture with AI analysis failed", extra={
                "business_event": "capture_failure",
                "error": str(e),
                "error_type": type(e).__name__,
                "capture_id": capture_id if 'capture_id' in locals() else "unknown"
            })
            return None
    
    def _process_ai_detections(self, ai_outputs: List, image_shape: tuple) -> List[Dict[str, Any]]:
        """Process raw AI detection outputs from IMX500"""
        detections = []
        
        if not ai_outputs:
            return detections
        
        try:
            # IMX500 SSD MobileNetV2 output format: [boxes, scores, classes]
            boxes = ai_outputs[0] if len(ai_outputs) > 0 else []
            scores = ai_outputs[1] if len(ai_outputs) > 1 else []
            classes = ai_outputs[2] if len(ai_outputs) > 2 else []
            
            height, width = image_shape[:2]
            
            for i in range(len(boxes)):
                score = scores[i]
                class_id = int(classes[i])
                
                # Filter by confidence and vehicle classes
                if score >= self.confidence_threshold and class_id in self.vehicle_classes:
                    box = boxes[i]
                    
                    # Convert normalized coordinates to pixel coordinates
                    x1, y1, x2, y2 = box
                    x1_px = int(x1 * width)
                    y1_px = int(y1 * height)
                    x2_px = int(x2 * width)
                    y2_px = int(y2 * height)
                    
                    # Calculate center and area
                    center_x = (x1_px + x2_px) // 2
                    center_y = (y1_px + y2_px) // 2
                    area = (x2_px - x1_px) * (y2_px - y1_px)
                    
                    detection = {
                        "vehicle_type": self.vehicle_classes[class_id],
                        "confidence": float(score),
                        "bbox": {
                            "x1": x1_px, "y1": y1_px,
                            "x2": x2_px, "y2": y2_px,
                            "center_x": center_x, "center_y": center_y,
                            "width": x2_px - x1_px,
                            "height": y2_px - y1_px,
                            "area": area
                        },
                        "normalized_coords": {
                            "x1": float(x1), "y1": float(y1),
                            "x2": float(x2), "y2": float(y2)
                        }
                    }
                    
                    detections.append(detection)
            
            logger.debug("AI detections processed", extra={
                "total_raw_detections": len(boxes) if boxes else 0,
                "filtered_detections": len(detections),
                "confidence_threshold": self.confidence_threshold
            })
            
        except Exception as e:
            logger.error("Failed to process AI detections", extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "ai_outputs_length": len(ai_outputs) if ai_outputs else 0
            })
        
        return detections
    
    def _filter_street_detections(self, detections: List[Dict], image_shape: tuple) -> List[Dict]:
        """Filter detections to only include vehicles in street ROI"""
        height, width = image_shape[:2]
        
        # Convert ROI percentages to pixel coordinates
        roi_x1 = int(self.street_roi["x_start"] * width)
        roi_x2 = int(self.street_roi["x_end"] * width)
        roi_y1 = int(self.street_roi["y_start"] * height)
        roi_y2 = int(self.street_roi["y_end"] * height)
        
        street_detections = []
        
        for detection in detections:
            center_x = detection["bbox"]["center_x"]
            center_y = detection["bbox"]["center_y"]
            
            # Check if vehicle center is within street ROI
            if self._is_in_street_roi(center_x, center_y, roi_x1, roi_x2, roi_y1, roi_y2):
                # Add ROI info to detection
                detection["in_street_roi"] = True
                street_detections.append(detection)
        
        return street_detections
    
    def _is_in_street_roi(self, center_x: int, center_y: int, 
                          roi_x1: int, roi_x2: int, roi_y1: int, roi_y2: int) -> bool:
        """Check if vehicle center point is within the street region of interest"""
        return (roi_x1 <= center_x <= roi_x2 and roi_y1 <= center_y <= roi_y2)
    
    def _find_primary_vehicle(self, detections: List[Dict]) -> Optional[Dict]:
        """Find the primary vehicle (highest confidence * area)"""
        if not detections:
            return None
        
        # Score by confidence * area (normalized by image area)
        best_vehicle = None
        best_score = 0
        
        for detection in detections:
            # Use confidence * area as primary vehicle metric
            score = detection["confidence"] * detection["bbox"]["area"]
            
            if score > best_score:
                best_score = score
                best_vehicle = detection
        
        return best_vehicle
    
    def _publish_ai_results(self, result_package: Dict[str, Any]):
        """Publish AI results to Redis for correlation with radar data"""
        try:
            if not self.redis_client:
                return
            
            # Extract correlation context
            correlation_id = CorrelationContext.get_correlation_id()
            
            # Check for related radar events
            radar_correlation = None
            if correlation_id:
                # Look for recent radar detection events that might correlate
                radar_key = f"radar_event:{correlation_id}"
                radar_data = self.redis_client.get(radar_key)
                if radar_data:
                    try:
                        radar_correlation = json.loads(radar_data)
                        logger.info("Found correlated radar event", extra={
                            "business_event": "radar_camera_correlation",
                            "correlation_id": correlation_id,
                            "radar_detection_time": radar_correlation.get("timestamp"),
                            "camera_capture_time": result_package["timestamp"]
                        })
                    except json.JSONDecodeError:
                        pass
            
            # Prepare correlation data
            correlation_data = {
                "service": "imx500-camera",
                "timestamp": result_package["timestamp"],
                "correlation_id": correlation_id,
                "event_type": "camera_detection",
                "vehicle_count": result_package["ai_results"]["detection_count"],
                "primary_vehicle": result_package["ai_results"]["primary_vehicle"],
                "radar_correlation": radar_correlation,
                "performance_metrics": {
                    "inference_time_ms": result_package["ai_results"]["inference_time_ms"],
                    "capture_time_ms": result_package["ai_results"]["capture_time_ms"]
                }
            }
            
            # Publish camera results
            camera_key = f"camera_detection:{result_package['capture_id']}"
            self.redis_client.setex(
                camera_key, 
                300,  # 5 minute TTL
                json.dumps(result_package)
            )
            
            # Publish correlation event
            correlation_key = f"correlation_event:{correlation_id or result_package['capture_id']}"
            self.redis_client.setex(
                correlation_key,
                300,  # 5 minute TTL
                json.dumps(correlation_data)
            )
            
            # Publish to general camera channel for real-time processing
            self.redis_client.publish("camera_detections", json.dumps(result_package))
            
            logger.debug("AI results published to Redis", extra={
                "business_event": "redis_publish_success",
                "capture_id": result_package["capture_id"],
                "correlation_id": correlation_id,
                "vehicle_count": result_package["ai_results"]["detection_count"]
            })
            
        except Exception as e:
            logger.warning("Failed to publish AI results to Redis", extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "capture_id": result_package.get("capture_id", "unknown")
            })
    
    def run(self):
        """Main capture loop using IMX500 on-chip AI"""
        if not self.initialize_camera():
            logger.error("Failed to initialize camera - cannot start capture service", extra={
                "business_event": "service_startup_failure",
                "failure_reason": "camera_initialization_failed"
            })
            return False
        
        self.running = True
        logger.info("IMX500 AI capture service started", extra={
            "business_event": "service_started",
            "capture_interval": self.capture_interval,
            "confidence_threshold": self.confidence_threshold,
            "ai_model": self.ai_model_path
        })
        
        try:
            while self.running:
                cycle_start = time.time()
                
                # Capture with AI analysis
                result = self.capture_with_ai_analysis()
                
                # Log periodic performance statistics
                if self.capture_stats["total_captures"] % 60 == 0:  # Every 60 captures
                    self._log_performance_stats()
                
                # Cleanup old files periodically
                if self.capture_stats["total_captures"] % 100 == 0:  # Every 100 captures
                    self._cleanup_old_files()
                
                # Wait for next capture
                elapsed = time.time() - cycle_start
                sleep_time = max(0, self.capture_interval - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            logger.info("Capture service interrupted by user", extra={
                "business_event": "service_shutdown",
                "shutdown_reason": "user_interrupt"
            })
        except Exception as e:
            logger.error("Capture service error", extra={
                "business_event": "service_error",
                "error": str(e),
                "error_type": type(e).__name__
            })
        finally:
            self.stop()
        
        return True
    
    def _log_performance_stats(self):
        """Log performance statistics"""
        stats = self.capture_stats.copy()
        success_rate = (stats["successful_captures"] / stats["total_captures"] * 100) if stats["total_captures"] > 0 else 0
        
        logger.info("Performance statistics", extra={
            "business_event": "performance_report",
            "total_captures": stats["total_captures"],
            "successful_captures": stats["successful_captures"],
            "success_rate_percent": round(success_rate, 2),
            "vehicles_detected": stats["vehicles_detected"],
            "avg_inference_time_ms": round(stats["avg_inference_time_ms"], 2),
            "detection_rate": round(stats["vehicles_detected"] / stats["successful_captures"], 2) if stats["successful_captures"] > 0 else 0
        })
    
    def _cleanup_old_files(self):
        """Remove old images to prevent disk space issues"""
        try:
            # Get all images sorted by modification time
            all_images = []
            for img_path in self.live_dir.glob("*.jpg"):
                all_images.append((img_path.stat().st_mtime, img_path))
            
            all_images.sort(reverse=True)  # Newest first
            
            # Keep only the most recent max_images
            if len(all_images) > self.max_images:
                files_to_remove = all_images[self.max_images:]
                
                for _, img_path in files_to_remove:
                    try:
                        img_path.unlink()
                    except Exception as e:
                        logger.warning("Failed to remove old image", extra={
                            "image_path": str(img_path),
                            "error": str(e)
                        })
                
                logger.info("Cleaned up old images", extra={
                    "business_event": "file_cleanup",
                    "files_removed": len(files_to_remove),
                    "files_retained": self.max_images
                })
                
        except Exception as e:
            logger.warning("File cleanup failed", extra={
                "error": str(e),
                "error_type": type(e).__name__
            })
    
    def stop(self):
        """Stop the capture service"""
        self.running = False
        
        logger.info("Stopping IMX500 capture service", extra={
            "business_event": "service_shutdown_start"
        })
        
        # Clean up GPIO
        if self.radar_gpio_initialized:
            try:
                import RPi.GPIO as GPIO
                GPIO.cleanup()
                logger.info("GPIO cleanup completed")
            except Exception as e:
                logger.warning("GPIO cleanup error", extra={
                    "error": str(e)
                })
        
        if self.camera:
            try:
                self.camera.stop()
                self.camera.close()
                logger.info("IMX500 camera stopped successfully")
            except Exception as e:
                logger.warning("Error stopping camera", extra={
                    "error": str(e)
                })
        
        # Final performance report
        self._log_performance_stats()
        
        logger.info("IMX500 capture service stopped", extra={
            "business_event": "service_shutdown_complete",
            "final_stats": self.capture_stats
        })


# Global service instance for signal handling
capture_service = None


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    global capture_service
    
    logger.info("Received shutdown signal", extra={
        "business_event": "signal_received",
        "signal": signum
    })
    
    if capture_service:
        capture_service.stop()
    sys.exit(0)


def main():
    """Main entry point"""
    global capture_service
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Configuration from environment or defaults
    config = {
        'capture_dir': os.getenv('CAMERA_CAPTURE_DIR', '/mnt/storage/camera_capture'),
        'ai_model_path': os.getenv('IMX500_MODEL_PATH', '/usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk'),
        'capture_interval': float(os.getenv('CAPTURE_INTERVAL', '1.0')),
        'confidence_threshold': float(os.getenv('AI_CONFIDENCE_THRESHOLD', '0.5')),
        'max_images': int(os.getenv('MAX_STORED_IMAGES', '100')),
        'redis_host': os.getenv('REDIS_HOST', 'localhost'),
        'redis_port': int(os.getenv('REDIS_PORT', '6379')),
        'street_roi': {
            'x_start': float(os.getenv('STREET_ROI_X_START', '0.15')),  # 15% from left
            'x_end': float(os.getenv('STREET_ROI_X_END', '0.85')),      # 85% from left  
            'y_start': float(os.getenv('STREET_ROI_Y_START', '0.5')),   # 50% from top (exclude cross street)
            'y_end': float(os.getenv('STREET_ROI_Y_END', '0.9'))        # 90% from top
        }
    }
    
    logger.info("=== IMX500 AI Host Capture Service - Enhanced ===", extra={
        "business_event": "service_startup",
        "config": {
            "capture_dir": config['capture_dir'],
            "ai_model": config['ai_model_path'],
            "confidence_threshold": config['confidence_threshold'],
            "capture_interval": config['capture_interval'],
            "street_roi": config['street_roi']
        }
    })
    
    try:
        capture_service = IMX500AIHostCapture(**config)
        success = capture_service.run()
        return 0 if success else 1
        
    except Exception as e:
        logger.error("Service startup failed", extra={
            "business_event": "service_startup_failure",
            "error": str(e),
            "error_type": type(e).__name__
        })
        return 1


if __name__ == "__main__":
    capture_service = None
    sys.exit(main())