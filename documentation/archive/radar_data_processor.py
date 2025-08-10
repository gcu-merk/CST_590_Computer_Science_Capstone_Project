#!/usr/bin/env python3
"""
OPS243-C FMCW Doppler Radar Data Processor
Processes real-time radar data for vehicle speed detection and tracking
"""

import json
import time
import serial
import threading
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Deque
from collections import deque
import numpy as np
from scipy import signal
from scipy.stats import zscore
import statistics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RadarReading:
    """Single radar measurement data point"""
    timestamp: float
    unit: str  # 'm' for magnitude, 'mps' for speed
    magnitude: int
    range_m: Optional[float] = None  # Range in meters
    speed_mps: Optional[float] = None  # Speed in m/s
    raw_data: Dict = field(default_factory=dict)

@dataclass
class VehicleDetection:
    """Processed vehicle detection from radar data"""
    detection_id: str
    start_time: float
    end_time: float
    peak_magnitude: int
    avg_magnitude: float
    speeds: List[float]
    avg_speed_mps: float
    max_speed_mps: float
    direction: str  # 'approaching', 'receding', 'stationary'
    confidence: float
    range_readings: List[float]

class RadarDataProcessor:
    """
    Processes OPS243-C radar data for vehicle detection and speed analysis
    """
    
    def __init__(self, 
                 serial_port: str = '/dev/ttyACM0',
                 baud_rate: int = 9600,
                 buffer_size: int = 1000,
                 detection_threshold: int = 2000,
                 speed_threshold: float = 0.3):
        """
        Initialize radar data processor
        
        Args:
            serial_port: UART port for radar sensor
            baud_rate: Communication baud rate
            buffer_size: Size of data buffer for processing
            detection_threshold: Minimum magnitude for vehicle detection
            speed_threshold: Minimum speed for valid detection (m/s)
        """
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self.detection_threshold = detection_threshold
        self.speed_threshold = speed_threshold
        
        # Data buffers
        self.magnitude_buffer: Deque[RadarReading] = deque(maxlen=buffer_size)
        self.speed_buffer: Deque[RadarReading] = deque(maxlen=buffer_size)
        
        # Processing state
        self.serial_connection: Optional[serial.Serial] = None
        self.is_running = False
        self.detection_counter = 0
        
        # Vehicle detection state
        self.current_detections: Dict[str, List[RadarReading]] = {}
        self.completed_detections: List[VehicleDetection] = []
        
        # Filtering parameters
        self.gaussian_sigma = 2.0
        self.outlier_threshold = 3.0  # Z-score threshold for outlier removal
        
    def connect_radar(self) -> bool:
        """
        Establish serial connection to radar sensor
        
        Returns:
            bool: True if connection successful
        """
        try:
            self.serial_connection = serial.Serial(
                port=self.serial_port,
                baudrate=self.baud_rate,
                timeout=1.0,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            
            # Send initialization commands
            self.serial_connection.write(b'{"PowerMode":"Active Continuously"}\n')
            self.serial_connection.write(b'{"SpeedOutputFeature":"J"}\n')
            
            logger.info(f"Connected to radar sensor on {self.serial_port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to radar: {e}")
            return False
    
    def disconnect_radar(self):
        """Close serial connection"""
        if self.serial_connection and self.serial_connection.is_open:
            # Set to idle mode before disconnecting
            self.serial_connection.write(b'{"PowerMode":"Idle or Pulse"}\n')
            self.serial_connection.close()
            logger.info("Radar sensor disconnected")
    
    def parse_radar_line(self, line: str) -> Optional[RadarReading]:
        """
        Parse single line of radar JSON data
        
        Args:
            line: JSON string from radar sensor
            
        Returns:
            RadarReading object or None if parsing fails
        """
        try:
            data = json.loads(line.strip())
            
            # Skip configuration messages
            if 'PowerMode' in data or 'SpeedOutputFeature' in data:
                return None
            
            # Parse data based on unit type
            if 'unit' in data and 'magnitude' in data and 'time' in data:
                reading = RadarReading(
                    timestamp=float(data['time']),
                    unit=data['unit'],
                    magnitude=int(data['magnitude']),
                    raw_data=data
                )
                
                # Add range data if available
                if 'range' in data:
                    reading.range_m = float(data['range'])
                
                # Add speed data if available
                if 'speed' in data:
                    reading.speed_mps = float(data['speed'])
                
                return reading
                
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Failed to parse radar data: {line.strip()} - {e}")
            
        return None
    
    def apply_gaussian_filter(self, magnitudes: List[float], sigma: float = None) -> List[float]:
        """
        Apply Gaussian smoothing filter to reduce noise
        
        Args:
            magnitudes: List of magnitude values
            sigma: Gaussian sigma parameter
            
        Returns:
            Filtered magnitude values
        """
        if len(magnitudes) < 3:
            return magnitudes
            
        sigma = sigma or self.gaussian_sigma
        return signal.gaussian_filter1d(magnitudes, sigma=sigma).tolist()
    
    def remove_outliers(self, values: List[float], threshold: float = None) -> List[float]:
        """
        Remove statistical outliers using Z-score method
        
        Args:
            values: List of numeric values
            threshold: Z-score threshold for outlier detection
            
        Returns:
            Values with outliers removed
        """
        if len(values) < 3:
            return values
            
        threshold = threshold or self.outlier_threshold
        z_scores = np.abs(zscore(values))
        return [val for val, z in zip(values, z_scores) if z < threshold]
    
    def detect_vehicle_events(self) -> List[VehicleDetection]:
        """
        Analyze magnitude buffer to detect vehicle passing events
        
        Returns:
            List of detected vehicle events
        """
        if len(self.magnitude_buffer) < 10:
            return []
        
        # Convert to arrays for processing
        times = [r.timestamp for r in self.magnitude_buffer]
        magnitudes = [float(r.magnitude) for r in self.magnitude_buffer]
        
        # Apply Gaussian filtering
        filtered_magnitudes = self.apply_gaussian_filter(magnitudes)
        
        # Find peaks above detection threshold
        peaks, properties = signal.find_peaks(
            filtered_magnitudes,
            height=self.detection_threshold,
            distance=20,  # Minimum distance between peaks
            width=5,      # Minimum width of peaks
            prominence=1000  # Minimum prominence
        )
        
        detections = []
        
        for peak_idx in peaks:
            # Extract peak region
            start_idx = max(0, peak_idx - 20)
            end_idx = min(len(filtered_magnitudes), peak_idx + 20)
            
            peak_region = filtered_magnitudes[start_idx:end_idx]
            time_region = times[start_idx:end_idx]
            
            # Find associated speed readings
            peak_time = times[peak_idx]
            associated_speeds = []
            
            for speed_reading in self.speed_buffer:
                if (abs(speed_reading.timestamp - peak_time) < 2.0 and 
                    speed_reading.speed_mps is not None and
                    abs(speed_reading.speed_mps) >= self.speed_threshold):
                    associated_speeds.append(speed_reading.speed_mps)
            
            if not associated_speeds:
                continue
                
            # Remove speed outliers
            clean_speeds = self.remove_outliers(associated_speeds)
            
            if not clean_speeds:
                continue
            
            # Calculate detection metrics
            avg_speed = statistics.mean(clean_speeds)
            max_speed = max(clean_speeds, key=abs)
            
            # Determine direction
            if avg_speed > 0.5:
                direction = "approaching"
            elif avg_speed < -0.5:
                direction = "receding"
            else:
                direction = "stationary"
            
            # Calculate confidence based on peak prominence and speed consistency
            speed_std = statistics.stdev(clean_speeds) if len(clean_speeds) > 1 else 0
            magnitude_prominence = properties['prominences'][list(peaks).index(peak_idx)]
            
            confidence = min(1.0, (magnitude_prominence / 5000.0) * (1.0 / (1.0 + speed_std)))
            
            # Create detection object
            detection = VehicleDetection(
                detection_id=f"radar_{self.detection_counter}_{int(peak_time)}",
                start_time=time_region[0],
                end_time=time_region[-1],
                peak_magnitude=int(filtered_magnitudes[peak_idx]),
                avg_magnitude=statistics.mean(peak_region),
                speeds=clean_speeds,
                avg_speed_mps=avg_speed,
                max_speed_mps=max_speed,
                direction=direction,
                confidence=confidence,
                range_readings=[]  # Could be populated if range data is available
            )
            
            detections.append(detection)
            self.detection_counter += 1
        
        return detections
    
    def process_reading(self, reading: RadarReading):
        """
        Process individual radar reading
        
        Args:
            reading: RadarReading object to process
        """
        if reading.unit == 'm':
            # Magnitude reading
            self.magnitude_buffer.append(reading)
            
        elif reading.unit == 'mps':
            # Speed reading
            self.speed_buffer.append(reading)
    
    def get_current_status(self) -> Dict:
        """
        Get current radar sensor status and statistics
        
        Returns:
            Dictionary with current status information
        """
        recent_magnitudes = [r.magnitude for r in list(self.magnitude_buffer)[-50:]]
        recent_speeds = [r.speed_mps for r in list(self.speed_buffer)[-50:] 
                        if r.speed_mps is not None]
        
        return {
            'is_connected': self.serial_connection and self.serial_connection.is_open,
            'buffer_magnitude_size': len(self.magnitude_buffer),
            'buffer_speed_size': len(self.speed_buffer),
            'recent_avg_magnitude': statistics.mean(recent_magnitudes) if recent_magnitudes else 0,
            'recent_max_magnitude': max(recent_magnitudes) if recent_magnitudes else 0,
            'recent_speeds': recent_speeds,
            'total_detections': self.detection_counter,
            'detection_threshold': self.detection_threshold
        }
    
    def start_continuous_processing(self):
        """Start continuous radar data processing in separate thread"""
        if not self.connect_radar():
            return False
            
        self.is_running = True
        processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
        processing_thread.start()
        
        logger.info("Started continuous radar processing")
        return True
    
    def stop_processing(self):
        """Stop continuous processing"""
        self.is_running = False
        self.disconnect_radar()
        logger.info("Stopped radar processing")
    
    def _processing_loop(self):
        """Main processing loop for continuous data acquisition"""
        while self.is_running and self.serial_connection:
            try:
                if self.serial_connection.in_waiting > 0:
                    line = self.serial_connection.readline().decode('utf-8', errors='ignore')
                    
                    if line.strip():
                        reading = self.parse_radar_line(line)
                        if reading:
                            self.process_reading(reading)
                            
                            # Detect vehicles every 50 readings
                            if len(self.magnitude_buffer) % 50 == 0:
                                new_detections = self.detect_vehicle_events()
                                self.completed_detections.extend(new_detections)
                                
                                # Keep only recent detections
                                current_time = time.time()
                                self.completed_detections = [
                                    d for d in self.completed_detections 
                                    if current_time - d.end_time < 300  # 5 minutes
                                ]
                    
                else:
                    time.sleep(0.01)  # Small delay to prevent busy waiting
                    
            except Exception as e:
                logger.error(f"Error in radar processing loop: {e}")
                time.sleep(1.0)

# Example usage and testing
if __name__ == "__main__":
    def test_with_sample_data():
        """Test processor with the provided sample data"""
        
        # Sample radar data (from your provided data)
        sample_data = [
            '{"time" : "104.438", "unit" : "m", "magnitude" : "10874", "range" : "2.1"}',
            '{"time" : "104.506", "unit" : "m", "magnitude" : "10880", "range" : "2.1"}',
            '{"time" : "105.122", "unit" : "mps", "magnitude" : "23", "speed" : "1.0"}',
            '{"time" : "105.190", "unit" : "mps", "magnitude" : "683", "speed" : "1.3"}',
            '{"time" : "105.258", "unit" : "mps", "magnitude" : "77", "speed" : "0.6"}',
            '{"time" : "106.206", "unit" : "mps", "magnitude" : "512", "speed" : "2.2"}',
            # ... add more sample data as needed
        ]
        
        processor = RadarDataProcessor()
        
        # Process sample data
        for line in sample_data:
            reading = processor.parse_radar_line(line)
            if reading:
                processor.process_reading(reading)
                print(f"Processed: {reading.unit} - {reading.magnitude} - Speed: {reading.speed_mps}")
        
        # Test detection
        detections = processor.detect_vehicle_events()
        print(f"\nDetected {len(detections)} vehicles:")
        for detection in detections:
            print(f"Vehicle {detection.detection_id}: {detection.avg_speed_mps:.1f} m/s ({detection.direction})")
        
        # Print status
        status = processor.get_current_status()
        print(f"\nRadar Status: {status}")
    
    # Run test
    test_with_sample_data()
