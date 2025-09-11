#!/usr/bin/env python3
"""
Vehicle Detection Service for Raspberry Pi 5
Uses TensorFlow/OpenCV with Sony IMX500 AI Camera for real-time vehicle detection
Optimized for Raspberry Pi 5 with native camera interface

Features:
- Real-time vehicle detection using IMX500 AI camera
- Automatic image saving to external SSD for high-confidence detections
- Periodic snapshots every 5 minutes for monitoring
- Configurable detection thresholds and storage management
- Support for both IMX500 on-sensor AI and TensorFlow Lite inference
"""


import cv2
import numpy as np
import time
import json
import os
import subprocess
import tempfile
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
    # TEMP: Suppress camera capture warnings - set to False for debugging
    suppress_camera_warning = False
    """
    Core vehicle detection service using Sony IMX500 AI Camera
    Optimized for Raspberry Pi 5 with native camera interface and edge inference
    """
    

    def __init__(self, camera_index=0, model_path=None, use_tflite=True, use_imx500_ai=True, imx500_model_path=None, 
                 save_detections=True, save_path="/mnt/storage/ai_camera_images", save_confidence_threshold=0.7, max_saved_images=1000,
                 periodic_snapshots=True, snapshot_interval_minutes=5, periodic_snapshot_path="/mnt/storage/periodic_snapshots"):
        self.camera_index = camera_index
        self.model_path = model_path
        self.use_tflite = use_tflite and TFLITE_AVAILABLE
        self.use_imx500_ai = use_imx500_ai and IMX500_AVAILABLE
        self.imx500_model_path = imx500_model_path or "/usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk"
        
        # Image saving configuration
        self.save_detections = save_detections
        self.save_path = save_path
        self.save_confidence_threshold = save_confidence_threshold
        self.max_saved_images = max_saved_images
        
        # Periodic snapshot configuration (allow environment overrides)
        # ENV VARS:
        #   PERIODIC_SNAPSHOT_PATH - override snapshot directory
        #   SNAPSHOT_INTERVAL_MINUTES - override interval
        #   DETECTION_SAVE_PATH - override detection save dir
        env_snapshot_path = os.getenv("PERIODIC_SNAPSHOT_PATH")
        env_snapshot_interval = os.getenv("SNAPSHOT_INTERVAL_MINUTES")
        env_detection_path = os.getenv("DETECTION_SAVE_PATH")

        self.periodic_snapshots = periodic_snapshots
        self.snapshot_interval_minutes = int(env_snapshot_interval) if env_snapshot_interval else snapshot_interval_minutes
        self.periodic_snapshot_path = env_snapshot_path if env_snapshot_path else periodic_snapshot_path
        if env_detection_path:
            self.save_path = env_detection_path
        self.last_snapshot_time = 0
        self.snapshot_interval_seconds = self.snapshot_interval_minutes * 60
        if env_snapshot_path or env_snapshot_interval or env_detection_path:
            logger.info(f"Environment overrides -> snapshot_path: {self.periodic_snapshot_path}, interval: {self.snapshot_interval_minutes}m, detections: {self.save_path}")
        
        self.camera = None
        self.picamera2 = None
        self.model = None
        self.interpreter = None
        self.imx500 = None
        self.is_running = False
        self.detection_buffer = deque(maxlen=100)
        self.frame_count = 0
        # Performance optimization settings - corrected for IMX500 SSD model
        self.input_size = (320, 320)  # Corrected: IMX500 SSD model expects 320x320 input
        self.confidence_threshold = 0.5
        self.nms_threshold = 0.4
        
    def initialize_camera(self):
        """Initialize Sony IMX500 AI Camera using optimal interface"""
        try:
            if PI_CAMERA_AVAILABLE:
                self.picamera2 = Picamera2()
                # Configure for optimal performance with IMX500
                camera_config = self.picamera2.create_video_configuration(
                    main={"size": (1920, 1080), "format": "RGB888"},
                    lores={"size": self.input_size, "format": "YUV420"}
                )
                # Set framerate for smooth video processing
                camera_config["controls"]["FrameRate"] = 30.0
                self.picamera2.configure(camera_config)
                self.picamera2.start()
                logger.info("Sony IMX500 AI Camera initialized with picamera2")
                # If using IMX500 on-sensor AI, initialize model
                if self.use_imx500_ai:
                    self.imx500 = IMX500Device(self.imx500_model_path)
                    logger.info(f"IMX500 on-sensor AI model loaded: {self.imx500_model_path}")
                    # Show firmware loading progress (as recommended in docs)
                    self.imx500.show_network_fw_progress_bar()
                    # Set inference aspect ratio to match model input
                    self.imx500.set_inference_aspect_ratio(self.input_size)
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
        try:
            if self.picamera2:
                # Use Picamera2 (preferred for Raspberry Pi with IMX500)
                try:
                    frame = self.picamera2.capture_array()
                    # Validate the frame
                    if frame is not None and frame.size > 0:
                        # Convert from YUV420 to RGB if needed
                        if len(frame.shape) == 3 and frame.shape[2] == 1:  # Grayscale
                            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
                        elif len(frame.shape) == 3 and frame.shape[2] == 3:  # Already RGB
                            pass
                        else:  # YUV or other format - try conversion
                            try:
                                frame = cv2.cvtColor(frame, cv2.COLOR_YUV2RGB_I420)
                            except:
                                # If color conversion fails, fallback to system level
                                logger.warning("Picamera2 color conversion failed, falling back to system-level capture")
                                return self._capture_frame_system_level()
                        return True, frame
                    else:
                        logger.warning("Picamera2 returned empty frame, falling back to system-level capture")
                        return self._capture_frame_system_level()
                except Exception as e:
                    logger.warning(f"Picamera2 capture failed: {e}, falling back to system-level capture")
                    return self._capture_frame_system_level()
            elif self.camera:
                # Use OpenCV fallback
                ret, frame = self.camera.read()
                if ret:
                    return True, frame
                else:
                    return False, None
            else:
                # Fallback to system-level camera capture (works with IMX500)
                return self._capture_frame_system_level()
        except Exception as e:
            logger.error(f"Failed to capture frame: {e}")
            # Try system-level capture as fallback
            try:
                return self._capture_frame_system_level()
            except Exception as e2:
                logger.error(f"System-level capture also failed: {e2}")
                # Final fallback to mock camera for testing
                return self._capture_mock_frame()

    def _capture_frame_system_level(self):
        """Capture frame using system-level tools (fswebcam) when OpenCV fails"""
        try:
            # Create temporary file for captured image
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
                temp_path = tmp_file.name
            
            # Use fswebcam to capture image (we verified this works with IMX500)
            cmd = [
                'fswebcam',
                '--no-banner',
                '--resolution', '1920x1080',
                '--device', '/dev/video0',
                '--jpeg', '95',
                temp_path
            ]
            
            # Execute fswebcam command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and os.path.exists(temp_path):
                # Load captured image with OpenCV
                frame = cv2.imread(temp_path)
                # Clean up temporary file
                os.unlink(temp_path)
                
                if frame is not None:
                    # Convert from BGR to RGB for consistency
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    logger.info("Successfully captured frame using system-level tools")
                    return True, frame
                else:
                    logger.error("Failed to load captured image")
                    return False, None
            else:
                logger.error(f"fswebcam failed: {result.stderr}")
                return False, None
                
        except subprocess.TimeoutExpired:
            logger.error("fswebcam command timed out")
            return False, None
        except Exception as e:
            logger.error(f"System-level capture failed: {e}")
            return False, None
        finally:
            # Ensure temp file is cleaned up
            if 'temp_path' in locals() and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except:
                    pass

    def _capture_mock_frame(self):
        """Create a mock frame for testing when camera is unavailable"""
        try:
            import numpy as np
            # Create a mock 1920x1080 RGB frame
            mock_frame = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
            
            # Add some text to indicate it's a mock frame
            cv2.putText(mock_frame, "MOCK CAMERA - FOR TESTING", (50, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
            cv2.putText(mock_frame, f"Time: {time.strftime('%H:%M:%S')}", (50, 120), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 2)
            
            logger.info("Using mock camera frame for testing")
            return True, mock_frame
        except Exception as e:
            logger.error(f"Failed to create mock frame: {e}")
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
    
    def save_detection_snapshots(self, frame, detections):
        """
        Save snapshots of frames with high-confidence vehicle detections to SSD
        """
        if not self.save_detections:
            return
            
        try:
            # Ensure save directory exists
            os.makedirs(self.save_path, exist_ok=True)
            
            # Filter for high-confidence detections
            high_conf_detections = [d for d in detections if d.confidence >= self.save_confidence_threshold]
            
            if high_conf_detections:
                # Create timestamp for filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                
                # Save the full frame
                frame_filename = f"detection_{timestamp}_frame_{self.frame_count}.jpg"
                frame_path = os.path.join(self.save_path, frame_filename)
                cv2.imwrite(frame_path, frame)
                
                # Save detection metadata
                metadata = {
                    "timestamp": timestamp,
                    "frame_id": self.frame_count,
                    "detections": [
                        {
                            "id": d.detection_id,
                            "bbox": d.bbox,
                            "confidence": d.confidence,
                            "vehicle_type": d.vehicle_type
                        } for d in high_conf_detections
                    ]
                }
                
                metadata_filename = f"detection_{timestamp}_metadata.json"
                metadata_path = os.path.join(self.save_path, metadata_filename)
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                logger.info(f"Saved detection snapshot: {frame_filename} ({len(high_conf_detections)} vehicles)")
                
                # Clean up old images if we have too many
                self._cleanup_old_images()
                
        except Exception as e:
            logger.error(f"Failed to save detection snapshot: {e}")
    
    def _cleanup_old_images(self):
        """Remove oldest images if we exceed the maximum saved images limit"""
        try:
            if not os.path.exists(self.save_path):
                return
                
            # Get all image files
            image_files = [f for f in os.listdir(self.save_path) if f.endswith(('.jpg', '.jpeg', '.png'))]
            
            if len(image_files) > self.max_saved_images:
                # Sort by modification time (oldest first)
                image_files.sort(key=lambda x: os.path.getmtime(os.path.join(self.save_path, x)))
                
                # Remove oldest files
                files_to_remove = image_files[:len(image_files) - self.max_saved_images + 50]  # Keep some buffer
                
                for filename in files_to_remove:
                    try:
                        os.remove(os.path.join(self.save_path, filename))
                        logger.info(f"Cleaned up old image: {filename}")
                    except Exception as e:
                        logger.warning(f"Failed to remove old image {filename}: {e}")
                        
        except Exception as e:
            logger.error(f"Failed to cleanup old images: {e}")
    
    def take_periodic_snapshot(self, frame):
        """
        Take a periodic snapshot every N minutes and save to SSD
        """
        if not self.periodic_snapshots:
            return
            
        current_time = time.time()
        time_since_last = current_time - self.last_snapshot_time
        
        # Debug logging
        if time_since_last >= 60:  # Log every minute
            logger.debug(f"Periodic snapshot check: {time_since_last:.0f}s since last snapshot (interval: {self.snapshot_interval_seconds}s)")
        
        if time_since_last >= self.snapshot_interval_seconds:
            logger.info(f"Taking periodic snapshot (every {self.snapshot_interval_minutes} minutes)")
            try:
                # Ensure periodic snapshot directory exists (create parent directories too)
                logger.debug(f"Creating snapshot directory: {self.periodic_snapshot_path}")
                os.makedirs(self.periodic_snapshot_path, exist_ok=True)
                
                # Create timestamp for filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"periodic_snapshot_{timestamp}.jpg"
                filepath = os.path.join(self.periodic_snapshot_path, filename)
                
                # Save the frame
                logger.debug(f"Saving snapshot to: {filepath}")
                cv2.imwrite(filepath, frame)
                
                # Verify file was created
                if os.path.exists(filepath):
                    file_size = os.path.getsize(filepath)
                    logger.info(f"✅ Periodic snapshot saved: {filename} ({file_size} bytes)")
                else:
                    logger.error(f"❌ Failed to verify snapshot file: {filepath}")
                
                # Update last snapshot time
                self.last_snapshot_time = current_time
                
                # Keep only the latest snapshot (cleanup old ones)
                self._cleanup_old_periodic_snapshots()
                
            except PermissionError as e:
                logger.error(f"Permission denied creating snapshot directory {self.periodic_snapshot_path}: {e}")
                # Try fallback directory
                self._try_fallback_snapshot_directory(frame)
            except OSError as e:
                logger.error(f"Failed to create snapshot directory {self.periodic_snapshot_path}: {e}")
                # Try fallback directory
                self._try_fallback_snapshot_directory(frame)
            except Exception as e:
                logger.error(f"Failed to take periodic snapshot: {e}")
    
    def _try_fallback_snapshot_directory(self, frame):  # Single consolidated implementation
        """Try to save snapshot to fallback directories in order of preference."""
        fallbacks = [
            "/tmp/periodic_snapshots",
            os.path.join(os.getcwd(), "periodic_snapshots")
        ]
        for fb in fallbacks:
            try:
                os.makedirs(fb, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"periodic_snapshot_{timestamp}.jpg"
                filepath = os.path.join(fb, filename)
                cv2.imwrite(filepath, frame)
                logger.info(f"✅ Saved periodic snapshot to fallback: {filepath}")
                self.periodic_snapshot_path = fb
                return
            except Exception as e:  # pragma: no cover - fallback rarely fails
                logger.error(f"Fallback save failed for {fb}: {e}")
        logger.error("All fallback snapshot saves failed")
    
    def _cleanup_old_periodic_snapshots(self):
        """Keep only the most recent periodic snapshot"""
        try:
            if not os.path.exists(self.periodic_snapshot_path):
                return
                
            # Get all periodic snapshot files
            snapshot_files = [f for f in os.listdir(self.periodic_snapshot_path) 
                            if f.startswith('periodic_snapshot_') and f.endswith('.jpg')]
            
            if len(snapshot_files) > 1:
                # Sort by modification time (oldest first)
                snapshot_files.sort(key=lambda x: os.path.getmtime(os.path.join(self.periodic_snapshot_path, x)))
                
                # Remove all but the most recent
                files_to_remove = snapshot_files[:-1]
                
                for filename in files_to_remove:
                    try:
                        os.remove(os.path.join(self.periodic_snapshot_path, filename))
                        logger.info(f"Cleaned up old periodic snapshot: {filename}")
                    except Exception as e:
                        logger.warning(f"Failed to remove old periodic snapshot {filename}: {e}")
                        
        except Exception as e:
            logger.error(f"Failed to cleanup old periodic snapshots: {e}")
    
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
        logger.info("🚀 Starting vehicle detection service...")
        logger.info(f"📹 Camera index: {self.camera_index}")
        logger.info(f"⏰ Periodic snapshots: {self.periodic_snapshots}")
        logger.info(f"⏱️  Snapshot interval: {self.snapshot_interval_minutes} minutes ({self.snapshot_interval_seconds} seconds)")
        logger.info(f"📁 Snapshot path: {self.periodic_snapshot_path}")
        logger.info(f"🔧 Use IMX500 AI: {self.use_imx500_ai}")
        logger.info(f"🧠 Model path: {self.model_path}")
        
        # Check if periodic snapshots directory exists
        if self.periodic_snapshots:
            if os.path.exists(self.periodic_snapshot_path):
                logger.info(f"✅ Periodic snapshot directory exists: {self.periodic_snapshot_path}")
            else:
                logger.warning(f"⚠️  Periodic snapshot directory does not exist: {self.periodic_snapshot_path}")
                try:
                    os.makedirs(self.periodic_snapshot_path, exist_ok=True)
                    logger.info(f"✅ Created periodic snapshot directory: {self.periodic_snapshot_path}")
                except Exception as e:
                    logger.error(f"❌ Failed to create periodic snapshot directory: {e}")
        
        if not self.initialize_camera():
            logger.error("❌ Camera initialization failed - cannot start detection")
            return False
            
        if not self.load_model():
            logger.error("❌ Model loading failed - cannot start detection")
            return False
            
        self.is_running = True
        detection_thread = threading.Thread(target=self._detection_loop)
        detection_thread.daemon = True
        detection_thread.start()
        logger.info("✅ Vehicle detection service started successfully")
        logger.info("🔄 Detection loop should be running in background thread")
        return True
    
    def _detection_loop(self):
        """Main detection loop with optimized frame processing"""
        logger.info("Detection loop started")
        loop_count = 0
        
        while self.is_running:
            try:
                loop_count += 1
                if loop_count % 100 == 0:  # Log every 100 frames
                    logger.info(f"Detection loop running - frame count: {self.frame_count}")
                
                ret, frame = self.capture_frame()
                if not ret or frame is None:
                    if not self.suppress_camera_warning:
                        logger.warning("Failed to capture frame from camera")
                    time.sleep(0.1)
                    continue
                
                self.frame_count += 1
                detections = self.detect_vehicles(frame)
                
                # Store detections
                for detection in detections:
                    self.detection_buffer.append(detection)
                
                # Save detection snapshots to SSD if vehicles detected
                self.save_detection_snapshots(frame, detections)
                
                # Take periodic snapshot every 5 minutes
                if self.periodic_snapshots:
                    logger.debug(f"About to call take_periodic_snapshot (frame {self.frame_count})")
                    self.take_periodic_snapshot(frame)
                
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
