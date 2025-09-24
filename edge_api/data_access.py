#!/usr/bin/env python3
"""
Data Access Layer for Edge API
Provides Redis and PostgreSQL connections with connection pooling and caching
"""

import logging
import json
import time
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from functools import wraps
import redis
from redis.connection import ConnectionPool
import threading
from contextlib import contextmanager

from .config import config
from .error_handling import (
    safe_redis_operation, DataSourceError, NotFoundError
)

logger = logging.getLogger(__name__)


class RedisDataAccess:
    """Redis data access with connection pooling and caching"""
    
    def __init__(self, host: str = None, port: int = None, db: int = None, password: str = None):
        """Initialize Redis connection pool"""
        self.host = host or config.database.redis_host
        self.port = port or config.database.redis_port
        self.db = db or config.database.redis_db
        self.password = password or config.database.redis_password
        
        # Create connection pool
        self.pool = ConnectionPool(
            host=self.host,
            port=self.port,
            db=self.db,
            password=self.password,
            decode_responses=True,
            max_connections=20,
            retry_on_timeout=True,
            socket_keepalive=True,
            socket_keepalive_options={},
        )
        
        # Connection instance
        self._redis = redis.Redis(connection_pool=self.pool)
        
        # Local cache for frequently accessed data
        self._cache = {}
        self._cache_ttl = {}
        self._cache_lock = threading.RLock()
        
        logger.info(f"Redis connection pool initialized: {self.host}:{self.port}/{self.db}")
    
    @contextmanager
    def get_connection(self):
        """Get Redis connection from pool with context management"""
        connection = None
        try:
            connection = redis.Redis(connection_pool=self.pool)
            yield connection
        except Exception as e:
            logger.error(f"Redis connection error: {e}")
            raise DataSourceError("Redis connection failed", source="Redis")
        finally:
            if connection:
                # Connection automatically returned to pool
                pass
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get value from local cache if not expired"""
        with self._cache_lock:
            if key in self._cache:
                if key in self._cache_ttl and time.time() < self._cache_ttl[key]:
                    return self._cache[key]
                else:
                    # Expired, remove from cache
                    self._cache.pop(key, None)
                    self._cache_ttl.pop(key, None)
        return None
    
    def _set_cache(self, key: str, value: Any, ttl_seconds: int = 300):
        """Set value in local cache with TTL"""
        with self._cache_lock:
            self._cache[key] = value
            self._cache_ttl[key] = time.time() + ttl_seconds
    
    @safe_redis_operation("Redis ping")
    def ping(self) -> bool:
        """Test Redis connection"""
        try:
            return self._redis.ping()
        except Exception:
            return False
    
    @safe_redis_operation("Get radar stream data")
    def get_radar_stream_data(self, start_time: datetime, end_time: datetime, 
                             count: int = 1000) -> List[Dict[str, Any]]:
        """Get radar data from stream within time range"""
        
        # Convert to millisecond timestamps for Redis streams
        start_ts = int(start_time.timestamp() * 1000)
        end_ts = int(end_time.timestamp() * 1000)
        
        # Check cache first
        cache_key = f"radar_stream:{start_ts}:{end_ts}:{count}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            logger.debug(f"Retrieved radar data from cache: {len(cached_data)} entries")
            return cached_data
        
        try:
            # Read from Redis stream
            stream_data = self._redis.xrange(
                config.radar.stream_name, 
                min=start_ts, 
                max=end_ts, 
                count=count
            )
            
            # Convert to structured format
            radar_entries = []
            for entry_id, fields in stream_data:
                try:
                    timestamp_ms = int(entry_id.split('-')[0])
                    entry_time = datetime.fromtimestamp(timestamp_ms / 1000)
                    
                    # Radar service now only stores actual speed data (no range data)
                    speed_value = float(fields.get('speed', 0))
                    
                    radar_entries.append({
                        'id': entry_id,
                        'timestamp': entry_time,
                        'timestamp_ms': timestamp_ms,
                        'speed': speed_value,
                        'unit': fields.get('unit', 'mph'),
                        'magnitude': fields.get('magnitude', 'unknown'),
                        'source': fields.get('_source', 'unknown')
                    })
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid radar entry {entry_id}: {e}")
                    continue
            
            # Cache the results (5 minute TTL for recent data)
            cache_ttl = 60 if (datetime.now() - end_time).total_seconds() < 3600 else 300
            self._set_cache(cache_key, radar_entries, cache_ttl)
            
            logger.debug(f"Retrieved {len(radar_entries)} radar entries from stream")
            return radar_entries
            
        except redis.ResponseError as e:
            if "no such key" in str(e).lower():
                logger.warning(f"Radar stream '{config.radar.stream_name}' not found")
                return []
            raise DataSourceError(f"Redis stream error: {e}", source="Redis")
    
    @safe_redis_operation("Get radar statistics")
    def get_radar_stats(self) -> Dict[str, Any]:
        """Get radar statistics from hash"""
        cache_key = "radar_stats"
        cached_stats = self._get_from_cache(cache_key)
        if cached_stats is not None:
            return cached_stats
        
        try:
            stats = self._redis.hgetall('radar_stats')
            
            # Convert numeric values
            processed_stats = {}
            for key, value in stats.items():
                try:
                    # Try to convert to appropriate type
                    if key in ['detection_count', 'total_pings']:
                        processed_stats[key] = int(value)
                    elif key in ['last_detection', 'average_range']:
                        processed_stats[key] = float(value)
                    else:
                        processed_stats[key] = value
                except (ValueError, TypeError):
                    processed_stats[key] = value
            
            # Cache for 1 minute
            self._set_cache(cache_key, processed_stats, 60)
            return processed_stats
            
        except Exception as e:
            logger.warning(f"Failed to get radar stats: {e}")
            return {}
    
    @safe_redis_operation("Get stream length")
    def get_stream_length(self, stream_name: str = None) -> int:
        """Get the length of a Redis stream"""
        stream_name = stream_name or config.radar.stream_name
        
        try:
            return self._redis.xlen(stream_name)
        except redis.ResponseError:
            return 0
    
    
    def group_radar_detections(self, radar_data: List[Dict[str, Any]], 
                             window_seconds: int = None) -> List[Dict[str, Any]]:
        """Group radar pings into vehicle detection windows"""
        window_seconds = window_seconds or config.radar.detection_window_seconds
        min_pings = config.radar.min_pings_per_vehicle
        
        if not radar_data:
            return []
        
        # Group by time windows
        windows = {}
        
        for entry in radar_data:
            # Create window key (group by N-second intervals)
            window_start = (entry['timestamp_ms'] // (window_seconds * 1000)) * (window_seconds * 1000)
            
            if window_start not in windows:
                windows[window_start] = {
                    'start_time': datetime.fromtimestamp(window_start / 1000),
                    'entries': [],
                    'ping_count': 0,
                    'avg_range': 0,
                    'range_variance': 0
                }
            
            windows[window_start]['entries'].append(entry)
            windows[window_start]['ping_count'] += 1
        
        # Convert windows to detections
        detections = []
        
        for window_start, window_data in windows.items():
            # Only consider windows with sufficient radar activity
            if window_data['ping_count'] >= min_pings:
                
                # Calculate statistics
                ranges = [entry['range'] for entry in window_data['entries']]
                avg_range = sum(ranges) / len(ranges)
                range_variance = sum((r - avg_range) ** 2 for r in ranges) / len(ranges)
                
                # Confidence based on ping count and range consistency
                confidence = min(0.95, 0.5 + (window_data['ping_count'] / 20))
                confidence *= max(0.5, 1.0 - (range_variance / 10))  # Reduce confidence for erratic ranges
                
                detections.append({
                    'id': f"radar_detection_{window_start}",
                    'timestamp': window_data['start_time'],
                    'confidence': round(confidence, 3),
                    'ping_count': window_data['ping_count'],
                    'average_range': round(avg_range, 2),
                    'range_variance': round(range_variance, 3),
                    'source': 'radar_grouping',
                    'window_seconds': window_seconds
                })
        
        return sorted(detections, key=lambda x: x['timestamp'])


# Global Redis instance
redis_client = RedisDataAccess()


def get_redis_client() -> RedisDataAccess:
    """Get the global Redis client instance"""
    return redis_client