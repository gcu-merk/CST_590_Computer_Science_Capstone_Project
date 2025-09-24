#!/usr/bin/env python3
"""
Enhanced DHT22 Weather Service - WITH CENTRALIZED LOGGING
Reads DHT22 temperature and humidity sensor data using lgpio with Redis storage
NOW WITH CENTRALIZED LOGGING AND CORRELATION TRACKING

This service:
- Reads DHT22 sensor on GPIO pin with proper bit-bang protocol
- Stores readings in Redis for real-time access
- Provides environmental monitoring for traffic correlation
- Centralized logging with environmental event tracking
- Performance monitoring for sensor read operations
- Error tracking and sensor health monitoring

Architecture:
DHT22 GPIO Sensor -> lgpio -> Enhanced Service -> Redis + Centralized Logging -> Docker Analytics
"""

import time
import redis
import os
import json
import sys
from datetime import datetime, timezone
from typing import Tuple, Optional, Dict, Any
from pathlib import Path
import uuid

# Add edge_processing to path for shared_logging
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
from shared_logging import ServiceLogger, CorrelationContext

# Initialize centralized logging
logger = ServiceLogger("dht22_weather_service")

# Import lgpio for modern GPIO access - fail fast if not available
try:
    import lgpio
    logger.info("lgpio library loaded successfully", extra={
        "business_event": "library_initialization",
        "library": "lgpio"
    })
except ImportError as e:
    logger.error("lgpio library not available - DHT22 service requires GPIO access", extra={
        "business_event": "initialization_failure",
        "failure_type": "library_missing",
        "library": "lgpio",
        "error": str(e)
    })
    sys.exit(1)

# Initialize GPIO handle with proper error handling
gpio_handle = None
try:
    gpio_handle = lgpio.gpiochip_open(4)  # Pi 5 uses gpiochip4
    logger.info("GPIO chip opened successfully", extra={
        "business_event": "gpio_initialization",
        "gpio_chip": 4
    })
except Exception as e:
    logger.error("Failed to open GPIO chip - DHT22 service requires GPIO access", extra={
        "business_event": "initialization_failure",
        "failure_type": "gpio_access",
        "gpio_chip": 4,
        "error": str(e)
    })
    sys.exit(1)

# Configuration with logging
GPIO_PIN = int(os.getenv("DHT22_GPIO_PIN", 4))
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
UPDATE_INTERVAL = int(os.getenv("DHT22_UPDATE_INTERVAL", 600))  # Default: 10 minutes
REDIS_KEY = os.getenv("DHT22_REDIS_KEY", "weather:dht22")

logger.info("DHT22 weather service initialized", extra={
    "business_event": "service_initialization",
    "gpio_pin": GPIO_PIN,
    "redis_host": REDIS_HOST,
    "redis_port": REDIS_PORT,
    "update_interval": UPDATE_INTERVAL,
    "redis_key": REDIS_KEY
})


