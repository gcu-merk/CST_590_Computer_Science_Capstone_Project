#!/usr/bin/env python3
"""
Vehicle Detection Service for Raspberry Pi 5
Uses TensorFlow/OpenCV for real-time vehicle detection and speed estimation
"""

import cv2
import numpy as np
import tensorflow as tf
import time
import json
from datetime import datetime
from collections import deque
import threading
import logging
import serial
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OPS243CRadar:
    """OmniPreSense OPS243-C FMCW Doppler Radar Sensor Interface"""
    
    def __init__(self, port='/dev/ttyACM0', baudrate=9600):
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.is_running = False
        self.speed_buffer = deque(maxlen=10)
        self.last_speed = 0.0
        self.detection_threshold = 0.5  # m/s minimum speed to register
        
    def connect(self):
        """Connect to OPS243-C radar sensor"""
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1.0,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            
            # Wait for connection to stabilize
            time.sleep(2)
            
            # Initialize sensor
            self._send_command("??")  # Query sensor info
            time.sleep(0.5)
            
            # Set to speed output mode
            self._send_command("OS")  # Output speed data
            time.sleep(0.5)
            
            # Set units to m/s
            self._send_command("UM")  # Units in m/s
            time.sleep(0.5)
            
            # Set minimum speed detection threshold
            self._send_command("SM")  # Speed magnitude mode
            time.sleep(0.5)
            
            self.is_running = True
            logger.info(f"OPS243-C radar connected on {self.port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to radar: {e}")
            return False
    
    def _send_command(self, command):
        """Send command to radar sensor"""
        if self.serial_conn and self.serial_conn.is_open:
            try:
                self.serial_conn.write((command + '\r').encode())
                self.serial_conn.flush()
            except Exception as e:
                logger.error(f"Error sending command {command}: {e}")
    
    def read_speed(self):
        """Read speed data from radar sensor"""
        if not self.is_running or not self.serial_conn:
            return None
        
        try:
            if self.serial_conn.in_waiting > 0:
                # Read line from sensor
                line = self.serial_conn.readline().decode('utf-8').strip()
                
                # Parse speed data - OPS243-C outputs format like "{speed}"
                if line.startswith('{') and line.endswith('}'):
                    speed_str = line[1:-1]  # Remove braces
                    
                    # Handle different possible formats
                    if ',' in speed_str:
                        # Format: "{speed,direction}" or "{speed,magnitude}"
                        parts = speed_str.split(',')
                        speed = float(parts[0])
                    else:
                        # Format: "{speed}"
                        speed = float(speed_str)
                    
                    # Convert to absolute value and apply threshold
                    abs_speed = abs(speed)
                    
                    if abs_speed >= self.detection_threshold:
                        self.last_speed = abs_speed
                        self.speed_buffer.append({
                            'speed_ms': abs_speed,
                            'speed_kmh': abs_speed * 3.6,
                            'timestamp': time.time(),
                            'direction': 'approaching' if speed < 0 else 'receding'
                        })
                        
                        return {
                            'speed_ms': abs_speed,
                            'speed_kmh': abs_speed * 3.6,
                            'raw_speed': speed,
                            'timestamp': time.time()
                        }
                
        except Exception as e:
            logger.error(f"Error reading radar data: {e}")
        
        return None
    
    def get_average_speed(self, window_seconds=3):
        """Get average speed over specified time window"""
        if not self.speed_buffer:
            return None
        
        current_time = time.time()
        recent_readings = [
            reading for reading in self.speed_buffer 
            if current_time - reading['timestamp'] <= window_seconds
        ]
        
        if not recent_readings:
            return None
        
        avg_speed_ms = sum(r['speed_ms'] for r in recent_readings) / len(recent_readings)
        return {
            'speed_ms': avg_speed_ms,
            'speed_kmh': avg_speed_ms * 3.6,
            'sample_count': len(recent_readings),
            'timestamp': current_time
        }
    
    def disconnect(self):
        """Disconnect from radar sensor"""
        self.is_running = False
        if self.serial_conn and self.serial_conn.is_open:
            try:
                self.serial_conn.close()
                logger.info("Radar sensor disconnected")
            except Exception as e:
                logger.error(f"Error disconnecting radar: {e}")

