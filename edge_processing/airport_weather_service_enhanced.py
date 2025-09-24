#!/usr/bin/env python3
"""
Enhanced Airport Weather Service - WITH CENTRALIZED LOGGING
Periodically fetches weather.gov API and updates Redis with latest observation
NOW WITH CENTRALIZED LOGGING AND CORRELATION TRACKING

This service:
- Fetches weather data from weather.gov API for KOKC station
- Stores observations in Redis for real-time access
- Provides external weather correlation for traffic analysis
- Centralized logging with API monitoring and error tracking
- Performance monitoring for API calls and data processing
- Correlation with local DHT22 sensor readings

Architecture:
Weather.gov API -> HTTP Request -> Enhanced Service -> Redis + Centralized Logging -> Docker Analytics
"""

import os
import time
import json
import requests
import redis
import sys
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pathlib import Path

# Add edge_processing to path for shared_logging
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
from shared_logging import ServiceLogger, CorrelationContext

# Initialize centralized logging
logger = ServiceLogger("airport_weather_service")

# Configuration with logging
FETCH_INTERVAL_MINUTES = int(os.getenv('FETCH_INTERVAL_MINUTES', 5))
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_KEY = os.getenv('AIRPORT_WEATHER_REDIS_KEY', 'weather:airport:latest')
WEATHER_API_URL = os.getenv('WEATHER_API_URL', 'https://api.weather.gov/stations/KOKC/observations/latest')
API_TIMEOUT = int(os.getenv('WEATHER_API_TIMEOUT', 10))

logger.info("Airport weather service initialized", extra={
    "business_event": "service_initialization",
    "fetch_interval_minutes": FETCH_INTERVAL_MINUTES,
    "redis_host": REDIS_HOST,
    "redis_port": REDIS_PORT,
    "redis_key": REDIS_KEY,
    "weather_api_url": WEATHER_API_URL,
    "api_timeout": API_TIMEOUT
})