class EnhancedDHT22Service:
    """Enhanced DHT22 service with centralized logging and monitoring"""
    
    def __init__(self):
        self.gpio_handle = gpio_handle
        self.gpio_pin = GPIO_PIN
        self.redis_client = None
        self.stats = {
            "total_readings": 0,
            "successful_readings": 0,
            "failed_readings": 0,
            "last_reading_time": None,
            "avg_read_time_ms": 0.0
        }
        
        # Initialize Redis connection
        self._connect_redis()
        
        logger.info("Enhanced DHT22 service initialized", extra={
            "business_event": "enhanced_service_initialization",
            "gpio_pin": self.gpio_pin
        })
    
    def _connect_redis(self):
        """Initialize Redis connection with logging"""
        try:
            self.redis_client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info("Connected to Redis successfully", extra={
                "business_event": "redis_connection_established",
                "redis_host": REDIS_HOST,
                "redis_port": REDIS_PORT,
                "redis_db": REDIS_DB
            })
        except Exception as e:
            logger.error("Failed to connect to Redis", extra={
                "business_event": "redis_connection_failure",
                "redis_host": REDIS_HOST,
                "redis_port": REDIS_PORT,
                "error": str(e)
            })
            self.redis_client = None
    
    @logger.monitor_performance("dht22_sensor_read")
    def read_dht22_lgpio(self) -> Tuple[Optional[float], Optional[float]]:
        """
        Read DHT22 sensor using lgpio library with proper bit-bang protocol and retry logic
        Enhanced with centralized logging and performance monitoring
        
        Returns:
            Tuple of (temperature_celsius, humidity_percent) or (None, None) on error
        """
        reading_id = str(uuid.uuid4())[:8]
        
        with CorrelationContext.set_correlation_id(reading_id):
            logger.debug("Starting DHT22 sensor read", extra={
                "business_event": "sensor_read_start",
                "reading_id": reading_id,
                "gpio_pin": self.gpio_pin
            })
            
            self.stats["total_readings"] += 1
            
            try:
                # Send start signal - pull low for 18ms
                lgpio.gpio_claim_output(self.gpio_handle, self.gpio_pin, 1)
                lgpio.gpio_write(self.gpio_handle, self.gpio_pin, 0)
                time.sleep(0.018)  # 18ms
                lgpio.gpio_write(self.gpio_handle, self.gpio_pin, 1)
                time.sleep(0.000030)  # 30μs
                lgpio.gpio_claim_input(self.gpio_handle, self.gpio_pin)
                
                # Wait for DHT22 response (80μs low + 80μs high)
                timeout = time.time() + 0.001  # 1ms timeout
                while lgpio.gpio_read(self.gpio_handle, self.gpio_pin) == 1:
                    if time.time() > timeout:
                        raise TimeoutError("DHT22 response timeout (initial high)")
                
                # Read 40 bits of data
                data_bits = []
                for i in range(40):
                    # Wait for bit start (50μs low)
                    timeout = time.time() + 0.001
                    while lgpio.gpio_read(self.gpio_handle, self.gpio_pin) == 0:
                        if time.time() > timeout:
                            raise TimeoutError(f"DHT22 bit {i} timeout (low phase)")
                    
                    # Measure high duration to determine bit value
                    bit_start = time.time()
                    timeout = time.time() + 0.001
                    while lgpio.gpio_read(self.gpio_handle, self.gpio_pin) == 1:
                        if time.time() > timeout:
                            raise TimeoutError(f"DHT22 bit {i} timeout (high phase)")
                    
                    bit_duration = (time.time() - bit_start) * 1000000  # microseconds
                    data_bits.append(1 if bit_duration > 40 else 0)  # >40μs = 1, <40μs = 0
                
                # Convert bits to bytes
                data_bytes = []
                for i in range(5):
                    byte_val = 0
                    for j in range(8):
                        byte_val = (byte_val << 1) | data_bits[i * 8 + j]
                    data_bytes.append(byte_val)
                
                # Verify checksum
                checksum = (data_bytes[0] + data_bytes[1] + data_bytes[2] + data_bytes[3]) & 0xFF
                if checksum != data_bytes[4]:
                    raise ValueError(f"DHT22 checksum mismatch: expected {data_bytes[4]}, got {checksum}")
                
                # Parse temperature and humidity
                humidity = ((data_bytes[0] << 8) | data_bytes[1]) / 10.0
                temperature = (((data_bytes[2] & 0x7F) << 8) | data_bytes[3]) / 10.0
                if data_bytes[2] & 0x80:  # Negative temperature
                    temperature = -temperature
                
                # Validate ranges
                if not (0 <= humidity <= 100):
                    raise ValueError(f"Invalid humidity reading: {humidity}%")
                if not (-40 <= temperature <= 80):
                    raise ValueError(f"Invalid temperature reading: {temperature}°C")
                
                self.stats["successful_readings"] += 1
                self.stats["last_reading_time"] = datetime.now(timezone.utc).isoformat()
                
                logger.info("DHT22 sensor read successful", extra={
                    "business_event": "sensor_read_success",
                    "reading_id": reading_id,
                    "temperature_celsius": temperature,
                    "humidity_percent": humidity,
                    "checksum_valid": True
                })
                
                return temperature, humidity
                
            except Exception as e:
                self.stats["failed_readings"] += 1
                logger.error("DHT22 sensor read failed", extra={
                    "business_event": "sensor_read_failure",
                    "reading_id": reading_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                })
                return None, None
            finally:
                # Always free the GPIO pin
                try:
                    lgpio.gpio_free(self.gpio_handle, self.gpio_pin)
                except:
                    pass
    
    def store_reading(self, temperature: float, humidity: float) -> bool:
        """Store reading in Redis with logging"""
        if not self.redis_client:
            logger.warning("Redis client not available - cannot store reading", extra={
                "business_event": "storage_failure",
                "failure_type": "redis_unavailable"
            })
            return False
        
        try:
            reading_data = {
                "temperature": temperature,
                "humidity": humidity,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "sensor_type": "DHT22",
                "gpio_pin": self.gpio_pin
            }
            
            # Store as hash for easy field access
            self.redis_client.hset(REDIS_KEY, mapping=reading_data)
            
            # Also store in time-series format
            ts_key = f"{REDIS_KEY}:timeseries"
            self.redis_client.zadd(ts_key, {json.dumps(reading_data): time.time()})
            
            # Keep only last 24 hours of time-series data
            cutoff_time = time.time() - (24 * 60 * 60)
            self.redis_client.zremrangebyscore(ts_key, 0, cutoff_time)
            
            logger.info("DHT22 reading stored successfully", extra={
                "business_event": "reading_stored",
                "temperature_celsius": temperature,
                "humidity_percent": humidity,
                "redis_key": REDIS_KEY
            })
            
            return True
            
        except Exception as e:
            logger.error("Failed to store DHT22 reading in Redis", extra={
                "business_event": "storage_failure",
                "error": str(e),
                "temperature": temperature,
                "humidity": humidity
            })
            return False
    
    def publish_stats(self):
        """Publish service statistics"""
        try:
            if self.redis_client:
                stats_key = f"{REDIS_KEY}:stats"
                self.redis_client.hset(stats_key, mapping=self.stats)
                
                logger.debug("DHT22 service statistics published", extra={
                    "business_event": "stats_published",
                    "stats": self.stats
                })
                
        except Exception as e:
            logger.error("Failed to publish DHT22 statistics", extra={
                "business_event": "stats_publication_failure",
                "error": str(e)
            })
    
    def run(self):
        """Main service loop with enhanced monitoring"""
        logger.info("Starting DHT22 weather service main loop", extra={
            "business_event": "service_start",
            "update_interval": UPDATE_INTERVAL
        })
        
        try:
            while True:
                # Generate reading correlation ID
                reading_cycle_id = str(uuid.uuid4())[:8]
                
                with CorrelationContext.set_correlation_id(reading_cycle_id):
                    logger.debug("Starting DHT22 reading cycle", extra={
                        "business_event": "reading_cycle_start",
                        "cycle_id": reading_cycle_id
                    })
                    
                    # Read sensor
                    temperature, humidity = self.read_dht22_lgpio()
                    
                    if temperature is not None and humidity is not None:
                        # Store reading
                        if self.store_reading(temperature, humidity):
                            logger.info("DHT22 reading cycle completed", extra={
                                "business_event": "reading_cycle_success",
                                "cycle_id": reading_cycle_id,
                                "temperature_celsius": temperature,
                                "humidity_percent": humidity
                            })
                        else:
                            logger.warning("DHT22 reading successful but storage failed", extra={
                                "business_event": "reading_cycle_partial_failure",
                                "cycle_id": reading_cycle_id
                            })
                    else:
                        logger.warning("DHT22 reading cycle failed", extra={
                            "business_event": "reading_cycle_failure",
                            "cycle_id": reading_cycle_id
                        })
                    
                    # Publish statistics
                    self.publish_stats()
                
                # Wait for next reading
                logger.debug(f"Waiting {UPDATE_INTERVAL} seconds for next reading", extra={
                    "business_event": "waiting_next_cycle",
                    "wait_seconds": UPDATE_INTERVAL
                })
                time.sleep(UPDATE_INTERVAL)
                
        except KeyboardInterrupt:
            logger.info("DHT22 service interrupted by user", extra={
                "business_event": "service_interrupted",
                "final_stats": self.stats
            })
        except Exception as e:
            logger.error("DHT22 service main loop failed", extra={
                "business_event": "service_failure",
                "error": str(e),
                "final_stats": self.stats
            })
        finally:
            self._cleanup()
    
    def _cleanup(self):
        """Cleanup resources"""
        try:
            if self.gpio_handle is not None:
                lgpio.gpiochip_close(self.gpio_handle)
                logger.info("GPIO resources cleaned up", extra={
                    "business_event": "cleanup_complete"
                })
        except Exception as e:
            logger.error("Error during cleanup", extra={
                "business_event": "cleanup_failure",
                "error": str(e)
            })


if __name__ == "__main__":
    try:
        service = EnhancedDHT22Service()
        service.run()
    except Exception as e:
        logger.error("Failed to start DHT22 service", extra={
            "business_event": "startup_failure",
            "error": str(e)
        })
        sys.exit(1)