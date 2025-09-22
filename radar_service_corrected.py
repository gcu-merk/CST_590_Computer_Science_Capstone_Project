#!/usr/bin/env python3
"""
Corrected OPS243-C Radar Service - 19200 baud with CSV parsing
"""

import time
import serial
import json
import threading
import logging
import redis
import signal
import sys
import re
from datetime import datetime
from typing import Callable, Optional, Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RadarServiceCorrected:
    """Corrected OPS243-C Radar Service with proper baud rate and CSV parsing"""
    
    def __init__(self, 
                 uart_port='/dev/ttyAMA0',
                 baudrate=19200,  # CORRECTED: Use 19200 baud
                 redis_host='localhost',
                 redis_port=6379):
        self.uart_port = uart_port
        self.baudrate = baudrate
        self.redis_host = redis_host
        self.redis_port = redis_port
        
        # Service state
        self.running = False
        self.ser = None
        self.redis_client = None
        self.thread = None
        
        # Speed thresholds
        self.low_speed_threshold = 15   # mph
        self.high_speed_threshold = 45  # mph
        
        # Statistics
        self.detection_count = 0
        self.startup_time = None
        
        # Signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)
    
    def start(self) -> bool:
        """Start the radar service"""
        try:
            self.startup_time = datetime.now()
            logger.info("🎯 Starting OPS243-C Radar Service (CORRECTED)")
            logger.info(f"UART: {self.uart_port} at {self.baudrate} baud")
            logger.info(f"Redis: {self.redis_host}:{self.redis_port}")
            logger.info(f"Speed Thresholds: {self.low_speed_threshold}mph (low), {self.high_speed_threshold}mph (high)")
            
            # Connect to Redis
            self.redis_client = redis.Redis(host=self.redis_host, port=self.redis_port, decode_responses=True)
            self.redis_client.ping()
            logger.info("✅ Connected to Redis")
            
            # Connect to radar with CORRECT baud rate
            self.ser = serial.Serial(self.uart_port, self.baudrate, timeout=1)
            time.sleep(0.5)
            logger.info("✅ Connected to radar UART at 19200 baud")
            
            # Clear any existing data
            if self.ser.in_waiting > 0:
                self.ser.read(self.ser.in_waiting)
                logger.info("📝 Cleared existing buffer data")
            
            # Start monitoring thread
            self.running = True
            self.thread = threading.Thread(target=self._radar_loop, daemon=False)
            self.thread.start()
            
            logger.info("✅ Radar service started successfully")
            logger.info("🎯 Monitoring for vehicle detections...")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start radar service: {e}")
            return False
    
    def _radar_loop(self):
        """Main radar reading loop"""
        logger.info("Starting radar monitoring loop...")
        
        while self.running:
            try:
                if self.ser and self.ser.in_waiting > 0:
                    # Read line-by-line
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        self._process_radar_data(line)
                
                time.sleep(0.05)  # 20Hz sampling rate
                
            except Exception as e:
                logger.error(f"Error in radar loop: {e}")
                time.sleep(1)
    
    def _process_radar_data(self, line: str):
        """Process and publish radar data"""
        data = self._parse_radar_line(line)
        if not data:
            return
        
        self.detection_count += 1
        
        # Log detection
        if 'speed' in data:
            speed = data['speed']
            magnitude = data.get('magnitude', 'unknown')
            logger.info(f"🚗 Vehicle detected: {speed} mph (magnitude: {magnitude})")
            
            # Check speed thresholds
            if speed >= self.high_speed_threshold:
                logger.warning(f"🚨 HIGH SPEED ALERT: {speed} mph")
                data['alert_level'] = 'high'
            elif speed >= self.low_speed_threshold:
                logger.info(f"⚠️  LOW SPEED ALERT: {speed} mph")
                data['alert_level'] = 'low'
            else:
                logger.info(f"✅ Normal speed: {speed} mph")
                data['alert_level'] = 'normal'
        else:
            logger.debug(f"📊 Radar data: {data}")
        
        # Publish to Redis
        self._publish_to_redis(data)
    
    def _parse_radar_line(self, line: str) -> Optional[Dict]:
        """Parse radar CSV data line"""
        if not line:
            return None
        
        timestamp = time.time()
        
        # Parse CSV format: "m",0.7
        # Format appears to be: "magnitude",speed
        csv_match = re.match(r'^"([^"]+)",([\\d\\.]+)$', line)
        if csv_match:
            try:
                magnitude = csv_match.group(1)
                speed_raw = float(csv_match.group(2))
                
                # The speed appears to already be in reasonable units
                # Convert to mph if needed (this may need adjustment based on actual units)
                speed = abs(speed_raw)  # Ensure positive speed
                
                return {
                    'speed': speed,
                    'magnitude': magnitude,
                    'unit': 'mph',
                    '_raw': line,
                    '_timestamp': timestamp,
                    '_source': 'ops243_radar_corrected'
                }
            except Exception as e:
                logger.debug(f"Failed to parse CSV: {e}")
        
        # Try other formats as fallback
        speed_match = re.search(r'([+-]?\\d+\\.?\\d*)\\s*(mph|fps|m/s)?', line)
        if speed_match:
            try:
                speed = float(speed_match.group(1))
                unit = speed_match.group(2) or 'unknown'
                
                return {
                    'speed': abs(speed),
                    'unit': unit,
                    '_raw': line,
                    '_timestamp': timestamp,
                    '_source': 'ops243_radar_corrected'
                }
            except Exception:
                pass
        
        # Unknown format - still record for debugging
        logger.debug(f"Unknown radar format: {line}")
        return {
            '_raw': line,
            '_timestamp': timestamp,
            '_source': 'ops243_radar_corrected'
        }
    
    def _publish_to_redis(self, data: Dict):
        """Publish radar data to Redis"""
        try:
            if self.redis_client:
                # Store latest detection
                key = "radar:latest"
                self.redis_client.set(key, json.dumps(data), ex=300)  # 5 min TTL
                
                # Store in time series
                ts_key = f"radar:detections:{int(time.time())}"
                self.redis_client.set(ts_key, json.dumps(data), ex=86400)  # 24 hour TTL
                
                # Update statistics
                stats_key = "radar:stats"
                self.redis_client.hset(stats_key, mapping={
                    'detection_count': self.detection_count,
                    'last_detection': time.time(),
                    'startup_time': self.startup_time.isoformat() if self.startup_time else None
                })
                
        except Exception as e:
            logger.error(f"Failed to publish to Redis: {e}")
    
    def stop(self):
        """Stop the radar service"""
        logger.info("🛑 Stopping radar service...")
        self.running = False
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        
        if self.ser:
            self.ser.close()
        
        logger.info("✅ Radar service stopped")
    
    def get_stats(self) -> Dict:
        """Get service statistics"""
        return {
            'running': self.running,
            'detection_count': self.detection_count,
            'startup_time': self.startup_time.isoformat() if self.startup_time else None,
            'thresholds': {
                'low': self.low_speed_threshold,
                'high': self.high_speed_threshold
            }
        }

if __name__ == "__main__":
    service = RadarServiceCorrected()
    
    if service.start():
        logger.info("Radar service running. Press Ctrl+C to stop.")
        try:
            # Keep main thread alive
            while service.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        finally:
            service.stop()
    else:
        logger.error("Failed to start radar service")
        sys.exit(1)