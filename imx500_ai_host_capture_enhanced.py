#!/usr/bin/env python3
"""
IMX500 AI-Enabled Host Camera Capture Service
Leverages Sony IMX500's on-chip AI processing for real-time vehicle detection

This service replaces the traditional rpicam-still approach with picamera2 + IMX500 AI
to utilize the sensor's built-in neural network processor for sub-100ms vehicle detection.

Key Benefits:
- Sub-100ms inference directly on sensor (vs seconds in software)
- Zero CPU usage for AI processing (dedicated AI chip)
- Real-time object detection with 4K image capture
- Outputs both high-resolution images AND AI detection results
- Eliminates need for software-based vehicle detection in Docker

Architecture:
IMX500 Sensor -> On-Chip AI (Vehicle Detection) -> Host Python Service -> Redis + Shared Volume -> Docker (Sky Analysis Only)
"""

import os
import sys
import time
import json
import logging
import signal
import threading
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List
import uuid

# Computer vision imports
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("WARNING: opencv-python not available. Install with: pip install opencv-python")

# IMX500 AI Camera imports
try:
    from picamera2 import Picamera2
    from picamera2.devices.imx500 import IMX500
    PICAMERA2_AVAILABLE = True
except ImportError:
    PICAMERA2_AVAILABLE = False
    print("WARNING: picamera2 not available. Install with: pip install picamera2")

# Redis for real-time data distribution
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("WARNING: Redis not available. Install with: pip install redis")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/tmp/imx500_ai_capture.log')
    ]
)
logger = logging.getLogger(__name__)

