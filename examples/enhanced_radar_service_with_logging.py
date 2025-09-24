#!/usr/bin/env python3
"""
Enhanced Radar Service with Centralized Logging and Debugging
Demonstrates integration with shared logging infrastructure
"""

import time
import json
import threading
from typing import Dict, Optional, Any
import serial

# Import centralized logging
from edge_processing.shared_logging import get_radar_logger, CorrelationContext

class EnhancedRadarService:
    """Radar service with enhanced logging and debugging"""
    
    def __init__(self, port: str = "/dev/ttyUSB0", baud_rate: int = 9600):
        # Initialize centralized logging
        self.service_logger = get_radar_logger()
        self.logger = self.service_logger.get_logger()
        
        self.port = port
        self.baud_rate = baud_rate
        self.ser = None
        self.running = False
        
        # Performance tracking
        self.stats = {
            'readings_processed': 0,
            'significant_detections': 0,
            'errors': 0,
            'last_detection_time': None
        }
        
        # Log service initialization
        self.service_logger.log_service_start({
            'port': port,
            'baud_rate': baud_rate,
            'service_version': '2.0.0'
        })
    
    def start(self):
        """Start radar service with comprehensive logging"""
        start_time = time.time()
        
        try:
            # Connection attempt with timing
            self.logger.info(f"🔌 Connecting to radar at {self.port}:{self.baud_rate}")
            
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                timeout=1.0,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS
            )
            
            connection_time = (time.time() - start_time) * 1000
            self.service_logger.log_performance("radar_connection", connection_time)
            
            # Configure radar
            self._configure_radar()
            
            self.running = True
            self.logger.info("✅ Radar service started successfully")
            
            # Start monitoring thread
            monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            monitor_thread.start()
            
        except Exception as e:
            self.service_logger.log_error_with_context(e, {
                'port': self.port,
                'baud_rate': self.baud_rate,
                'connection_time_ms': (time.time() - start_time) * 1000
            })
            raise
    
    def _configure_radar(self):
        """Configure radar with detailed logging"""
        
        with CorrelationContext(self.service_logger) as correlation_id:
            self.logger.info(f"🔧 Configuring radar (correlation: {correlation_id})")
            
            commands = [
                ('OF', 'Set units to feet per second'),
                ('OM', 'Set units to miles per hour'),  
                ('OJ', 'Set JSON output format'),
                ('AL15', 'Set low alert to 15 mph'),
                ('AH45', 'Set high alert to 45 mph'),
                ('AE', 'Enable alert reporting')
            ]
            
            config_start = time.time()
            
            for cmd, description in commands:
                cmd_start = time.time()
                
                try:
                    self.logger.debug(f"📤 Sending command: {cmd} ({description})")
                    self.ser.write(f'{cmd}\\n'.encode())
                    time.sleep(0.2)
                    
                    # Read response
                    if self.ser.in_waiting > 0:
                        response = self.ser.read(self.ser.in_waiting).decode('utf-8', errors='ignore').strip()
                        if response:
                            self.logger.debug(f"📥 Response: {response}")
                    
                    cmd_time = (time.time() - cmd_start) * 1000
                    self.service_logger.log_performance(f"radar_cmd_{cmd}", cmd_time)
                    
                except Exception as e:
                    self.service_logger.log_error_with_context(e, {
                        'command': cmd,
                        'description': description
                    })
            
            total_config_time = (time.time() - config_start) * 1000
            self.service_logger.log_performance("radar_configuration", total_config_time)
            
            self.logger.info("✅ Radar configuration completed")
    
    def _monitor_loop(self):
        """Main monitoring loop with enhanced debugging"""
        
        self.logger.info("🔍 Starting radar monitoring loop")
        
        while self.running:
            try:
                if self.ser and self.ser.in_waiting > 0:
                    raw_data = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    
                    if raw_data:
                        self._process_radar_reading(raw_data)
                
                time.sleep(0.1)  # Small delay to prevent CPU spinning
                
            except Exception as e:
                self.stats['errors'] += 1
                self.service_logger.log_error_with_context(e, {
                    'loop_iteration': self.stats['readings_processed'],
                    'uptime_seconds': time.time() - getattr(self, 'start_time', time.time())
                })
                time.sleep(1)  # Longer delay on error
    
    def _process_radar_reading(self, raw_data: str):
        """Process radar reading with comprehensive logging"""
        
        processing_start = time.time()
        
        with CorrelationContext(self.service_logger) as correlation_id:
            
            self.stats['readings_processed'] += 1
            
            # Parse radar data
            parsed_data = self._parse_radar_data(raw_data)
            
            if parsed_data:
                # Check for significant detection
                if 'speed' in parsed_data and parsed_data['speed'] > 15:
                    self.stats['significant_detections'] += 1
                    self.stats['last_detection_time'] = time.time()
                    
                    # Log significant detection with full context
                    self.logger.info(f"🚛 Vehicle detected: {parsed_data['speed']:.1f} mph", extra={
                        'event_type': 'vehicle_detection',
                        'speed_mph': parsed_data['speed'],
                        'raw_data': raw_data,
                        'detection_number': self.stats['significant_detections']
                    })
                    
                    # Publish to Redis (existing functionality)
                    self._publish_to_redis(parsed_data)
                    
                else:
                    # Debug logging for non-significant readings
                    self.logger.debug(f"📊 Radar reading: {raw_data[:50]}", extra={
                        'event_type': 'radar_reading',
                        'raw_data': raw_data,
                        'parsed': parsed_data
                    })
            
            processing_time = (time.time() - processing_start) * 1000
            
            # Log performance for significant detections only
            if 'speed' in (parsed_data or {}) and parsed_data['speed'] > 15:
                self.service_logger.log_performance("radar_processing", processing_time, {
                    'speed': parsed_data['speed'],
                    'data_length': len(raw_data)
                })
    
    def _parse_radar_data(self, raw_data: str) -> Optional[Dict]:
        """Parse radar data with error handling"""
        
        try:
            # Try JSON format first
            if raw_data.startswith('{'):
                return json.loads(raw_data)
            
            # Try speed pattern
            import re
            speed_match = re.search(r'([+-]?\\d+\\.?\\d*)\\s*(mph|fps|m/s)?', raw_data)
            if speed_match:
                speed = float(speed_match.group(1))
                unit = speed_match.group(2) or 'mph'
                
                return {
                    'speed': abs(speed),
                    'unit': unit,
                    'timestamp': time.time(),
                    'raw': raw_data
                }
            
            return None
            
        except Exception as e:
            self.service_logger.log_error_with_context(e, {
                'raw_data': raw_data,
                'parsing_attempt': 'radar_data'
            })
            return None
    
    def _publish_to_redis(self, data: Dict):
        """Publish to Redis with logging"""
        
        try:
            # Redis publishing logic here
            self.logger.debug("📡 Publishing to Redis", extra={
                'event_type': 'redis_publish',
                'data_keys': list(data.keys()) if data else []
            })
            
        except Exception as e:
            self.service_logger.log_error_with_context(e, {
                'data': data,
                'operation': 'redis_publish'
            })
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get service health with comprehensive metrics"""
        
        uptime = time.time() - getattr(self, 'start_time', time.time())
        
        return {
            'status': 'healthy' if self.running and self.ser and self.ser.is_open else 'unhealthy',
            'uptime_seconds': uptime,
            'readings_processed': self.stats['readings_processed'],
            'significant_detections': self.stats['significant_detections'],
            'error_count': self.stats['errors'],
            'detection_rate': self.stats['significant_detections'] / (uptime / 3600) if uptime > 0 else 0,
            'last_detection': self.stats['last_detection_time'],
            'port': self.port,
            'baud_rate': self.baud_rate
        }
    
    def stop(self):
        """Stop service with cleanup logging"""
        
        self.logger.info("🛑 Stopping radar service")
        
        self.running = False
        
        if self.ser:
            self.ser.close()
        
        # Log final statistics
        health = self.get_health_status()
        self.logger.info("📊 Final service statistics", extra={
            'event_type': 'service_stats',
            'stats': health
        })
        
        self.service_logger.log_service_stop()


if __name__ == "__main__":
    service = EnhancedRadarService()
    
    try:
        service.start()
        
        # Keep running
        while True:
            time.sleep(60)
            
            # Log health status every minute
            health = service.get_health_status()
            service.logger.info(f"💓 Service health check", extra={
                'event_type': 'health_check',
                'health': health
            })
            
    except KeyboardInterrupt:
        service.stop()
    except Exception as e:
        service.service_logger.log_error_with_context(e, {'phase': 'main_execution'})
        service.stop()
        raise