class EnhancedAirportWeatherService:
    """Enhanced airport weather service with centralized logging and monitoring"""
    
    def __init__(self):
        self.redis_client = None
        self.stats = {
            "total_api_calls": 0,
            "successful_api_calls": 0,
            "failed_api_calls": 0,
            "total_storage_operations": 0,
            "successful_storage_operations": 0,
            "last_successful_fetch": None,
            "last_api_error": None,
            "avg_api_response_time_ms": 0.0
        }
        
        # Initialize Redis connection
        self._connect_redis()
        
        logger.info("Enhanced airport weather service initialized", extra={
            "business_event": "enhanced_service_initialization",
            "weather_station": "KOKC"
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
    
    @logger.monitor_performance("weather_api_fetch")
    def fetch_weather_api(self) -> Dict[str, Any]:
        """
        Fetch weather data from weather.gov API with enhanced logging and monitoring
        
        Returns:
            Dict containing weather data or error information
        """
        fetch_id = str(uuid.uuid4())[:8]
        
        with CorrelationContext.set_correlation_id(fetch_id):
            logger.debug("Starting weather API fetch", extra={
                "business_event": "api_fetch_start",
                "fetch_id": fetch_id,
                "api_url": WEATHER_API_URL
            })
            
            self.stats["total_api_calls"] += 1
            
            try:
                # Add User-Agent header as required by weather.gov
                headers = {
                    'User-Agent': 'TrafficMonitor/1.0 (https://github.com/gcu-merk/CST_590_Computer_Science_Capstone_Project)'
                }
                
                response = requests.get(
                    WEATHER_API_URL,
                    timeout=API_TIMEOUT,
                    headers=headers
                )
                response.raise_for_status()
                
                data = response.json()
                props = data.get('properties', {})
                
                # Parse weather data
                weather_data = {
                    'fetch_id': fetch_id,
                    'timestamp': props.get('timestamp'),
                    'textDescription': props.get('textDescription'),
                    'temperature': self._extract_value(props.get('temperature')),
                    'dewpoint': self._extract_value(props.get('dewpoint')),
                    'windDirection': self._extract_value(props.get('windDirection')),
                    'windSpeed': self._extract_value(props.get('windSpeed')),
                    'windGust': self._extract_value(props.get('windGust')),
                    'visibility': self._extract_value(props.get('visibility')),
                    'precipitationLast3Hours': self._extract_value(props.get('precipitationLast3Hours')),
                    'relativeHumidity': self._extract_value(props.get('relativeHumidity')),
                    'cloudLayers': props.get('cloudLayers', []),
                    'stationId': props.get('stationId'),
                    'stationName': props.get('stationName'),
                    'fetch_timestamp': datetime.now(timezone.utc).isoformat(),
                    'response_status_code': response.status_code,
                    'response_time_ms': response.elapsed.total_seconds() * 1000
                }
                
                self.stats["successful_api_calls"] += 1
                self.stats["last_successful_fetch"] = weather_data['fetch_timestamp']
                
                # Update average response time
                if self.stats["successful_api_calls"] > 0:
                    current_avg = self.stats.get("avg_api_response_time_ms", 0)
                    new_avg = ((current_avg * (self.stats["successful_api_calls"] - 1)) + weather_data['response_time_ms']) / self.stats["successful_api_calls"]
                    self.stats["avg_api_response_time_ms"] = round(new_avg, 2)
                
                logger.info("Weather API fetch successful", extra={
                    "business_event": "api_fetch_success",
                    "fetch_id": fetch_id,
                    "station_id": weather_data.get('stationId'),
                    "temperature": weather_data.get('temperature'),
                    "humidity": weather_data.get('relativeHumidity'),
                    "wind_speed": weather_data.get('windSpeed'),
                    "visibility": weather_data.get('visibility'),
                    "response_time_ms": weather_data['response_time_ms']
                })
                
                return weather_data
                
            except requests.exceptions.Timeout as e:
                self.stats["failed_api_calls"] += 1
                self.stats["last_api_error"] = f"Timeout: {str(e)}"
                
                error_data = {
                    'fetch_id': fetch_id,
                    'error': 'timeout',
                    'error_message': str(e),
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'api_url': WEATHER_API_URL
                }
                
                logger.error("Weather API fetch timeout", extra={
                    "business_event": "api_fetch_failure",
                    "fetch_id": fetch_id,
                    "error_type": "timeout",
                    "error": str(e),
                    "timeout_seconds": API_TIMEOUT
                })
                
                return error_data
                
            except requests.exceptions.HTTPError as e:
                self.stats["failed_api_calls"] += 1
                self.stats["last_api_error"] = f"HTTP Error: {str(e)}"
                
                error_data = {
                    'fetch_id': fetch_id,
                    'error': 'http_error',
                    'error_message': str(e),
                    'status_code': getattr(e.response, 'status_code', None),
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'api_url': WEATHER_API_URL
                }
                
                logger.error("Weather API HTTP error", extra={
                    "business_event": "api_fetch_failure",
                    "fetch_id": fetch_id,
                    "error_type": "http_error",
                    "error": str(e),
                    "status_code": error_data['status_code']
                })
                
                return error_data
                
            except Exception as e:
                self.stats["failed_api_calls"] += 1
                self.stats["last_api_error"] = f"Unexpected error: {str(e)}"
                
                error_data = {
                    'fetch_id': fetch_id,
                    'error': 'unexpected_error',
                    'error_message': str(e),
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'api_url': WEATHER_API_URL
                }
                
                logger.error("Weather API unexpected error", extra={
                    "business_event": "api_fetch_failure",
                    "fetch_id": fetch_id,
                    "error_type": "unexpected_error",
                    "error": str(e)
                })
                
                return error_data
    
    def _extract_value(self, weather_field: Optional[Dict]) -> Optional[float]:
        """Extract numerical value from weather.gov field format"""
        if weather_field and isinstance(weather_field, dict):
            value = weather_field.get('value')
            return value if value is not None else None
        return None
    
    def store_weather_data(self, weather_data: Dict[str, Any]) -> bool:
        """Store weather data in Redis with logging"""
        if not self.redis_client:
            logger.warning("Redis client not available - cannot store weather data", extra={
                "business_event": "storage_failure",
                "failure_type": "redis_unavailable"
            })
            return False
        
        self.stats["total_storage_operations"] += 1
        
        try:
            # Store latest weather data
            self.redis_client.set(REDIS_KEY, json.dumps(weather_data))
            
            # Store in time-series format for historical analysis
            ts_key = f"{REDIS_KEY}:timeseries"
            self.redis_client.zadd(ts_key, {json.dumps(weather_data): time.time()})
            
            # Keep only last 24 hours of time-series data
            cutoff_time = time.time() - (24 * 60 * 60)
            self.redis_client.zremrangebyscore(ts_key, 0, cutoff_time)
            
            # Store correlation data with DHT22 if available
            dht22_key = "weather:dht22"
            dht22_data = self.redis_client.hgetall(dht22_key)
            if dht22_data:
                correlation_data = {
                    "airport_temperature": weather_data.get('temperature'),
                    "dht22_temperature": float(dht22_data.get('temperature', 0)),
                    "airport_humidity": weather_data.get('relativeHumidity'),
                    "dht22_humidity": float(dht22_data.get('humidity', 0)),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "correlation_id": weather_data.get('fetch_id')
                }
                
                correlation_key = "weather:correlation:airport_dht22"
                self.redis_client.set(correlation_key, json.dumps(correlation_data))
                
                logger.debug("Weather correlation data stored", extra={
                    "business_event": "weather_correlation",
                    "airport_temp": correlation_data["airport_temperature"],
                    "dht22_temp": correlation_data["dht22_temperature"],
                    "temp_difference": abs(correlation_data["airport_temperature"] - correlation_data["dht22_temperature"]) if correlation_data["airport_temperature"] and correlation_data["dht22_temperature"] else None
                })
            
            self.stats["successful_storage_operations"] += 1
            
            logger.info("Weather data stored successfully", extra={
                "business_event": "weather_data_stored",
                "fetch_id": weather_data.get('fetch_id'),
                "redis_key": REDIS_KEY,
                "has_error": 'error' in weather_data
            })
            
            return True
            
        except Exception as e:
            logger.error("Failed to store weather data in Redis", extra={
                "business_event": "storage_failure",
                "error": str(e),
                "fetch_id": weather_data.get('fetch_id')
            })
            return False
    
    def publish_stats(self):
        """Publish service statistics"""
        try:
            if self.redis_client:
                stats_key = f"{REDIS_KEY}:stats"
                self.redis_client.hset(stats_key, mapping=self.stats)
                
                logger.debug("Airport weather service statistics published", extra={
                    "business_event": "stats_published",
                    "stats": self.stats
                })
                
        except Exception as e:
            logger.error("Failed to publish airport weather statistics", extra={
                "business_event": "stats_publication_failure",
                "error": str(e)
            })
    
    def run(self):
        """Main service loop with enhanced monitoring"""
        fetch_interval_seconds = FETCH_INTERVAL_MINUTES * 60
        
        logger.info("Starting airport weather service main loop", extra={
            "business_event": "service_start",
            "fetch_interval_minutes": FETCH_INTERVAL_MINUTES,
            "fetch_interval_seconds": fetch_interval_seconds
        })
        
        try:
            while True:
                # Generate fetch cycle correlation ID
                fetch_cycle_id = str(uuid.uuid4())[:8]
                
                with CorrelationContext.set_correlation_id(fetch_cycle_id):
                    logger.debug("Starting weather fetch cycle", extra={
                        "business_event": "fetch_cycle_start",
                        "cycle_id": fetch_cycle_id
                    })
                    
                    # Fetch weather data
                    weather_data = self.fetch_weather_api()
                    
                    # Store data (whether successful or error)
                    if self.store_weather_data(weather_data):
                        if 'error' not in weather_data:
                            logger.info("Weather fetch cycle completed successfully", extra={
                                "business_event": "fetch_cycle_success",
                                "cycle_id": fetch_cycle_id,
                                "temperature": weather_data.get('temperature'),
                                "station_id": weather_data.get('stationId')
                            })
                        else:
                            logger.warning("Weather fetch cycle completed with API error", extra={
                                "business_event": "fetch_cycle_api_error",
                                "cycle_id": fetch_cycle_id,
                                "error_type": weather_data.get('error')
                            })
                    else:
                        logger.warning("Weather fetch cycle failed - storage error", extra={
                            "business_event": "fetch_cycle_storage_failure",
                            "cycle_id": fetch_cycle_id
                        })
                    
                    # Publish statistics
                    self.publish_stats()
                
                # Wait for next fetch
                logger.debug(f"Waiting {fetch_interval_seconds} seconds for next fetch", extra={
                    "business_event": "waiting_next_cycle",
                    "wait_seconds": fetch_interval_seconds
                })
                time.sleep(fetch_interval_seconds)
                
        except KeyboardInterrupt:
            logger.info("Airport weather service interrupted by user", extra={
                "business_event": "service_interrupted",
                "final_stats": self.stats
            })
        except Exception as e:
            logger.error("Airport weather service main loop failed", extra={
                "business_event": "service_failure",
                "error": str(e),
                "final_stats": self.stats
            })


if __name__ == "__main__":
    try:
        service = EnhancedAirportWeatherService()
        service.run()
    except Exception as e:
        logger.error("Failed to start airport weather service", extra={
            "business_event": "startup_failure",
            "error": str(e)
        })
        sys.exit(1)