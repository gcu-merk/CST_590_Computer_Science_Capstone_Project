#!/usr/bin/env python3
"""
Fixed OPS243-C Radar Service with proper command protocol
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

class RadarServiceFixed:
    """Fixed OPS243-C Radar Service with correct protocol"""
    
    def __init__(self, 
                 uart_port='/dev/ttyAMA0',
                 baudrate=9600,
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
            logger.info("🎯 Starting OPS243-C Radar Service...")
            logger.info(f"UART: {self.uart_port}")
            logger.info(f"Redis: {self.redis_host}:{self.redis_port}")
            logger.info(f"Speed Thresholds: {self.low_speed_threshold}mph (low), {self.high_speed_threshold}mph (high)")
            
            # Connect to Redis
            self.redis_client = redis.Redis(host=self.redis_host, port=self.redis_port, decode_responses=True)
            self.redis_client.ping()
            logger.info("✅ Connected to Redis")
            
            # Connect to radar
            self.ser = serial.Serial(self.uart_port, self.baudrate, timeout=1)
            time.sleep(0.5)
            logger.info("✅ Connected to radar UART")
            
            # Configure radar properly
            self._configure_radar()
            
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
    
    def _configure_radar(self):
        """Configure OPS243-C radar with proper commands"""
        logger.info("🔧 Configuring radar settings...")
        
        # Clear any existing data
        if self.ser.in_waiting > 0:
            self.ser.read(self.ser.in_waiting)
        
        # Send proper OPS243-C commands
        commands = [
            ('OF', 'Set units to feet per second'),
            ('OM', 'Set units to miles per hour'),
            ('OJ', 'Set JSON output format'),
            ('OD', 'Set Doppler output'),
            ('AL15', 'Set low alert to 15 mph'),
            ('AH45', 'Set high alert to 45 mph'),
            ('AE', 'Enable alert reporting'),
            ('R1', 'Set reporting interval to 1 second'),
            ('CT', 'Clear memory/reset'),
        ]
        
        for cmd, description in commands:
            logger.info(f"📤 {description}")
            # Send command with proper termination
            self.ser.write(f'{cmd}\\r\\n'.encode())
            time.sleep(0.3)  # Give radar time to process
            
            # Read response
            if self.ser.in_waiting > 0:
                response = self.ser.read(self.ser.in_waiting)
                try:
                    decoded = response.decode('utf-8', errors='ignore').strip()
                    if decoded and decoded not in ['(*', '(*(*', '(*(*(*']:
                        logger.info(f"📥 Response: {decoded}")
                except:
                    logger.debug(f"📥 Raw response: {response}")
        
        # Final configuration check
        self.ser.write(b'??\\r\\n')  # Query settings
        time.sleep(0.5)
        if self.ser.in_waiting > 0:
            response = self.ser.read(self.ser.in_waiting)
            logger.info(f"📥 Final config: {response}")
        
        logger.info("✅ Radar configuration completed")
    
    def _radar_loop(self):
        """Main radar reading loop"""
        logger.info("Starting radar monitoring loop...")
        
        buffer = ""
        
        while self.running:
            try:
                if self.ser and self.ser.in_waiting > 0:
                    # Read available data
                    data = self.ser.read(self.ser.in_waiting)
                    
                    # Try to decode as text
                    try:
                        text = data.decode('utf-8', errors='ignore')
                        buffer += text
                        
                        # Process complete lines
                        while '\\n' in buffer:
                            line, buffer = buffer.split('\\n', 1)
                            line = line.strip()
                            if line and line not in ['(*', '(*(*', '(*(*(*']:
                                self._process_radar_data(line)
                                
                    except UnicodeDecodeError:
                        # Handle binary data
                        self._process_binary_data(data)
                
                time.sleep(0.1)  # 10Hz sampling rate
                
            except Exception as e:
                logger.error(f"Error in radar loop: {e}")
                time.sleep(1)
    
    def _process_binary_data(self, data: bytes):
        """Process binary radar data"""
        # For now, just log that we received binary data
        if len(data) > 10:  # Only log significant data
            logger.debug(f"📊 Binary data received: {len(data)} bytes")
    
    def _process_radar_data(self, line: str):
        """Process and publish radar data"""
        data = self._parse_radar_line(line)
        if not data:
            return
        
        self.detection_count += 1
        
        # Log detection
        if 'speed' in data:
            speed = data['speed']
            logger.info(f"🚗 Vehicle detected: {speed} mph")
            
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
        """Parse radar data line with multiple format support"""
        if not line:
            return None
        
        timestamp = time.time()
        
        # Try JSON format first
        try:
            if line.startswith('{'):
                data = json.loads(line)
                data['_timestamp'] = timestamp
                data['_source'] = 'ops243_radar'
                return data
        except Exception:
            pass
        
        # Try speed format: "15.2 mph" or "15.2"
        speed_match = re.search(r'([+-]?\\d+\\.?\\d*)\\s*(mph|fps|m/s)?', line)
        if speed_match:
            try:
                speed = float(speed_match.group(1))
                unit = speed_match.group(2) or 'mph'
                
                # Convert to mph if needed
                if unit == 'fps':
                    speed = speed * 0.681818  # fps to mph
                elif unit == 'm/s':
                    speed = speed * 2.237  # m/s to mph
                
                return {
                    'speed': abs(speed),  # Always positive
                    'unit': 'mph',
                    '_raw': line,
                    '_timestamp': timestamp,
                    '_source': 'ops243_radar'
                }
            except Exception:
                pass
        
        # Unknown format - still record it for debugging
        return {
            '_raw': line,
            '_timestamp': timestamp,
            '_source': 'ops243_radar'
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
    service = RadarServiceFixed()
    
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