class VehicleDetector:
    def __init__(self, model_path=None, confidence_threshold=0.5):
        self.confidence_threshold = confidence_threshold
        self.vehicle_classes = [2, 3, 5, 7]  # car, motorcycle, bus, truck in COCO
        self.class_names = {2: 'car', 3: 'motorcycle', 5: 'bus', 7: 'truck'}
        
        # Load pre-trained model (using TensorFlow Hub MobileNet)
        self.model = self._load_model()
        
        # Vehicle tracking for radar correlation
        self.tracked_vehicles = {}
        self.next_vehicle_id = 1
        
    def _load_model(self):
        """Load TensorFlow Hub MobileNet SSD model"""
        try:
            # Using TensorFlow Hub for easy model loading
            import tensorflow_hub as hub
            model = hub.load("https://tfhub.dev/tensorflow/ssd_mobilenet_v2/2")
            logger.info("Model loaded successfully")
            return model
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            # Fallback to a simpler detection method
            return None
    
    def detect_vehicles(self, frame):
        """Detect vehicles in frame"""
        if self.model is None:
            return self._simple_detection(frame)
        
        # Preprocess frame
        input_tensor = tf.convert_to_tensor(frame)
        input_tensor = input_tensor[tf.newaxis, ...]
        
        # Run detection
        detections = self.model(input_tensor)
        
        # Process results
        vehicles = []
        boxes = detections['detection_boxes'][0].numpy()
        classes = detections['detection_classes'][0].numpy().astype(int)
        scores = detections['detection_scores'][0].numpy()
        
        h, w = frame.shape[:2]
        
        for i in range(len(boxes)):
            if scores[i] > self.confidence_threshold and classes[i] in self.vehicle_classes:
                box = boxes[i]
                y1, x1, y2, x2 = box
                
                # Convert to pixel coordinates
                x1, y1, x2, y2 = int(x1*w), int(y1*h), int(x2*w), int(y2*h)
                
                vehicle = {
                    'id': self._assign_vehicle_id([x1, y1, x2, y2]),
                    'class': self.class_names.get(classes[i], 'vehicle'),
                    'confidence': float(scores[i]),
                    'bbox': [x1, y1, x2, y2],
                    'center': [(x1+x2)//2, (y1+y2)//2],
                    'area': (x2-x1) * (y2-y1),
                    'timestamp': time.time()
                }
                vehicles.append(vehicle)
        
        return vehicles
    
    def _simple_detection(self, frame):
        """Fallback detection using background subtraction"""
        # Simple background subtraction for motion detection
        # This is a fallback if TensorFlow model fails
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        if not hasattr(self, 'bg_subtractor'):
            self.bg_subtractor = cv2.createBackgroundSubtractorMOG2()
        
        fg_mask = self.bg_subtractor.apply(gray)
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        vehicles = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 1000:  # Minimum area for vehicle
                x, y, w, h = cv2.boundingRect(contour)
                vehicle = {
                    'id': self._assign_vehicle_id([x, y, x+w, y+h]),
                    'class': 'vehicle',
                    'confidence': 0.7,
                    'bbox': [x, y, x+w, y+h],
                    'center': [x+w//2, y+h//2],
                    'area': w * h,
                    'timestamp': time.time()
                }
                vehicles.append(vehicle)
        
        return vehicles
    
    def _assign_vehicle_id(self, bbox):
        """Assign or retrieve vehicle ID based on position tracking"""
        center = [(bbox[0] + bbox[2]) // 2, (bbox[1] + bbox[3]) // 2]
        current_time = time.time()
        
        # Clean up old tracked vehicles (older than 5 seconds)
        self.tracked_vehicles = {
            vid: data for vid, data in self.tracked_vehicles.items()
            if current_time - data['last_seen'] < 5.0
        }
        
        # Find closest existing vehicle
        best_match_id = None
        min_distance = float('inf')
        
        for vehicle_id, tracked_data in self.tracked_vehicles.items():
            distance = np.sqrt(
                (center[0] - tracked_data['center'][0]) ** 2 +
                (center[1] - tracked_data['center'][1]) ** 2
            )
            
            if distance < min_distance and distance < 100:  # Max tracking distance
                min_distance = distance
                best_match_id = vehicle_id
        
        if best_match_id:
            # Update existing vehicle
            self.tracked_vehicles[best_match_id].update({
                'center': center,
                'last_seen': current_time
            })
            return best_match_id
        else:
            # Create new vehicle ID
            new_id = f"vehicle_{self.next_vehicle_id}"
            self.next_vehicle_id += 1
            
            self.tracked_vehicles[new_id] = {
                'center': center,
                'last_seen': current_time,
                'first_seen': current_time
            }
            
            return new_id
    
    def correlate_with_radar(self, vehicles, radar_speed_data):
        """Correlate detected vehicles with radar speed measurements"""
        if not radar_speed_data or not vehicles:
            return vehicles
        
        # For now, assign radar speed to the largest/most prominent vehicle
        # In a more sophisticated system, you'd use spatial correlation
        largest_vehicle = max(vehicles, key=lambda v: v.get('area', 0))
        
        # Add radar speed data to the largest vehicle
        largest_vehicle.update({
            'radar_speed_ms': radar_speed_data['speed_ms'],
            'radar_speed_kmh': radar_speed_data['speed_kmh'],
            'speed_source': 'radar'
        })
        
        return vehicles

class CameraManager:
    def __init__(self, use_ai_camera=True):
        self.use_ai_camera = use_ai_camera
        self.cap = None
        self.picam2 = None
        self.is_running = False
        
    def start(self):
        """Start camera capture"""
        if self.use_ai_camera:
            return self._start_ai_camera()
        else:
            return self._start_usb_camera()
    
    def _start_ai_camera(self):
        """Start Raspberry Pi AI Camera"""
        try:
            from picamera2 import Picamera2
            
            self.picam2 = Picamera2()
            
            # Configure for traffic monitoring (good balance of quality/performance)
            config = self.picam2.create_preview_configuration(
                main={"size": (1280, 720), "format": "RGB888"}
            )
            self.picam2.configure(config)
            
            self.picam2.start()
            self.is_running = True
            logger.info("AI Camera started successfully")
            return True
            
        except ImportError:
            logger.error("picamera2 not installed. Install with: sudo apt install python3-picamera2")
            return False
        except Exception as e:
            logger.error(f"Failed to start AI camera: {e}")
            return False
    
    def _start_usb_camera(self):
        """Start USB camera (fallback)"""
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            logger.error("Failed to open USB camera")
            return False
        
        # Set camera properties
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        self.is_running = True
        logger.info("USB Camera started successfully")
        return True
    
    def get_frame(self):
        """Get current frame from camera"""
        if not self.is_running:
            return None
        
        if self.use_ai_camera and self.picam2:
            try:
                # Get frame from AI camera
                frame = self.picam2.capture_array()
                # Convert RGB to BGR for OpenCV compatibility
                return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            except Exception as e:
                logger.error(f"Error capturing from AI camera: {e}")
                return None
        
        elif self.cap:
            ret, frame = self.cap.read()
            return frame if ret else None
        
        return None
    
    def stop(self):
        """Stop camera capture"""
        self.is_running = False
        
        if self.picam2:
            try:
                self.picam2.stop()
                self.picam2.close()
            except:
                pass
            self.picam2 = None
        
        if self.cap:
            self.cap.release()
            self.cap = None
        
        logger.info("Camera stopped")

class EdgeTrafficMonitor:
    def __init__(self, radar_port='/dev/ttyACM0'):
        self.detector = VehicleDetector()
        self.camera = CameraManager()
        self.radar = OPS243CRadar(port=radar_port)
        self.results_buffer = deque(maxlen=1000)
        self.is_running = False
        
    def start_monitoring(self):
        """Start the traffic monitoring system"""
        # Start camera
        if not self.camera.start():
            logger.error("Failed to start camera")
            return False
        
        # Start radar
        if not self.radar.connect():
            logger.warning("Failed to connect radar - continuing with camera only")
            self.radar = None
        
        self.is_running = True
        logger.info("Traffic monitoring started")
        
        try:
            while self.is_running:
                frame = self.camera.get_frame()
                if frame is None:
                    continue
                
                # Detect vehicles from camera
                vehicles = self.detector.detect_vehicles(frame)
                
                # Get radar speed data
                radar_data = None
                if self.radar:
                    radar_data = self.radar.read_speed()
                
                # Correlate camera detections with radar speed
                if vehicles and radar_data:
                    vehicles = self.detector.correlate_with_radar(vehicles, radar_data)
                
                # Store results
                result = {
                    'timestamp': datetime.now().isoformat(),
                    'vehicle_count': len(vehicles),
                    'vehicles': vehicles,
                    'radar_data': radar_data,
                    'frame_size': frame.shape if frame is not None else None
                }
                self.results_buffer.append(result)
                
                # Print summary
                if vehicles:
                    logger.info(f"Detected {len(vehicles)} vehicles")
                    for vehicle in vehicles:
                        if 'radar_speed_kmh' in vehicle:
                            logger.info(f"Vehicle {vehicle['id']} ({vehicle['class']}): {vehicle['radar_speed_kmh']:.1f} km/h (radar)")
                        else:
                            logger.info(f"Vehicle {vehicle['id']} ({vehicle['class']}): No speed data")
                
                elif radar_data:
                    logger.info(f"Radar detected speed: {radar_data['speed_kmh']:.1f} km/h (no visual detection)")
                
                time.sleep(0.1)  # Small delay
                
        except KeyboardInterrupt:
            logger.info("Stopping monitoring...")
        finally:
            self.stop_monitoring()
    
    def stop_monitoring(self):
        """Stop the monitoring system"""
        self.is_running = False
        self.camera.stop()
        if self.radar:
            self.radar.disconnect()
        logger.info("Traffic monitoring stopped")
    
    def get_recent_results(self, limit=10):
        """Get recent detection results"""
        return list(self.results_buffer)[-limit:]

if __name__ == "__main__":
    # Test the system
    import argparse
    
    parser = argparse.ArgumentParser(description='Traffic Monitoring System')
    parser.add_argument('--radar-port', default='/dev/ttyACM0', 
                       help='Serial port for OPS243-C radar sensor')
    parser.add_argument('--no-radar', action='store_true',
                       help='Run without radar sensor')
    
    args = parser.parse_args()
    
    if args.no_radar:
        # Create monitor without radar
        monitor = EdgeTrafficMonitor(radar_port=None)
        monitor.radar = None
    else:
        monitor = EdgeTrafficMonitor(radar_port=args.radar_port)
    
    try:
        monitor.start_monitoring()
    except KeyboardInterrupt:
        print("\nShutting down...")
        monitor.stop_monitoring()