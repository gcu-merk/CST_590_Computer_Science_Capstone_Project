#!/usr/bin/env python3
"""
OPS243-C Radar Service
Production systemd service for radar speed detection with GPIO alerts and Redis integration
"""

import time
import serial
import json
import threading
import logging
import redis
import signal
import sys
from datetime import datetime
from typing import Callable, Optional, Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RadarService:
    """Production OPS243-C Radar Service with Redis integration"""
    
    def __init__(self, 
                 uart_port='/dev/ttyAMA0',
                 baudrate=19200,  # CORRECTED: Use 19200 baud for proper CSV data
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
        
        # Speed thresholds (configured via radar commands)
        self.low_speed_threshold = 15   # mph - triggers GPIO5 (Blue)
        self.high_speed_threshold = 45  # mph - triggers GPIO6 (Purple)
        
        # Statistics
        self.detection_count = 0
        self.startup_time = None
    
    def start(self) -> bool:
        """Start the radar service"""
        logger.info("=== OPS243-C Radar Service ===")
        logger.info(f"UART Port: {self.uart_port}")
        logger.info(f"Baudrate: {self.baudrate}")
        logger.info(f"Redis: {self.redis_host}:{self.redis_port}")
        logger.info(f"Speed Thresholds: {self.low_speed_threshold}mph (low), {self.high_speed_threshold}mph (high)")
        
        try:
            # Connect to Redis
            self.redis_client = redis.Redis(
                host=self.redis_host, 
                port=self.redis_port, 
                decode_responses=True
            )
            self.redis_client.ping()  # Test connection
            logger.info("✅ Connected to Redis")
            
            # Connect to UART
            self.ser = serial.Serial(self.uart_port, self.baudrate, timeout=2)
            time.sleep(0.5)
            logger.info("✅ Connected to radar UART")
            
            # Configure radar
            self._configure_radar()
            
            # Start background thread
            self.running = True
            self.startup_time = time.time()
            self.thread = threading.Thread(target=self._radar_loop, daemon=True)
            self.thread.start()
            
            logger.info("✅ Radar service started successfully")
            logger.info("🎯 Monitoring for vehicle detections...")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start radar service: {e}")
            return False
    
    def _configure_radar(self):
        """Configure radar with speed alerts"""
        logger.info("🔧 Configuring radar settings...")
        
        commands = [
            ('OJ', 'Set JSON output mode'),
            (f'AL{self.low_speed_threshold:02d}', f'Set low speed alert to {self.low_speed_threshold} mph'),
            (f'AH{self.high_speed_threshold:02d}', f'Set high speed alert to {self.high_speed_threshold} mph'),
            ('AE', 'Enable speed alerts'),
            ('OJ', 'Confirm JSON mode')
        ]
        
        for cmd, description in commands:
            logger.info(f"📤 {description}")
            self.ser.write(f'{cmd}\n'.encode())
            time.sleep(0.2)
            
            # Read any response
            if self.ser.in_waiting > 0:
                response = self.ser.read(self.ser.in_waiting).decode('utf-8', errors='ignore').strip()
                if response:
                    logger.info(f"📥 Response: {response}")
        
        logger.info("✅ Radar configuration completed")
    
    def _radar_loop(self):
        """Main radar reading loop"""
        logger.info("Starting radar monitoring loop...")
        
        while self.running:
            try:
                if self.ser and self.ser.in_waiting > 0:
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
            logger.info(f"🚗 Vehicle detected: {speed} mph")
            
            # Check speed thresholds
            if speed >= self.high_speed_threshold:
                logger.warning(f"🚨 HIGH SPEED ALERT: {speed} mph (GPIO6/Purple should trigger)")
                data['alert_level'] = 'high'
            elif speed >= self.low_speed_threshold:
                logger.info(f"⚠️  LOW SPEED ALERT: {speed} mph (GPIO5/Blue should trigger)")
                data['alert_level'] = 'low'
            else:
                logger.info(f"✅ Normal speed: {speed} mph")
                data['alert_level'] = 'normal'
        else:
            logger.debug(f"📊 Radar data: {data}")
        
        # Publish to Redis
        self._publish_to_redis(data)
    
    def _parse_radar_line(self, line: str) -> Optional[Dict]:
        """Parse radar data line with CSV support"""
        if not line:
            return None
        
        timestamp = time.time()
        
        # Try CSV format first: "m",0.7 (magnitude, speed)
        import re
        csv_match = re.match(r'^"([^"]+)",([\\d\\.]+)$', line)
        if csv_match:
            try:
                magnitude = csv_match.group(1)
                speed_raw = float(csv_match.group(2))
                speed = abs(speed_raw)  # Ensure positive speed
                
                return {
                    'speed': speed,
                    'magnitude': magnitude,
                    'unit': 'mph',
                    '_raw': line,
                    '_timestamp': timestamp,
                    '_source': 'ops243_radar'
                }
            except Exception:
                pass
        
        # Try JSON format
        try:
            if line.startswith('{'):
                data = json.loads(line)
                data['_timestamp'] = timestamp
                data['_source'] = 'ops243_radar'
                return data
        except Exception:
            pass
        
        # Try simple format: "speed unit"
        parts = line.split()
        if len(parts) >= 2:
            try:
                speed = float(parts[0])
                unit = parts[1]
                return {
                    'speed': speed,
                    'unit': unit,
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
            # Publish to radar channel
            self.redis_client.publish('radar_detections', json.dumps(data))
            
            # Store in radar data stream
            self.redis_client.xadd('radar_data', data)
            
            # Update statistics
            stats = {
                'last_detection': data.get('_timestamp', time.time()),
                'detection_count': self.detection_count,
                'uptime': time.time() - self.startup_time if self.startup_time else 0
            }
            self.redis_client.hmset('radar_stats', stats)
            
        except Exception as e:
            logger.error(f"Error publishing to Redis: {e}")
    
    def stop(self):
        """Stop the radar service"""
        logger.info("🛑 Stopping radar service...")
        
        self.running = False
        
        if self.thread:
            self.thread.join(timeout=5)
        
        if self.ser:
            try:
                self.ser.close()
            except Exception:
                pass
        
        if self.redis_client:
            try:
                # Final stats update
                if self.startup_time:
                    uptime = time.time() - self.startup_time
                    logger.info(f"📊 Service uptime: {uptime:.1f}s, detections: {self.detection_count}")
            except Exception:
                pass
        
        logger.info("✅ Radar service stopped")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    if 'service' in globals():
        service.stop()
    sys.exit(0)

def main():
    """Main service entry point"""
    # Set up signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Create and start service
    service = RadarService()
    
    if service.start():
        logger.info("Radar service running. Press Ctrl+C to stop.")
        try:
            # Keep main thread alive
            while service.running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            service.stop()
    else:
        logger.error("Failed to start radar service")
        sys.exit(1)

if __name__ == '__main__':
    main()