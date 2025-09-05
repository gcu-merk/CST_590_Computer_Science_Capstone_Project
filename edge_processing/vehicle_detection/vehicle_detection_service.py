#!/usr/bin/env python3
"""
Vehicle Detection Service for Raspberry Pi 5
Uses TensorFlow/OpenCV with Sony IMX500 AI Camera for real-time vehicle detection
Optimized for Raspberry Pi 5 with native camera interface
"""


import cv2
import numpy as np
import time
import json
from datetime import datetime
from collections import deque
import threading
import logging
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple

# IMX500 on-sensor AI import
try:
    from picamera2.devices.imx500 import IMX500 as IMX500Device
    IMX500_AVAILABLE = True
except ImportError:
    IMX500_AVAILABLE = False
    logging.warning("IMX500 API not available; on-sensor AI will be disabled.")

# Raspberry Pi specific imports
try:
    from picamera2 import Picamera2
    from picamera2.encoders import H264Encoder
    from picamera2.outputs import FileOutput
    PI_CAMERA_AVAILABLE = True
except ImportError:
    PI_CAMERA_AVAILABLE = False
    logging.warning("picamera2 not available, falling back to OpenCV camera")

# TensorFlow imports with edge optimization
try:
    import tensorflow as tf
    # Try to use TensorFlow Lite for better edge performance
    try:
        import tflite_runtime.interpreter as tflite
        TFLITE_AVAILABLE = True
    except ImportError:
        TFLITE_AVAILABLE = False
except ImportError:
    tf = None
    TFLITE_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class VehicleDetection:
    """Vehicle detection result from AI camera"""
    detection_id: str
    timestamp: float
    bbox: Tuple[int, int, int, int]  # x, y, width, height
    confidence: float
    vehicle_type: str  # car, truck, motorcycle, etc.
    frame_id: int
    
