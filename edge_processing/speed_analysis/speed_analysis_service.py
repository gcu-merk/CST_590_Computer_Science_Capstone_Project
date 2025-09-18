#!/usr/bin/env python3
"""
OPS243-C FMCW Doppler Radar Speed Analysis Service
Processes real-time radar data for vehicle speed detection and tracking
Optimized for Raspberry Pi 5 with improved serial communication
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

# Raspberry Pi 5 GPIO for hardware control
import RPi.GPIO as GPIO
from gpiozero import LED, Button

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
class SpeedDetection:
    """Processed speed detection from radar data"""
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
            self._send_command("OJ")  # Set JSON output format
            self._send_command("OF")  # Turn on FFT output
            time.sleep(1)
            
            logger.info(f"Connected to OPS243-C radar on {self.port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to radar: {e}")
            return False
    
    def _send_command(self, command):
        """Send command to radar sensor"""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.write((command + "\n").encode())
            time.sleep(0.1)
    
    def read_data(self):
        """Read data from radar sensor"""
        if not self.serial_conn or not self.serial_conn.is_open:
            return None
            
        try:
            if self.serial_conn.in_waiting > 0:
                line = self.serial_conn.readline().decode('utf-8').strip()
                return self._parse_radar_data(line)
        except Exception as e:
            logger.error(f"Error reading radar data: {e}")
            
        return None
    
    def _parse_radar_data(self, data_line):
        """Parse radar data line into structured format"""
        try:
            # Try to parse as JSON first
            if data_line.startswith('{'):
                data = json.loads(data_line)
                return RadarReading(
                    timestamp=time.time(),
                    unit=data.get('units', ''),
                    magnitude=data.get('mag', 0),
                    speed_mps=data.get('speed', None),
                    range_m=data.get('range', None),
                    raw_data=data
                )
            
            # Parse simple format: {speed} {unit}
            parts = data_line.strip().split()
            if len(parts) >= 2:
                try:
                    speed = float(parts[0])
                    unit = parts[1]
                    
                    return RadarReading(
                        timestamp=time.time(),
                        unit=unit,
                        magnitude=0,
                        speed_mps=speed if unit == 'mps' else None,
                        raw_data={'raw': data_line}
                    )
                except ValueError:
                    pass
                    
        except Exception as e:
            logger.debug(f"Failed to parse radar data: {data_line} - {e}")
            
        return None
    
    def disconnect(self):
        """Disconnect from radar sensor"""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
        logger.info("Disconnected from OPS243-C radar")

class SpeedAnalysisService:
    """
    Main speed analysis service using OPS243-C radar
    Processes radar data for vehicle speed detection
    """
    
    def __init__(self, radar_port='/dev/ttyACM0'):
        # Radar disabled for troubleshooting IMX500 only
        self.radar = None
        self.is_running = False
        self.raw_readings = deque(maxlen=1000)
        self.speed_detections = deque(maxlen=100)
        self.current_detection = None
        self.detection_timeout = 3.0  # seconds
        
    def start_analysis(self):
        """Start speed analysis service (disabled during IMX500 troubleshooting)"""
        logger.info("Speed analysis disabled; skipping start.")
        return False
    
    def _analysis_loop(self):
        """Main analysis loop"""
        while self.is_running:
            try:
                reading = self.radar.read_data()
                if reading:
                    self.raw_readings.append(reading)
                    self._process_reading(reading)
                
                time.sleep(0.01)  # 100Hz processing rate
                
            except Exception as e:
                logger.error(f"Analysis loop error: {e}")
    
    def _process_reading(self, reading):
        """Process a single radar reading"""
        try:
            # Check if this reading indicates vehicle presence
            if self._is_vehicle_detected(reading):
                if not self.current_detection:
                    # Start new detection
                    self.current_detection = {
                        'id': f"speed_{int(time.time())}",
                        'start_time': reading.timestamp,
                        'readings': [reading],
                        'speeds': []
                    }
                else:
                    # Add to existing detection
                    self.current_detection['readings'].append(reading)
                    
                # Update speeds if available
                if reading.speed_mps is not None:
                    self.current_detection['speeds'].append(reading.speed_mps)
            
            else:
                # Check if we should finalize current detection
                if self.current_detection:
                    time_since_start = reading.timestamp - self.current_detection['start_time']
                    if time_since_start > self.detection_timeout:
                        self._finalize_detection()
                        
        except Exception as e:
            logger.error(f"Error processing reading: {e}")
    
    def _is_vehicle_detected(self, reading):
        """Determine if reading indicates vehicle presence"""
        # Simple threshold-based detection
        if reading.magnitude > 50:  # Adjust threshold as needed
            return True
        if reading.speed_mps and abs(reading.speed_mps) > 0.5:
            return True
        return False
    
    def _finalize_detection(self):
        """Finalize and store current detection"""
        if not self.current_detection or not self.current_detection['speeds']:
            self.current_detection = None
            return
            
        try:
            readings = self.current_detection['readings']
            speeds = self.current_detection['speeds']
            
            detection = SpeedDetection(
                detection_id=self.current_detection['id'],
                start_time=self.current_detection['start_time'],
                end_time=readings[-1].timestamp,
                peak_magnitude=max(r.magnitude for r in readings),
                avg_magnitude=statistics.mean(r.magnitude for r in readings),
                speeds=speeds,
                avg_speed_mps=statistics.mean(speeds),
                max_speed_mps=max(speeds),
                direction=self._determine_direction(speeds),
                confidence=self._calculate_confidence(readings, speeds),
                range_readings=[r.range_m for r in readings if r.range_m is not None]
            )
            
            self.speed_detections.append(detection)
            logger.info(f"Speed detection: {detection.avg_speed_mps:.2f} m/s ({detection.direction})")
            
        except Exception as e:
            logger.error(f"Error finalizing detection: {e}")
        finally:
            self.current_detection = None
    
    def _determine_direction(self, speeds):
        """Determine vehicle direction from speed readings"""
        if not speeds:
            return 'unknown'
        
        avg_speed = statistics.mean(speeds)
        if avg_speed > 0.5:
            return 'approaching'
        elif avg_speed < -0.5:
            return 'receding'
        else:
            return 'stationary'
    
    def _calculate_confidence(self, readings, speeds):
        """Calculate confidence score for detection"""
        if not readings or not speeds:
            return 0.0
        
        # Simple confidence based on reading consistency
        speed_std = statistics.stdev(speeds) if len(speeds) > 1 else 0
        magnitude_consistency = len([r for r in readings if r.magnitude > 30]) / len(readings)
        
        confidence = magnitude_consistency * (1.0 - min(speed_std / 10.0, 1.0))
        return max(0.0, min(1.0, confidence))
    
    def stop_analysis(self):
        """Stop speed analysis service"""
        self.is_running = False
        if getattr(self, 'radar', None):
            try:
                self.radar.disconnect()
            except Exception:
                pass
        logger.info("Speed analysis service stopped")
    
    def get_recent_detections(self, seconds=60):
        """Get speed detections from the last N seconds"""
        current_time = time.time()
        recent_detections = []
        
        for detection in self.speed_detections:
            if current_time - detection.end_time <= seconds:
                recent_detections.append(detection)
                
        return recent_detections

if __name__ == "__main__":
    # Test the speed analysis service
    service = SpeedAnalysisService()
    
    try:
        if service.start_analysis():
            time.sleep(60)  # Run for 60 seconds
        else:
            logger.error("Failed to start speed analysis service")
    finally:
        service.stop_analysis()
