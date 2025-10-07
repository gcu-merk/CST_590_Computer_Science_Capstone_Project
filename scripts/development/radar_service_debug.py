#!/usr/bin/env python3
"""
Simplified Radar Service for Debugging
Basic radar service to isolate and fix the monitoring loop issues
"""

import time
import serial
import json
import threading
import redis
import signal
import sys
import os
import uuid
from datetime import datetime
from typing import Optional, Dict
import logging

# Set up basic logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('radar-debug')

class RadarServiceDebug:
    """Simplified Radar Service for debugging monitoring loop issues"""
    
    def __init__(self, 
                 uart_port='/dev/ttyAMA0',
                 baudrate=19200,
                 redis_host='localhost',
                 redis_port=6379):
        
        # Service configuration
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
        self.motion_threshold = 2.0  # mph
        
        # Statistics
        self.detection_count = 0
        self.startup_time = None
        
        logger.info("Radar debug service initialized")

    def start(self) -> bool:
        """Start the simplified radar service"""
        
        logger.info("Starting radar debug service...")
        
        try:
            # Connect to Redis
            logger.info("Connecting to Redis...")
            self.redis_client = redis.Redis(
                host=self.redis_host, 
                port=self.redis_port, 
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info("✅ Connected to Redis successfully")
            
            # Connect to UART
            logger.info(f"Connecting to UART {self.uart_port}...")
            self.ser = serial.Serial(self.uart_port, self.baudrate, timeout=2)
            time.sleep(0.5)
            logger.info("✅ Connected to radar UART successfully")
            
            # Start background monitoring thread
            self.running = True
            self.startup_time = time.time()
            self.thread = threading.Thread(target=self._radar_loop_debug, daemon=True)
            self.thread.start()
            
            logger.info("✅ Radar debug service started successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start radar service: {str(e)}", exc_info=True)
            return False

    def _radar_loop_debug(self):
        """Simplified radar monitoring loop for debugging"""
        
        logger.info("Starting debug radar monitoring loop")
        
        loop_iterations = 0
        last_stats_log = time.time()
        
        while self.running:
            try:
                loop_iterations += 1
                
                if self.ser and self.ser.in_waiting > 0:
                    # Read raw data
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        logger.debug(f"Raw radar data: {repr(line)}")
                        self._process_radar_data_debug(line)
                
                # Log stats every minute
                if time.time() - last_stats_log > 60:
                    logger.info(f"Debug stats: {loop_iterations} iterations, {self.detection_count} detections")
                    last_stats_log = time.time()
                    loop_iterations = 0
                
                time.sleep(0.1)  # 10Hz sampling for debugging
                
            except Exception as e:
                logger.error(f"Error in debug radar loop: {str(e)}", exc_info=True)
                time.sleep(1)
        
        logger.info("Debug radar monitoring loop stopped")

    def _process_radar_data_debug(self, line: str):
        """Simplified radar data processing for debugging"""
        
        try:
            logger.debug(f"Processing line: {repr(line)}")
            
            data = self._parse_radar_line_debug(line)
            if not data:
                logger.debug("No parseable data")
                return
            
            # Check for motion
            if 'speed' in data:
                speed = float(data['speed'])
                logger.debug(f"Parsed speed: {speed} mph")
                
                if speed >= self.motion_threshold:
                    self.detection_count += 1
                    detection_id = str(uuid.uuid4())[:8]
                    
                    logger.info(f"🚗 Motion detected: {speed:.1f} mph (detection #{self.detection_count})")
                    
                    # Publish to Redis
                    try:
                        redis_data = {
                            'detection_id': detection_id,
                            'speed': speed,
                            'timestamp': time.time(),
                            'service': 'radar-debug'
                        }
                        self.redis_client.xadd('traffic:radar', redis_data)
                        logger.info(f"📡 Published to Redis: traffic:radar")
                    except Exception as e:
                        logger.error(f"Failed to publish to Redis: {e}")
                else:
                    logger.debug(f"Speed {speed:.1f} mph below threshold")
            
        except Exception as e:
            logger.error(f"Error processing radar data: {str(e)}", exc_info=True)

    def _parse_radar_line_debug(self, line: str) -> Optional[Dict]:
        """Simplified radar data parsing for debugging"""
        
        if not line or not line.strip():
            return None
        
        line = line.strip()
        
        try:
            # Try CSV format: "m",12.3
            if '"' in line and ',' in line:
                parts = line.replace('"', '').split(',')
                if len(parts) == 2:
                    try:
                        speed = abs(float(parts[1]))
                        return {'speed': speed, 'format': 'csv', 'raw': line}
                    except ValueError:
                        pass
            
            # Try JSON format
            if line.startswith('{') and line.endswith('}'):
                try:
                    data = json.loads(line)
                    if 'speed' in data:
                        speed_raw = data['speed']
                        # Handle different units
                        if data.get('unit') == 'mps':
                            speed = abs(float(speed_raw) * 2.237)  # Convert m/s to mph
                        else:
                            speed = abs(float(speed_raw))
                        return {'speed': speed, 'format': 'json', 'raw': line}
                except (json.JSONDecodeError, ValueError):
                    pass
            
            # Try simple numeric
            try:
                speed = abs(float(line))
                return {'speed': speed, 'format': 'numeric', 'raw': line}
            except ValueError:
                pass
            
            # Try space-separated
            parts = line.split()
            if len(parts) >= 2:
                try:
                    speed = abs(float(parts[0]))
                    return {'speed': speed, 'format': 'space_separated', 'raw': line}
                except ValueError:
                    pass
        
        except Exception as e:
            logger.debug(f"Parse exception: {e}")
        
        logger.debug(f"Unrecognized format: {repr(line)}")
        return None

    def stop(self):
        """Stop the debug service"""
        logger.info("Stopping radar debug service...")
        self.running = False
        
        if self.thread:
            self.thread.join(timeout=5)
        
        if self.ser:
            try:
                self.ser.close()
            except Exception as e:
                pass
        
        logger.info("Radar debug service stopped")

def main():
    """Main entry point for debug service"""
    
    # Set up signal handlers
    def signal_handler(signum, frame):
        print(f"Received signal {signum}, shutting down...")
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Create debug service
    service = RadarServiceDebug()
    
    if service.start():
        print("Debug radar service running. Press Ctrl+C to stop.")
        try:
            while service.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nReceived interrupt signal...")
        finally:
            service.stop()
    else:
        print("Failed to start debug radar service")
        sys.exit(1)

if __name__ == '__main__':
    main()