class VehicleDetectionService:
    """
    Core vehicle detection service using Sony IMX500 AI Camera
    Optimized for Raspberry Pi 5 with native camera interface and edge inference
    """
    

    def __init__(self, camera_index=0, model_path=None, use_tflite=True, use_imx500_ai=True, imx500_model_path=None):
        self.camera_index = camera_index
        self.model_path = model_path
        self.use_tflite = use_tflite and TFLITE_AVAILABLE
        self.use_imx500_ai = use_imx500_ai and IMX500_AVAILABLE
        self.imx500_model_path = imx500_model_path or "/usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk"
        self.camera = None
        self.picamera2 = None
        self.model = None
        self.interpreter = None
        self.imx500 = None
        self.is_running = False
        self.detection_buffer = deque(maxlen=100)
        self.frame_count = 0
        # Performance optimization settings
        self.input_size = (640, 640)  # Optimized for edge inference
        self.confidence_threshold = 0.5
        self.nms_threshold = 0.4
        
    def initialize_camera(self):
        """Initialize Sony IMX500 AI Camera using optimal interface"""
        try:
            if PI_CAMERA_AVAILABLE:
                self.picamera2 = Picamera2()
                # Configure for optimal performance
                camera_config = self.picamera2.create_still_configuration(
                    main={"size": (1920, 1080)},
                    lores={"size": self.input_size, "format": "YUV420"}
                )
                self.picamera2.configure(camera_config)
                self.picamera2.start()
                logger.info("Sony IMX500 AI Camera initialized with picamera2")
                # If using IMX500 on-sensor AI, initialize model
                if self.use_imx500_ai:
                    self.imx500 = IMX500Device(self.imx500_model_path)
                    logger.info(f"IMX500 on-sensor AI model loaded: {self.imx500_model_path}")
                return True
            else:
                # Fallback to OpenCV
                self.camera = cv2.VideoCapture(self.camera_index)
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
                self.camera.set(cv2.CAP_PROP_FPS, 30)
                logger.info("Camera initialized with OpenCV (fallback)")
                return True
        except Exception as e:
            logger.error(f"Failed to initialize camera: {e}")
            return False
    
    def load_model(self):
        """Load TensorFlow model with edge optimization"""
        try:
            if self.use_tflite and self.model_path and self.model_path.endswith('.tflite'):
                # Use TensorFlow Lite for better edge performance
                self.interpreter = tflite.Interpreter(model_path=self.model_path)
                self.interpreter.allocate_tensors()
                
                # Get input and output details
                self.input_details = self.interpreter.get_input_details()
                self.output_details = self.interpreter.get_output_details()
                
                logger.info("TensorFlow Lite model loaded for edge inference")
                
            elif tf is not None and self.model_path:
                # Use standard TensorFlow
                self.model = tf.saved_model.load(self.model_path)
                logger.info("TensorFlow model loaded")
                
            else:
                # Use pre-trained model or mock detection
                logger.info("Using built-in vehicle detection (mock for development)")
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False
    
    def capture_frame(self):
        """Capture frame using optimal camera interface"""
    # Temporarily disabled image capture from Pi
    return False, None
    
    def detect_vehicles(self, frame):
        """
        Detect vehicles in a single frame using IMX500 on-sensor AI if enabled, otherwise edge-optimized inference
        Returns list of VehicleDetection objects
        """
        detections = []
        try:
            timestamp = time.time()
            if self.use_imx500_ai and self.imx500 and self.picamera2:
                # Use IMX500 on-sensor AI
                request = self.picamera2.capture_request()
                outputs = self.imx500.get_outputs(request.get_metadata())
                # Parse outputs to VehicleDetection objects
                for i, det in enumerate(outputs or []):
                    # det: dict with keys 'bbox', 'label', 'score'
                    bbox = det.get('bbox', [0,0,0,0])
                    x, y, w, h = bbox if len(bbox) == 4 else (0,0,0,0)
                    detection = VehicleDetection(
                        detection_id=f"imx500_{self.frame_count}_{i}",
                        timestamp=timestamp,
                        bbox=(int(x), int(y), int(w), int(h)),
                        confidence=float(det.get('score', 0.0)),
                        vehicle_type=det.get('label', 'vehicle'),
                        frame_id=self.frame_count
                    )
                    detections.append(detection)
                request.release()
            elif self.interpreter:
                # TensorFlow Lite inference (preferred for edge)
                processed_frame = self._preprocess_frame(frame)
                detections = self._run_tflite_inference(processed_frame, timestamp)
            elif self.model:
                # Standard TensorFlow inference
                processed_frame = self._preprocess_frame(frame)
                detections = self._run_tf_inference(processed_frame, timestamp)
            else:
                # Mock detection for development/testing
                detections = self._run_mock_detection(frame, timestamp)
        except Exception as e:
            logger.error(f"Detection error: {e}")
        return detections
    
    def _preprocess_frame(self, frame):
        """Preprocess frame for model input"""
        # Resize to model input size
        resized = cv2.resize(frame, self.input_size)
        
        # Normalize to [0, 1] range
        normalized = resized.astype(np.float32) / 255.0
        
        # Add batch dimension
        return np.expand_dims(normalized, axis=0)
    
    def _run_tflite_inference(self, processed_frame, timestamp):
        """Run TensorFlow Lite inference (optimized for edge)"""
        detections = []
        
        try:
            # Set input tensor
            self.interpreter.set_tensor(self.input_details[0]['index'], processed_frame)
            
            # Run inference
            self.interpreter.invoke()
            
            # Get output tensors
            boxes = self.interpreter.get_tensor(self.output_details[0]['index'])[0]
            classes = self.interpreter.get_tensor(self.output_details[1]['index'])[0]
            scores = self.interpreter.get_tensor(self.output_details[2]['index'])[0]
            
            # Process detections
            for i in range(len(scores)):
                if scores[i] > self.confidence_threshold:
                    # Convert normalized coordinates to pixel coordinates
                    y1, x1, y2, x2 = boxes[i]
                    x1 = int(x1 * self.input_size[0])
                    y1 = int(y1 * self.input_size[1])
                    x2 = int(x2 * self.input_size[0])
                    y2 = int(y2 * self.input_size[1])
                    
                    detection = VehicleDetection(
                        detection_id=f"det_{self.frame_count}_{i}",
                        timestamp=timestamp,
                        bbox=(x1, y1, x2-x1, y2-y1),
                        confidence=float(scores[i]),
                        vehicle_type=self._get_vehicle_class(int(classes[i])),
                        frame_id=self.frame_count
                    )
                    detections.append(detection)
                    
        except Exception as e:
            logger.error(f"TFLite inference error: {e}")
            
        return detections
    
    def _run_tf_inference(self, processed_frame, timestamp):
        """Run standard TensorFlow inference"""
        detections = []
        
        try:
            # Convert to tensor
            input_tensor = tf.convert_to_tensor(processed_frame)
            
            # Run inference
            # Note: This would need to be adapted to your specific model
            # For now, using mock detection
            detections = self._run_mock_detection(processed_frame[0], timestamp)
            
        except Exception as e:
            logger.error(f"TensorFlow inference error: {e}")
            
        return detections
    
    def _run_mock_detection(self, frame, timestamp):
        """Mock detection for development/testing"""
        detections = []
        
        # Create mock detection for testing
        mock_detection = VehicleDetection(
            detection_id=f"mock_{self.frame_count}_0",
            timestamp=timestamp,
            bbox=(100, 100, 200, 150),
            confidence=0.85,
            vehicle_type='car',
            frame_id=self.frame_count
        )
        detections.append(mock_detection)
        
        return detections
    
    def _get_vehicle_class(self, class_id):
        """Map class ID to vehicle type"""
        # COCO dataset vehicle classes
        vehicle_classes = {
            2: 'car',
            3: 'motorcycle', 
            5: 'bus',
            7: 'truck'
        }
        return vehicle_classes.get(class_id, 'vehicle')
    
    def start_detection(self):
        """Start continuous vehicle detection"""
        if not self.initialize_camera() or not self.load_model():
            return False
            
        self.is_running = True
        detection_thread = threading.Thread(target=self._detection_loop)
        detection_thread.start()
        logger.info("Vehicle detection service started")
        return True
    
    def _detection_loop(self):
        """Main detection loop with optimized frame processing"""
        while self.is_running:
            try:
                ret, frame = self.capture_frame()
                if not ret or frame is None:
                    logger.warning("Failed to capture frame from camera")
                    continue
                
                self.frame_count += 1
                detections = self.detect_vehicles(frame)
                
                # Store detections
                for detection in detections:
                    self.detection_buffer.append(detection)
                
                # Adaptive frame rate based on processing load
                # Maintain ~30 FPS but allow dynamic adjustment
                time.sleep(0.033)  # ~30 FPS baseline
                
            except Exception as e:
                logger.error(f"Detection loop error: {e}")
                time.sleep(0.1)  # Prevent tight error loop
                
    def stop_detection(self):
        """Stop vehicle detection service with proper cleanup"""
        self.is_running = False
        
        # Cleanup camera resources
        if self.picamera2:
            try:
                self.picamera2.stop()
                self.picamera2.close()
            except Exception as e:
                logger.error(f"Error stopping picamera2: {e}")
                
        if self.camera:
            try:
                self.camera.release()
            except Exception as e:
                logger.error(f"Error releasing OpenCV camera: {e}")
        
        logger.info("Vehicle detection service stopped")
    
    def get_recent_detections(self, seconds=10):
        """Get detections from the last N seconds"""
        current_time = time.time()
        recent_detections = []
        
        for detection in self.detection_buffer:
            if current_time - detection.timestamp <= seconds:
                recent_detections.append(detection)
                
        return recent_detections

if __name__ == "__main__":
    # Test the vehicle detection service
    service = VehicleDetectionService()
    
    try:
        service.start_detection()
        time.sleep(30)  # Run for 30 seconds
    finally:
        service.stop_detection()