class IMX500AIHostCapture:
    """
    Host service that leverages IMX500's on-chip AI for vehicle detection
    Processes both images and AI inference results from the camera sensor
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
                 enable_radar_gpio: bool = True,
                 radar_triggered_mode: bool = False,
                 radar_trigger_channel: str = "traffic_events",
                 radar_min_speed_trigger: float = 2.0):
        
        if not PICAMERA2_AVAILABLE:
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
        self.radar_triggered_mode = radar_triggered_mode
        self.radar_trigger_channel = radar_trigger_channel
        self.radar_min_speed_trigger = radar_min_speed_trigger
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
        
        # Redis setup
        self.redis_client = None
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
                self.redis_client.ping()
                logger.info(f"Connected to Redis at {redis_host}:{redis_port}")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}")
                self.redis_client = None
        
        # Vehicle class mapping for SSD MobileNetV2 model
        self.vehicle_classes = {
            2: "car",           # COCO class ID 2
            3: "motorcycle",    # COCO class ID 3  
            5: "bus",           # COCO class ID 5
            7: "truck",         # COCO class ID 7
        }
        
        logger.info(f"IMX500 AI Host Capture initialized")
        logger.info(f"Model: {self.ai_model_path}")
        logger.info(f"Confidence threshold: {self.confidence_threshold}")
        logger.info(f"Capture interval: {self.capture_interval}s")
    
    def initialize_camera(self) -> bool:
        """Initialize IMX500 camera with AI model"""
        try:
            # Check if AI model exists
            if not os.path.exists(self.ai_model_path):
                logger.error(f"AI model not found: {self.ai_model_path}")
                return False
            
            logger.info("Initializing IMX500 AI camera...")
            
            # Initialize camera
            self.camera = Picamera2()
            
            # Load AI model onto IMX500 sensor
            self.imx500 = IMX500(self.ai_model_path)
            logger.info(f"AI model loaded: {self.ai_model_path}")
            
            # Configure camera for high-resolution capture with AI
            config = self.camera.create_still_configuration(
                main={"size": (4056, 3040), "format": "RGB888"},
                controls={"FrameRate": 1.0}  # 1 FPS for high-quality AI processing
            )
            
            self.camera.configure(config)
            
            # Note: IMX500 threshold parameters are configured at model level
            # Confidence filtering will be applied during result processing
            
            logger.info("Starting camera...")
            self.camera.start()
            
            # Wait for camera to settle
            time.sleep(2)
            
            # Initialize radar GPIO integration if enabled
            if self.enable_radar_gpio:
                self._initialize_radar_gpio()
            
            logger.info("✅ IMX500 AI camera initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize IMX500 camera: {e}")
            return False
    
    def capture_with_ai_analysis(self) -> Optional[Dict[str, Any]]:
        """
        Capture image and get AI detection results from IMX500 on-chip processor
        Returns both image data and vehicle detection results
        """
        try:
            capture_start = time.time()
            timestamp = datetime.now()
            
            # Generate unique IDs
            image_id = f"img_{int(timestamp.timestamp())}"
            capture_id = str(uuid.uuid4())
            
            # Capture high-resolution image with AI processing
            logger.debug("Triggering IMX500 capture with AI...")
            
            # Capture image array and request metadata with AI results
            image_array = self.camera.capture_array("main")
            metadata = self.camera.capture_metadata()
            
            # Analyze image brightness for lighting conditions
            brightness_analysis = self._analyze_image_brightness(image_array)
            
            # Get AI inference results from camera
            ai_outputs = self.imx500.get_outputs(metadata)
            
            capture_time = (time.time() - capture_start) * 1000  # Convert to ms
            
            # Process AI detection results
            detections = self._process_ai_detections(ai_outputs, image_array.shape)
            
            # Save high-resolution image
            filename = f"capture_{timestamp.strftime('%Y%m%d_%H%M%S_%f')[:-3]}.jpg"
            image_path = self.live_dir / filename
            
            # Convert RGB to BGR for OpenCV saving
            import cv2
            image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
            cv2.imwrite(str(image_path), image_bgr, [cv2.IMWRITE_JPEG_QUALITY, 95])
            
            file_size = image_path.stat().st_size
            
            # Create comprehensive result package
            result_package = {
                "capture_info": {
                    "capture_id": capture_id,
                    "image_id": image_id,
                    "timestamp": timestamp.isoformat(),
                    "filename": filename,
                    "file_size": file_size,
                    "resolution": f"{image_array.shape[1]}x{image_array.shape[0]}",
                    "capture_latency_ms": capture_time,
                    "processing_method": "imx500_on_chip_ai"
                },
                "ai_results": {
                    "inference_time_ms": capture_time,  # On-chip inference is included in capture time
                    "model_used": self.ai_model_path,
                    "confidence_threshold": self.confidence_threshold,
                    "detection_count": len(detections),
                    "detections": detections,
                    "primary_vehicle": self._find_primary_vehicle(detections) if detections else None
                },
                "brightness_analysis": brightness_analysis,
                "redis_keys": {
                    "vehicle_keys": [f"vehicle:detection:{det['detection_id']}" for det in detections]
                }
            }
            
            # Save AI results
            ai_results_path = self.ai_results_dir / f"{filename}.json"
            with open(ai_results_path, 'w') as f:
                json.dump(result_package, f, indent=2)
            
            # Save metadata
            metadata_path = self.metadata_dir / f"{filename}.json"
            with open(metadata_path, 'w') as f:
                json.dump(result_package["capture_info"], f, indent=2)
            
            # Publish to Redis for real-time processing
            if self.redis_client:
                self._publish_ai_results(result_package)
            
            logger.info(f"✅ IMX500 AI capture: {filename} ({file_size} bytes, {len(detections)} vehicles, {capture_time:.1f}ms)")
            
            return result_package
            
        except Exception as e:
            logger.error(f"IMX500 AI capture failed: {e}")
            return None
    
    def _analyze_image_brightness(self, image_array: np.ndarray) -> Dict[str, Any]:
        """Analyze image brightness to determine lighting conditions"""
        try:
            # Convert RGB to grayscale for brightness analysis
            if CV2_AVAILABLE and len(image_array.shape) == 3:
                gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
            elif len(image_array.shape) == 3:
                # Fallback: simple RGB to grayscale conversion
                gray = np.dot(image_array[...,:3], [0.299, 0.587, 0.114])
            else:
                gray = image_array
            
            # Calculate brightness metrics
            mean_brightness = np.mean(gray)
            std_brightness = np.std(gray)
            histogram = np.histogram(gray, bins=32, range=(0, 256))[0]
            
            # Calculate percentage of dark pixels (< 32)
            dark_pixels = np.sum(gray < 32) / gray.size * 100
            
            # Calculate percentage of bright pixels (> 224)
            bright_pixels = np.sum(gray > 224) / gray.size * 100
            
            # Determine lighting condition
            if mean_brightness < 30:
                lighting_condition = "very_dark"
            elif mean_brightness < 60:
                lighting_condition = "dark"
            elif mean_brightness < 120:
                lighting_condition = "low_light"
            elif mean_brightness < 180:
                lighting_condition = "normal"
            else:
                lighting_condition = "bright"
            
            # Determine night vision classification
            if mean_brightness < 40 or dark_pixels > 70:
                visibility_status = "low_visibility"
            elif mean_brightness < 60 or dark_pixels > 50:
                visibility_status = "poor_lighting"
            elif std_brightness < 15:  # Very uniform, possibly overexposed or underexposed
                visibility_status = "poor_contrast"
            else:
                visibility_status = "good"
            
            return {
                "mean_brightness": float(mean_brightness),
                "std_brightness": float(std_brightness),
                "dark_pixels_percent": float(dark_pixels),
                "bright_pixels_percent": float(bright_pixels),
                "lighting_condition": lighting_condition,
                "visibility_status": visibility_status,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Brightness analysis failed: {e}")
            return {
                "mean_brightness": 0.0,
                "lighting_condition": "unknown",
                "visibility_status": "analysis_failed",
                "error": str(e)
            }
    
    def _process_ai_detections(self, ai_outputs: List, image_shape: tuple) -> List[Dict[str, Any]]:
        """Process raw AI detection outputs from IMX500"""
        detections = []
        
        if not ai_outputs or len(ai_outputs) < 4:
            return detections
        
        # Debug: Log the actual structure of AI outputs
        logger.debug(f"AI outputs type: {type(ai_outputs)}, length: {len(ai_outputs) if hasattr(ai_outputs, '__len__') else 'N/A'}")
        if ai_outputs:
            logger.debug(f"First output type: {type(ai_outputs[0])}, shape: {getattr(ai_outputs[0], 'shape', 'N/A')}")
            if hasattr(ai_outputs[0], 'shape') and len(ai_outputs[0].shape) > 0:
                logger.debug(f"First output content sample: {ai_outputs[0][:5] if ai_outputs[0].shape[0] > 5 else ai_outputs[0]}")
        
        height, width = image_shape[:2]
        
        # Calculate street ROI boundaries in pixels
        roi_x1 = int(self.street_roi["x_start"] * width)
        roi_x2 = int(self.street_roi["x_end"] * width)
        roi_y1 = int(self.street_roi["y_start"] * height)
        roi_y2 = int(self.street_roi["y_end"] * height)
        
        # IMX500 SSD MobileNet format: [boxes, scores, classes, num_detections]
        try:
            boxes = ai_outputs[0]  # Shape: (N, 4) - normalized coordinates [y1, x1, y2, x2]
            scores = ai_outputs[1] # Shape: (N,) - confidence scores
            classes = ai_outputs[2] # Shape: (N,) - class IDs
            num_detections = int(ai_outputs[3].item()) if hasattr(ai_outputs[3], 'item') else int(ai_outputs[3][0])
            
            logger.debug(f"Boxes shape: {boxes.shape}, Scores shape: {scores.shape}, Classes shape: {classes.shape}, Num detections: {num_detections}")
            
            # Process only valid detections
            for i in range(min(num_detections, len(boxes), len(scores), len(classes))):
                confidence = float(scores[i])
                class_id = int(classes[i])
                
                # Only process vehicle classes above confidence threshold
                if class_id in self.vehicle_classes and confidence >= self.confidence_threshold:
                    # Convert normalized coordinates to pixels
                    # Note: IMX500 often uses [y1, x1, y2, x2] format
                    if boxes.shape[1] == 4:
                        y1, x1, y2, x2 = boxes[i]
                        # Convert to pixel coordinates
                        x1 = int(x1 * width)
                        x2 = int(x2 * width)
                        y1 = int(y1 * height)
                        y2 = int(y2 * height)
                    else:
                        logger.warning(f"Unexpected bbox format for detection {i}: {boxes[i]}")
                        continue
                    
                    # Check if vehicle is in the street ROI (filter out parked cars in driveways)
                    center_x = (x1 + x2) // 2
                    center_y = (y1 + y2) // 2
                    
                    if not self._is_in_street_roi(center_x, center_y, roi_x1, roi_x2, roi_y1, roi_y2):
                        logger.debug(f"Vehicle detection {i} filtered out - outside street ROI (parked car or cross street)")
                        continue
                    
                    detection_data = {
                        "detection_id": f"imx500_{int(time.time())}_{i}",
                        "vehicle_type": self.vehicle_classes[class_id],
                        "confidence": float(confidence),
                        "bounding_box": {
                            "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                            "width": x2 - x1, "height": y2 - y1
                        },
                        "area_pixels": (x2 - x1) * (y2 - y1),
                        "center_point": [center_x, center_y],
                        "class_id": class_id,
                        "inference_source": "imx500_on_chip",
                        "in_street_roi": True,
                        "roi_filtered": "street_traffic_only"
                    }
                    
                    detections.append(detection_data)
                    logger.debug(f"✅ Valid vehicle detection {i}: {self.vehicle_classes[class_id]} confidence={confidence:.2f} bbox=({x1},{y1},{x2},{y2})")
                    
        except Exception as e:
            logger.error(f"Failed to parse IMX500 detection format: {e}")
            
        return detections
    
    def _is_in_street_roi(self, center_x: int, center_y: int, 
                          roi_x1: int, roi_x2: int, roi_y1: int, roi_y2: int) -> bool:
        """Check if vehicle center point is within the street region of interest"""
        return (roi_x1 <= center_x <= roi_x2) and (roi_y1 <= center_y <= roi_y2)
    
    def _find_primary_vehicle(self, detections: List[Dict]) -> Optional[Dict]:
        """Find the primary vehicle (highest confidence * area)"""
        if not detections:
            return None
        
        return max(detections, key=lambda d: d["confidence"] * d["area_pixels"])
    
    def _publish_ai_results(self, result_package: Dict[str, Any]):
        """Publish AI results to Redis for Docker container consumption"""
        if not self.redis_client:
            return
        
        try:
            # Publish vehicle detections
            for detection in result_package["ai_results"]["detections"]:
                detection_key = f"vehicle:detection:{detection['detection_id']}"
                detection_data = {
                    **detection,
                    "timestamp": time.time(),
                    "image_id": result_package["capture_info"]["image_id"],
                    "source": "imx500_host_ai"
                }
                self.redis_client.setex(detection_key, 300, json.dumps(detection_data))  # 5 min TTL

            
            # Publish real-time event
            event_data = {
                "event_type": "imx500_ai_capture",
                "timestamp": time.time(),
                "vehicle_detections": len(result_package["ai_results"]["detections"]),
                "primary_vehicle": result_package["ai_results"]["primary_vehicle"]["vehicle_type"] if result_package["ai_results"]["primary_vehicle"] else None,
                "inference_time_ms": result_package["ai_results"]["inference_time_ms"],
                "image_id": result_package["capture_info"]["image_id"]
            }
            self.redis_client.publish("traffic_events", json.dumps(event_data))
            
            logger.debug(f"Published AI results to Redis: {len(result_package['ai_results']['detections'])} vehicles")
            
        except Exception as e:
            logger.error(f"Failed to publish AI results to Redis: {e}")
    
    def run(self):
        """Main capture loop using IMX500 on-chip AI"""
        if not self.initialize_camera():
            logger.error("Failed to initialize camera - cannot start capture service")
            return False
        
        self.running = True
        
        if self.radar_triggered_mode and self.redis_client:
            logger.info(f"🎯 Starting RADAR-TRIGGERED IMX500 AI capture service")
            logger.info(f"   Listening on Redis channel: {self.radar_trigger_channel}")
            logger.info(f"   Camera requests channel: camera_requests")
            logger.info(f"   Minimum speed trigger: {self.radar_min_speed_trigger} mph")
            return self._run_radar_triggered_mode_with_handshake()
        else:
            logger.info(f"🚗 Starting IMX500 AI capture service (continuous mode, interval: {self.capture_interval}s)")
            return self._run_continuous_mode()
    
    def _run_continuous_mode(self):
        """Original continuous capture mode"""
        try:
            while self.running:
                start_time = time.time()
                
                # Capture with AI analysis
                result = self.capture_with_ai_analysis()
                
                if result:
                    # Log performance metrics
                    vehicle_count = result["ai_results"]["detection_count"]
                    inference_time = result["ai_results"]["inference_time_ms"]
                    
                    if vehicle_count > 0:
                        primary = result["ai_results"]["primary_vehicle"]
                        logger.info(f"🚗 Detected {vehicle_count} vehicles (primary: {primary['vehicle_type'] if primary else 'none'}, {inference_time:.1f}ms)")
                
                # Cleanup old files periodically
                self._cleanup_old_files()
                
                # Wait for next capture
                elapsed = time.time() - start_time
                sleep_time = max(0, self.capture_interval - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            logger.info("Capture service interrupted by user")
        except Exception as e:
            logger.error(f"Capture service error: {e}")
        finally:
            self.stop()
        
        return True
    
    def _run_radar_triggered_mode_with_handshake(self):
        """Enhanced radar-triggered capture mode with camera request handshake"""
        try:
            # Setup dual channel subscription for radar triggers AND camera requests
            pubsub = self.redis_client.pubsub()
            pubsub.subscribe(self.radar_trigger_channel)
            pubsub.subscribe("camera_requests")  # New handshake channel
            
            logger.info(f"✅ Subscribed to radar triggers on '{self.radar_trigger_channel}'")
            logger.info(f"✅ Subscribed to camera requests on 'camera_requests'")
            
            for message in pubsub.listen():
                if not self.running:
                    break
                    
                if message['type'] == 'message':
                    try:
                        data = json.loads(message['data'])
                        channel = message['channel']
                        
                        if channel == self.radar_trigger_channel:
                            # Handle radar trigger (legacy mode)
                            self._handle_radar_trigger(data)
                            
                        elif channel == "camera_requests":
                            # Handle camera processing request (new handshake mode)
                            self._handle_camera_request(data)
                            
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse message from {message['channel']}: {e}")
                    except Exception as e:
                        logger.error(f"Error processing message from {message['channel']}: {e}")
                        
        except Exception as e:
            logger.error(f"Radar triggered mode error: {e}")
        finally:
            self.stop()
            
        return True
    
    def _handle_radar_trigger(self, data: Dict[str, Any]):
        """Handle legacy radar trigger messages"""
        # Check if this is a vehicle detection with sufficient speed
        if (data.get('event_type') == 'vehicle_detection' and 
            data.get('speed_mph', 0) >= self.radar_min_speed_trigger):
            
            speed = data.get('speed_mph', 0)
            detection_id = data.get('detection_id', 'unknown')
            
            logger.info(f"🎯 Radar trigger: {speed:.1f} mph vehicle detected (ID: {detection_id})")
            
            # Trigger immediate IMX500 capture
            result = self.capture_with_ai_analysis()
            if result:
                # Add radar correlation data
                result["trigger_source"] = "radar"
                result["radar_speed_mph"] = speed
                result["radar_detection_id"] = detection_id
                result["correlation_id"] = data.get('correlation_id')
                
                # Log capture completion
                vehicle_count = result["ai_results"]["detection_count"]
                inference_time = result["ai_results"]["inference_time_ms"]
                primary = result["ai_results"]["primary_vehicle"]
                primary_type = primary["vehicle_type"] if primary else "none"
                
                logger.info(f"📸 Radar-triggered capture: {vehicle_count} vehicles detected (primary: {primary_type}, {inference_time:.1f}ms)")
                
                # Also publish to general camera channel for real-time processing
                self.redis_client.publish("camera_detections", json.dumps(result))
    
    def _handle_camera_request(self, request_data: Dict[str, Any]):
        """Handle camera processing request from consolidator (handshake protocol)"""
        
        correlation_id = request_data.get('correlation_id')
        radar_data = request_data.get('radar_data', {})
        request_time = request_data.get('request_timestamp', time.time())
        
        logger.info(f"📨 Camera processing request received for detection {correlation_id}")
        
        try:
            # Trigger immediate IMX500 capture for this specific detection
            result = self.capture_with_ai_analysis()
            
            if result:
                # Extract AI detection results
                ai_results = result.get("ai_results", {})
                vehicle_count = ai_results.get("detection_count", 0)
                inference_time = ai_results.get("inference_time_ms", 0)
                primary = ai_results.get("primary_vehicle")
                
                # Determine vehicle types and handle special cases
                vehicle_types = []
                detection_confidence = 0.0
                
                if vehicle_count > 0 and primary:
                    vehicle_types = [primary.get("vehicle_type", "unknown")]
                    detection_confidence = primary.get("confidence", 0.0)
                    logger.info(f"📸 Camera captured: {vehicle_count} vehicles (primary: {vehicle_types[0]}, confidence: {detection_confidence:.2f})")
                else:
                    # Check for night/poor visibility conditions using brightness analysis
                    brightness_analysis = result.get("brightness_analysis", {})
                    visibility_status = brightness_analysis.get("visibility_status", "unknown")
                    lighting_condition = brightness_analysis.get("lighting_condition", "unknown")
                    mean_brightness = brightness_analysis.get("mean_brightness", 128)
                    
                    if visibility_status == "low_visibility":
                        vehicle_types = ["low_visibility"]
                        logger.info(f"📸 Camera captured: Low visibility detected (brightness: {mean_brightness:.1f}, condition: {lighting_condition})")
                    elif visibility_status == "poor_lighting":
                        vehicle_types = ["poor_lighting"]
                        logger.info(f"📸 Camera captured: Poor lighting conditions (brightness: {mean_brightness:.1f}, condition: {lighting_condition})")
                    elif visibility_status == "poor_contrast":
                        vehicle_types = ["poor_contrast"]
                        logger.info(f"📸 Camera captured: Poor contrast detected (brightness: {mean_brightness:.1f}, condition: {lighting_condition})")
                    else:
                        vehicle_types = ["no_detection"]
                        logger.info(f"📸 Camera captured: No vehicles detected in {lighting_condition} conditions")
                
                # Create response data
                camera_response = {
                    "correlation_id": correlation_id,
                    "status": "completed",
                    "camera_data": {
                        "vehicle_count": vehicle_count,
                        "vehicle_types": vehicle_types,
                        "detection_confidence": detection_confidence,
                        "processing_time": inference_time,
                        "image_metadata": result.get("capture_info", {}),
                        "brightness_analysis": result.get("brightness_analysis", {}),
                        "capture_timestamp": time.time(),
                        "brightness_level": result.get("brightness_analysis", {}).get("mean_brightness", 128)
                    },
                    "response_timestamp": time.time(),
                    "request_processing_time": time.time() - request_time
                }
                
                # Send response back to consolidator
                self.redis_client.publish("camera_responses", json.dumps(camera_response))
                
                logger.info(f"📤 Camera response sent for detection {correlation_id} (vehicles: {vehicle_types})")
                
            else:
                # Capture failed - send error response
                self._send_camera_error_response(correlation_id, "capture_failed", request_time)
                
        except Exception as e:
            logger.error(f"Camera processing failed for {correlation_id}: {e}")
            self._send_camera_error_response(correlation_id, "processing_error", request_time)
    
    def _send_camera_error_response(self, correlation_id: str, error_type: str, request_time: float):
        """Send error response when camera processing fails"""
        
        error_response = {
            "correlation_id": correlation_id,
            "status": "error",
            "camera_data": {
                "vehicle_count": 0,
                "vehicle_types": [f"error_{error_type}"],
                "detection_confidence": 0.0,
                "processing_time": 0.0,
                "image_metadata": {"error": error_type},
                "capture_timestamp": time.time()
            },
            "response_timestamp": time.time(),
            "request_processing_time": time.time() - request_time,
            "error": error_type
        }
        
        self.redis_client.publish("camera_responses", json.dumps(error_response))
        logger.error(f"📤 Camera error response sent for detection {correlation_id}: {error_type}")
    
    def _cleanup_old_files(self):
        """Remove old images to prevent disk space issues"""
        try:
            images = list(self.live_dir.glob("*.jpg"))
            if len(images) > self.max_images:
                images.sort(key=lambda x: x.stat().st_mtime)
                for old_image in images[:-self.max_images]:
                    old_image.unlink()
                    # Also remove associated metadata
                    (self.metadata_dir / f"{old_image.name}.json").unlink(missing_ok=True)
                    (self.ai_results_dir / f"{old_image.name}.json").unlink(missing_ok=True)
        except Exception as e:
            logger.warning(f"Cleanup error: {e}")
    
    def _initialize_radar_gpio(self):
        """Initialize GPIO pins for radar integration"""
        try:
            import RPi.GPIO as GPIO
            
            # Set GPIO mode
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # Setup input pins with pull-up resistors
            GPIO.setup(self.radar_gpio_pins["host_interrupt"], GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.radar_gpio_pins["low_alert"], GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.radar_gpio_pins["high_alert"], GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            # Setup output pin for radar reset
            GPIO.setup(self.radar_gpio_pins["reset"], GPIO.OUT)
            GPIO.output(self.radar_gpio_pins["reset"], GPIO.HIGH)  # Keep radar out of reset
            
            # Add interrupt detection for radar signals
            GPIO.add_event_detect(self.radar_gpio_pins["host_interrupt"], 
                                GPIO.FALLING, callback=self._on_radar_detection, bouncetime=50)
            GPIO.add_event_detect(self.radar_gpio_pins["low_alert"], 
                                GPIO.FALLING, callback=self._on_radar_low_alert, bouncetime=100)
            GPIO.add_event_detect(self.radar_gpio_pins["high_alert"], 
                                GPIO.FALLING, callback=self._on_radar_high_alert, bouncetime=100)
            
            self.radar_gpio_initialized = True
            logger.info("✅ Radar GPIO integration initialized:")
            logger.info(f"   Host Interrupt: GPIO{self.radar_gpio_pins['host_interrupt']} (Orange wire)")
            logger.info(f"   Reset: GPIO{self.radar_gpio_pins['reset']} (Yellow wire)")
            logger.info(f"   Low Alert: GPIO{self.radar_gpio_pins['low_alert']} (Blue wire)")
            logger.info(f"   High Alert: GPIO{self.radar_gpio_pins['high_alert']} (Purple wire)")
            
        except ImportError:
            logger.warning("RPi.GPIO not available - radar GPIO integration disabled")
        except Exception as e:
            logger.error(f"Failed to initialize radar GPIO: {e}")
    
    def _on_radar_detection(self, channel):
        """Handle radar detection interrupt (GPIO23 - Orange wire)"""
        current_time = time.time()
        logger.info(f"🎯 Radar detection interrupt triggered on GPIO{channel}")
        
        # Avoid duplicate triggers within 500ms
        if current_time - self.radar_last_trigger < 0.5:
            return
            
        self.radar_last_trigger = current_time
        self.radar_triggered_mode = True
        
        # Trigger immediate high-priority capture
        try:
            logger.info("📸 Radar-triggered immediate IMX500 capture")
            detection_data = self.capture_with_ai_analysis()
            if detection_data:
                detection_data["trigger_source"] = "radar_interrupt"
                detection_data["radar_trigger_time"] = current_time
                logger.info("✅ Radar-triggered capture completed")
        except Exception as e:
            logger.error(f"Error in radar-triggered capture: {e}")
    
    def _on_radar_low_alert(self, channel):
        """Handle radar low speed/range alert (GPIO5 - Blue wire)"""
        logger.info(f"🐌 Radar LOW ALERT triggered on GPIO{channel} - Slow vehicle detected")
        # Could adjust capture parameters for slow vehicles
        # E.g., increase capture frequency, use higher resolution
    
    def _on_radar_high_alert(self, channel):
        """Handle radar high speed alert (GPIO6 - Purple wire)"""
        logger.info(f"🏎️ Radar HIGH ALERT triggered on GPIO{channel} - Fast vehicle detected")
        # Could trigger rapid capture sequence for fast vehicles
        # E.g., burst mode, track vehicle progression
    
    def radar_reset(self):
        """Reset the radar sensor via GPIO"""
        if not self.radar_gpio_initialized:
            logger.warning("Radar GPIO not initialized")
            return
        
        try:
            import RPi.GPIO as GPIO
            logger.info("🔄 Resetting radar sensor...")
            GPIO.output(self.radar_gpio_pins["reset"], GPIO.LOW)
            time.sleep(0.001)  # 1ms reset pulse
            GPIO.output(self.radar_gpio_pins["reset"], GPIO.HIGH)
            logger.info("✅ Radar reset completed")
        except Exception as e:
            logger.error(f"Failed to reset radar: {e}")
    
    def stop(self):
        """Stop the capture service"""
        self.running = False
        
        # Clean up GPIO
        if self.radar_gpio_initialized:
            try:
                import RPi.GPIO as GPIO
                GPIO.cleanup()
                logger.info("GPIO cleanup completed")
            except Exception as e:
                logger.warning(f"GPIO cleanup error: {e}")
        
        if self.camera:
            try:
                self.camera.stop()
                self.camera.close()
                logger.info("IMX500 camera stopped")
            except Exception as e:
                logger.warning(f"Error stopping camera: {e}")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    global capture_service
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
        },
        'radar_triggered_mode': os.getenv('RADAR_TRIGGERED_MODE', 'false').lower() == 'true',
        'radar_trigger_channel': os.getenv('RADAR_TRIGGER_CHANNEL', 'traffic_events'),
        'radar_min_speed_trigger': float(os.getenv('RADAR_MIN_SPEED_TRIGGER', '2.0'))
    }
    
    logger.info("=== IMX500 AI Host Capture Service ===")
    logger.info(f"Capture directory: {config['capture_dir']}")
    logger.info(f"AI model: {config['ai_model_path']}")
    logger.info(f"Confidence threshold: {config['confidence_threshold']}")
    if config['radar_triggered_mode']:
        logger.info(f"Mode: RADAR-TRIGGERED (channel: {config['radar_trigger_channel']}, min speed: {config['radar_min_speed_trigger']} mph)")
    else:
        logger.info(f"Mode: CONTINUOUS (interval: {config['capture_interval']}s)")
    logger.info(f"Street ROI: {config['street_roi']} (filters out parked cars and cross street)")
    
    try:
        capture_service = IMX500AIHostCapture(**config)
        success = capture_service.run()
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"Service startup failed: {e}")
        return 1

if __name__ == "__main__":
    capture_service = None
    sys.exit(main())