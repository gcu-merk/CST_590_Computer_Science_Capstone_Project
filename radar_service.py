#!/usr/bin/env python3
"""
OPS243-C Radar Service with Centralized Logging
Enhanced production radar service with correlation tracking and performance monitoring
Version: 2.1.2 - Enhanced monitoring loop error handling (Sept 26, 2025)

NOTE: This is the PRODUCTION version used by docker-compose.yml
      Restored from scripts/deprecated/ to maintain docker-compose compatibility.
      Do not move this file - it is referenced by: command: ["python", "radar_service.py"]
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
from typing import Callable, Optional, Dict

# Import centralized logging infrastructure
from edge_processing.shared_logging import ServiceLogger, CorrelationContext, performance_monitor

class RadarServiceEnhanced:
    """Enhanced OPS243-C Radar Service with centralized logging and correlation tracking"""
    
    def __init__(self, 
                 uart_port='/dev/ttyAMA0',
                 baudrate=19200,
                 redis_host='localhost',
                 redis_port=6379):
        
        # Initialize centralized logger
        self.logger = ServiceLogger(
            service_name="radar-service",
            service_version="2.1.2",
            environment=os.environ.get('ENVIRONMENT', 'production')
        )
        
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
        
        # Speed thresholds (configured via radar commands)
        self.low_speed_threshold = 2    # mph - triggers GPIO5 (Blue)
        self.high_speed_threshold = 26   # mph - realistic upper limit for traffic monitoring
        
        # Statistics
        self.detection_count = 0
        self.startup_time = None
        
        # Performance tracking
        self.last_detection_time = None
        self.processing_times = []

    def start(self) -> bool:
        """Start the radar service with full correlation tracking"""
        
        # Create correlation context for startup process
        with CorrelationContext.create("radar_service_startup") as ctx:
            self.logger.log_service_event(
                event_type="service_startup_initiated",
                message="OPS243-C Radar Service startup initiated",
                details={
                    "uart_port": self.uart_port,
                    "baudrate": self.baudrate,
                    "redis_host": self.redis_host,
                    "redis_port": self.redis_port,
                    "speed_thresholds": {
                        "low": self.low_speed_threshold,
                        "high": self.high_speed_threshold
                    }
                }
            )
            
            try:
                # Connect to Redis with performance monitoring
                with performance_monitor("redis_connection"):
                    self.redis_client = redis.Redis(
                        host=self.redis_host, 
                        port=self.redis_port, 
                        decode_responses=True
                    )
                    self.redis_client.ping()
                
                self.logger.log_service_event(
                    event_type="redis_connection_success",
                    message="✅ Connected to Redis successfully"
                )
                
                # Connect to UART with performance monitoring
                with performance_monitor("uart_connection"):
                    self.ser = serial.Serial(self.uart_port, self.baudrate, timeout=2)
                    time.sleep(0.5)
                
                self.logger.log_service_event(
                    event_type="uart_connection_success",
                    message="✅ Connected to radar UART successfully"
                )
                
                # Configure radar with correlation tracking
                self._configure_radar_enhanced()
                
                # Start background monitoring thread
                self.running = True
                self.startup_time = time.time()
                self.thread = threading.Thread(target=self._radar_loop_enhanced, daemon=True)
                self.thread.start()
                
                self.logger.log_service_event(
                    event_type="service_startup_complete",
                    message="✅ Radar service started successfully - monitoring for vehicles",
                    details={"thread_id": self.thread.ident}
                )
                
                return True
                
            except Exception as e:
                self.logger.log_error(
                    error_type="service_startup_failed",
                    message=f"❌ Failed to start radar service: {str(e)}",
                    exception=e,
                    details={
                        "uart_port": self.uart_port,
                        "redis_connection": f"{self.redis_host}:{self.redis_port}"
                    }
                )
                return False

    def _configure_radar_enhanced(self):
        """Configure radar with enhanced logging and error handling"""
        
        with CorrelationContext.create("radar_configuration") as ctx:
            self.logger.log_service_event(
                event_type="radar_configuration_started",
                message="🔧 Starting radar configuration process"
            )
            
            commands = [
                ('OJ', 'Set JSON output mode'),
                (f'AL{self.low_speed_threshold:02d}', f'Set low speed alert to {self.low_speed_threshold} mph'),
                (f'AH{self.high_speed_threshold:02d}', f'Set high speed alert to {self.high_speed_threshold} mph'),
                ('AE', 'Enable speed alerts'),
                ('OJ', 'Confirm JSON mode')
            ]
            
            successful_commands = 0
            
            for cmd, description in commands:
                try:
                    self.logger.debug(f"📤 Sending command: {description}")
                    
                    # Clear any pending data first
                    if self.ser.in_waiting > 0:
                        self.ser.read(self.ser.in_waiting)
                    
                    # Send command with proper line ending
                    self.ser.write(f'{cmd}\r\n'.encode())
                    self.ser.flush()  # Ensure command is sent
                    time.sleep(0.5)  # Increased delay for radar response
                    
                    # Read response with timeout
                    response_data = []
                    timeout_count = 0
                    while timeout_count < 10:  # 1 second timeout total
                        if self.ser.in_waiting > 0:
                            data = self.ser.read(self.ser.in_waiting).decode('utf-8', errors='ignore')
                            response_data.append(data)
                            break
                        time.sleep(0.1)
                        timeout_count += 1
                    
                    response = ''.join(response_data).strip()
                    if response:
                        self.logger.debug(f"📥 Command response: {repr(response)}")
                    else:
                        self.logger.debug(f"⚠️  No response to command: {cmd}")
                    
                    successful_commands += 1
                    
                except Exception as e:
                    self.logger.log_error(
                        error_type="radar_command_failed",
                        message=f"Failed to send radar command: {cmd}",
                        exception=e,
                        details={
                            "command": cmd, 
                            "description": description,
                            "serial_port": str(self.ser),
                            "is_open": self.ser.is_open if self.ser else False
                        }
                    )
            
            self.logger.log_service_event(
                event_type="radar_configuration_complete",
                message="✅ Radar configuration completed",
                details={
                    "total_commands": len(commands),
                    "successful_commands": successful_commands
                }
            )

    def _radar_loop_enhanced(self):
        """Enhanced radar monitoring loop with correlation tracking"""
        
        with CorrelationContext.create("radar_monitoring_session") as ctx:
            self.logger.log_service_event(
                event_type="radar_monitoring_started",
                message="Starting enhanced radar monitoring loop with correlation tracking"
            )
            
            loop_iterations = 0
            last_stats_log = time.time()
            
            while self.running:
                try:
                    loop_iterations += 1
                    
                    if self.ser and self.ser.in_waiting > 0:
                        # Process radar data with correlation context
                        try:
                            line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                            if line:
                                self._process_radar_data_enhanced(line)
                        except Exception as data_error:
                            # Handle data processing errors separately from loop errors
                            self.logger.log_error(
                                error_type="radar_data_processing_error",
                                message="Error processing radar data (continuing monitoring)",
                                exception=data_error,
                                details={"raw_line": repr(line) if 'line' in locals() else 'unknown'}
                            )
                            # Continue monitoring despite data processing errors
                    
                    # Log periodic statistics (every 5 minutes)
                    if time.time() - last_stats_log > 300:
                        try:
                            self._log_periodic_stats(loop_iterations)
                            last_stats_log = time.time()
                            loop_iterations = 0
                        except Exception as stats_error:
                            # Log stats error but don't break the loop
                            self.logger.log_error(
                                error_type="stats_logging_error", 
                                message="Error logging statistics (continuing monitoring)",
                                exception=stats_error
                            )
                            last_stats_log = time.time()  # Reset to avoid spam
                    
                    time.sleep(0.05)  # 20Hz sampling rate
                    
                except Exception as e:
                    # Only catch truly critical loop errors (serial communication, etc.)
                    self.logger.log_error(
                        error_type="radar_loop_critical_error",
                        message="Critical error in radar monitoring loop",
                        exception=e,
                        details={"loop_iterations": loop_iterations}
                    )
                    time.sleep(1)
            
            self.logger.log_service_event(
                event_type="radar_monitoring_stopped",
                message="Radar monitoring loop stopped",
                details={"total_iterations": loop_iterations}
            )

    def _process_radar_data_enhanced(self, line: str):
        """Enhanced radar data processing with correlation tracking and performance monitoring"""
        
        try:
            # Create correlation context for this detection
            with CorrelationContext.create("vehicle_detection") as ctx:
                
                # Log all raw data for debugging
                self.logger.debug(f"Raw radar data: {repr(line)}")
                
                data = self._parse_radar_line_enhanced(line)
                if not data:
                    self.logger.debug(f"No parseable data from line: {repr(line)}")
                    return
                
                # Additional validation: ensure we have valid speed data
                if 'speed' not in data or data['speed'] is None:
                    self.logger.debug(f"No speed in parsed data: {data}")
                    return
                
                # Track processing performance
                processing_start = time.time()
                
                # Check for significant vehicle detection
                is_significant = False
                
                if 'speed' in data and data['speed'] is not None:
                    try:
                        speed = float(data['speed'])
                        magnitude = data.get('magnitude', 'unknown')
                        
                        # Filter significant detections (above noise threshold)
                        # Use absolute value to detect both approaching (-) and departing (+) vehicles
                        if abs(speed) >= 2.0:
                            is_significant = True
                            self.detection_count += 1
                            detection_id = str(uuid.uuid4())[:8]
                            
                            # Log vehicle detection with correlation
                            alert_level = self._determine_alert_level(speed)
                            
                            self.logger.log_business_event(
                                event_name="vehicle_detected",
                                event_data={
                                    "detection_id": detection_id,
                                    "speed_mph": speed,
                                    "speed_mps": data.get('speed_mps'),
                                    "magnitude": magnitude,
                                    "alert_level": alert_level,
                                    "raw_data": data.get('_raw'),
                                    "detection_number": self.detection_count,
                                    "message": f"🚗 Vehicle detected: {speed:.1f} mph"
                                }
                            )
                            
                            # Log speed alerts with appropriate severity
                            if alert_level == 'high':
                                self.logger.log_service_event(
                                    event_type="high_speed_detected",
                                    message=f"🚨 HIGH SPEED ALERT: {speed:.1f} mph exceeds {self.high_speed_threshold} mph limit",
                                    details={"detection_id": detection_id, "speed": speed, "warning_level": "high"}
                                )
                            elif alert_level == 'low':
                                self.logger.info(f"⚠️  Low speed alert: {speed:.1f} mph")
                            
                            data['alert_level'] = alert_level
                            data['detection_id'] = detection_id
                            
                            # Track detection timing for performance analysis
                            current_time = time.time()
                            if self.last_detection_time:
                                time_since_last = current_time - self.last_detection_time
                                self.logger.debug(f"Time since last detection: {time_since_last:.2f}s")
                            self.last_detection_time = current_time
                            
                            # Publish motion detection to standardized FIFO stream
                            try:
                                # Use detection_id as correlation_id to avoid context issues
                                correlation_id = detection_id
                                
                                self._publish_to_redis_enhanced(data, correlation_id)
                                self.logger.debug("✅ Redis stream publish successful")
                                
                                # Publish traffic event for consolidator notification
                                self._publish_traffic_event(detection_id, speed, alert_level, correlation_id)
                                self.logger.debug("✅ Traffic event publish successful")
                                
                            except Exception as redis_error:
                                # Don't let Redis errors break the detection loop
                                import traceback
                                self.logger.log_error(
                                    error_type="redis_publish_error",
                                    message=f"Failed to publish detection to Redis: {str(redis_error)}",
                                    exception=redis_error,
                                    details={
                                        "detection_id": detection_id, 
                                        "speed": speed,
                                        "traceback": traceback.format_exc(),
                                        "exception_type": type(redis_error).__name__
                                    }
                                )
                        
                        else:
                            # Log noise filtering - no Redis publishing for noise
                            self.logger.debug(f"Filtered noise: {speed:.1f} mph below threshold")
                            data['alert_level'] = 'noise'
                    
                    except (ValueError, TypeError) as e:
                        # Log with more detail to understand the data format issue
                        error_details = {
                            "raw_speed": data.get('speed'),
                            "raw_data": data.get('_raw'),
                            "data_keys": list(data.keys()),
                            "speed_value": repr(data.get('speed')),
                            "speed_type": type(data.get('speed')).__name__,
                            "exception_type": type(e).__name__,
                            "exception_msg": str(e)
                        }
                        
                        self.logger.error(f"❌ Speed conversion failed: {error_details}")
                        self.logger.log_error(
                            error_type="speed_conversion_error",
                            message="Failed to convert speed data",
                            exception=e,
                            details=error_details
                        )
                        data['alert_level'] = 'parse_error'
                
                # Track processing performance
                processing_time = time.time() - processing_start
                self.processing_times.append(processing_time)
                
                # Keep only last 1000 processing times for statistics
                if len(self.processing_times) > 1000:
                    self.processing_times = self.processing_times[-1000:]
                
                # Log performance metrics for significant detections
                if is_significant:
                    avg_processing = sum(self.processing_times) / len(self.processing_times)
                    self.logger.debug(
                        f"Detection processed in {processing_time*1000:.2f}ms (avg: {avg_processing*1000:.2f}ms)"
                    )
        
        except Exception as e:
            # Catch any unexpected exceptions in data processing to prevent loop crashes
            import traceback
            self.logger.log_error(
                error_type="radar_data_processing_exception",
                message=f"Unexpected error in radar data processing: {str(e)}",
                exception=e,
                details={
                    "raw_line": repr(line),
                    "traceback": traceback.format_exc(),
                    "exception_type": type(e).__name__
                }
            )

    def _parse_radar_line_enhanced(self, line: str) -> Optional[Dict]:
        """Enhanced radar data parsing with detailed error tracking"""
        
        if not line or not line.strip():
            return None
        
        line = line.strip()
        timestamp = time.time()
        
        try:
            # Debug: Log what we're trying to parse
            self.logger.debug(f"Parsing radar line: {repr(line)}")
            
            # Try CSV format first: "m",0.7 (magnitude, speed)
            import re
            csv_match = re.match(r'^"([^"]+)",([\\d\\.-]+)$', line)
            if csv_match:
                magnitude = csv_match.group(1)
                speed_raw = float(csv_match.group(2))
                speed = speed_raw  # Preserve sign for direction detection
                
                self.logger.debug(f"Parsed CSV format: magnitude={magnitude}, speed={speed} (raw: {speed_raw})")
                
                return {
                    'speed': speed,
                    'magnitude': magnitude,
                    'unit': 'mph',
                    '_raw': line,
                    '_timestamp': timestamp,
                    '_source': 'ops243_radar',
                    '_format': 'csv'
                }
            
            # Try JSON format
            if line.startswith('{') and line.endswith('}'):
                try:
                    data = json.loads(line)
                    self.logger.debug(f"Parsed JSON data: {data}")
                    
                    if 'speed' in data:
                        speed_raw = data['speed']
                        
                        # Handle different units - preserve sign for direction detection
                        if data.get('unit') == 'mps':
                            speed_mph = float(speed_raw) * 2.237  # Convert m/s to mph, preserve sign
                        else:
                            speed_mph = float(speed_raw)  # Assume mph, preserve sign
                        
                        return {
                            'speed': speed_mph,
                            'speed_mps': data.get('speed') if data.get('unit') == 'mps' else None,
                            'magnitude': data.get('magnitude', 'unknown'),
                            'unit': 'mph',
                            '_raw': line,
                            '_timestamp': timestamp,
                            '_source': 'ops243_radar',
                            '_format': 'json'
                        }
                    
                    # If no speed, log what we got
                    self.logger.debug(f"JSON data without speed field: {list(data.keys())}")
                    return None
                    
                except json.JSONDecodeError as e:
                    self.logger.debug(f"JSON parse error: {e}")
            
            # Try simple numeric formats
            # Format: "12.3" (just speed) - preserve sign for direction detection
            try:
                speed = float(line)  # Preserve sign for direction detection
                self.logger.debug(f"Parsed simple numeric: {speed}")
                return {
                    'speed': speed,
                    'unit': 'mph',
                    '_raw': line,
                    '_timestamp': timestamp,
                    '_source': 'ops243_radar',
                    '_format': 'numeric'
                }
            except ValueError:
                pass
            
            # Try space-separated format: "12.3 mph" - preserve sign for direction detection
            parts = line.split()
            if len(parts) >= 2:
                try:
                    speed = float(parts[0])  # Preserve sign for direction detection
                    unit = parts[1]
                    self.logger.debug(f"Parsed space-separated: {speed} {unit}")
                    return {
                        'speed': speed,
                        'unit': unit,
                        '_raw': line,
                        '_timestamp': timestamp,
                        '_source': 'ops243_radar',
                        '_format': 'simple'
                    }
                except ValueError:
                    pass
            
            # Try comma-separated without quotes: m,12.3
            if ',' in line:
                parts = line.split(',')
                if len(parts) == 2:
                    try:
                        magnitude = parts[0].strip()
                        speed = abs(float(parts[1].strip()))
                        self.logger.debug(f"Parsed comma-separated: {magnitude},{speed}")
                        return {
                            'speed': speed,
                            'magnitude': magnitude,
                            'unit': 'mph',
                            '_raw': line,
                            '_timestamp': timestamp,
                            '_source': 'ops243_radar',
                            '_format': 'comma_separated'
                        }
                    except ValueError:
                        pass
        
        except Exception as e:
            self.logger.log_error(
                error_type="radar_parse_exception",
                message=f"Exception parsing radar line: {line}",
                exception=e,
                details={"line_length": len(line), "line_repr": repr(line)}
            )
        
        # Log unrecognized format for debugging
        self.logger.debug(f"Unrecognized radar format: {repr(line)}")
        
        # Return None for unrecognized formats to avoid processing
        return None

    def _determine_alert_level(self, speed: float) -> str:
        """Determine alert level based on speed thresholds using absolute value"""
        abs_speed = abs(speed)
        if abs_speed >= self.high_speed_threshold:
            return 'high'
        elif abs_speed >= self.low_speed_threshold:
            return 'low'
        else:
            return 'normal'

    def _publish_to_redis_enhanced(self, data: Dict, correlation_id: str):
        """Standardized FIFO Redis publishing with correlation tracking"""
        
        try:
            # Convert all values to strings for Redis compatibility
            redis_data = {}
            for key, value in data.items():
                if value is not None:
                    redis_data[key] = str(value)
            
            # Add correlation ID to Redis data (already as string)
            redis_data['correlation_id'] = str(correlation_id)
            
            # Publish to standardized FIFO traffic radar stream
            self.redis_client.xadd('traffic:radar', redis_data)
            
            self.logger.debug(
                f"📡 Published radar data to FIFO stream: {data.get('speed', 0):.1f} mph",
                details={
                    "correlation_id": correlation_id,
                    "stream": "traffic:radar"
                }
            )
        
        except Exception as e:
            import traceback
            self.logger.log_error(
                error_type="redis_publish_failed",
                message=f"Failed to publish radar data to Redis: {str(e)}",
                exception=e,
                details={
                    "correlation_id": correlation_id,
                    "data_keys": list(data.keys()) if data else [],
                    "traceback": traceback.format_exc(),
                    "exception_type": type(e).__name__,
                    "redis_connected": self.redis_client is not None,
                    "data_sample": {k: str(v)[:100] for k, v in data.items() if k != '_raw'} if data else {}
                }
            )

    def _publish_traffic_event(self, detection_id: str, speed: float, alert_level: str, correlation_id: str):
        """Publish traffic event to notify consolidator service"""
        
        try:
            # Create event message for consolidator
            event_data = {
                "event_type": "vehicle_detection",
                "detection_id": detection_id,
                "speed_mph": speed,
                "alert_level": alert_level,
                "correlation_id": correlation_id,
                "timestamp": time.time(),
                "source": "radar_service"
            }
            
            # Publish to traffic_events channel for consolidator notification
            self.redis_client.publish('traffic_events', json.dumps(event_data))
            
            self.logger.debug(
                f"🔔 Published traffic event: {speed:.1f} mph detection",
                details={
                    "detection_id": detection_id,
                    "correlation_id": correlation_id,
                    "channel": "traffic_events"
                }
            )
            
        except Exception as e:
            import traceback
            self.logger.log_error(
                error_type="traffic_event_publish_failed",
                message=f"Failed to publish traffic event: {str(e)}",
                exception=e,
                details={
                    "detection_id": detection_id,
                    "speed": speed,
                    "correlation_id": correlation_id,
                    "traceback": traceback.format_exc(),
                    "exception_type": type(e).__name__
                }
            )

    def _log_periodic_stats(self, loop_iterations: int):
        """Log periodic service statistics"""
        
        uptime = time.time() - self.startup_time if self.startup_time else 0
        avg_processing_time = 0
        
        if self.processing_times:
            avg_processing_time = sum(self.processing_times) / len(self.processing_times)
        
        self.logger.log_service_event(
            event_type="periodic_stats",
            message="📊 Radar service statistics",
            details={
                "uptime_seconds": uptime,
                "uptime_formatted": f"{uptime/3600:.1f}h",
                "total_detections": self.detection_count,
                "loop_iterations_5min": loop_iterations,
                "avg_processing_time_ms": avg_processing_time * 1000,
                "detection_rate_per_hour": (self.detection_count / (uptime / 3600)) if uptime > 0 else 0
            }
        )

    def stop(self):
        """Enhanced service shutdown with correlation tracking"""
        
        with CorrelationContext.create("service_shutdown") as ctx:
            self.logger.log_service_event(
                event_type="service_shutdown_initiated",
                message="🛑 Initiating radar service shutdown"
            )
            
            self.running = False
            
            # Stop monitoring thread
            if self.thread:
                self.thread.join(timeout=5)
                self.logger.debug("Radar monitoring thread stopped")
            
            # Close UART connection
            if self.ser:
                try:
                    self.ser.close()
                    self.logger.debug("UART connection closed")
                except Exception as e:
                    self.logger.log_error(
                        error_type="uart_close_error",
                        message="Error closing UART connection",
                        exception=e
                    )
            
            # Log final statistics
            if self.startup_time:
                uptime = time.time() - self.startup_time
                avg_processing = sum(self.processing_times) / len(self.processing_times) if self.processing_times else 0
                
                self.logger.log_service_event(
                    event_type="service_shutdown_complete",
                    message="✅ Radar service shutdown complete",
                    details={
                        "total_uptime_seconds": uptime,
                        "total_detections": self.detection_count,
                        "avg_processing_time_ms": avg_processing * 1000,
                        "detection_rate": (self.detection_count / (uptime / 3600)) if uptime > 0 else 0
                    }
                )

def signal_handler(signum, frame):
    """Handle shutdown signals with proper logging"""
    print(f"Received signal {signum}, shutting down...")
    sys.exit(0)

def main():
    """Main service entry point with enhanced error handling"""
    
    # Set up signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Read configuration from environment variables
    uart_port = os.environ.get('RADAR_UART_PORT', '/dev/ttyAMA0')
    baudrate = int(os.environ.get('RADAR_BAUD_RATE', '19200'))
    redis_host = os.environ.get('REDIS_HOST', 'localhost')
    redis_port = int(os.environ.get('REDIS_PORT', '6379'))
    
    # Create enhanced radar service
    service = RadarServiceEnhanced(
        uart_port=uart_port,
        baudrate=baudrate,
        redis_host=redis_host,
        redis_port=redis_port
    )
    
    if service.start():
        print("Enhanced radar service running with centralized logging. Press Ctrl+C to stop.")
        try:
            # Keep main thread alive
            while service.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nReceived interrupt signal...")
        finally:
            service.stop()
    else:
        print("Failed to start enhanced radar service")
        sys.exit(1)

if __name__ == '__main__':
    main()
