#!/usr/bin/env python3
"""
API Services Layer
Business logic for API endpoints with caching and performance monitoring
"""

import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from functools import wraps
from collections import defaultdict

from .config import config
from .data_access import get_redis_client
from .error_handling import (
    ValidationError, DataSourceError, NotFoundError,
    validate_time_period, validate_pagination, validate_speed_range
)

logger = logging.getLogger(__name__)


def monitor_performance(operation_name: str):
    """Decorator to monitor API operation performance"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(f"Operation '{operation_name}' completed in {duration:.3f}s")
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"Operation '{operation_name}' failed after {duration:.3f}s: {e}")
                raise
        return wrapper
    return decorator


class TrafficDetectionService:
    """Service for vehicle detection operations"""
    
    def __init__(self):
        self.redis_client = get_redis_client()
        logger.info("TrafficDetectionService initialized")
    
    @monitor_performance("get_vehicle_detections")
    def get_detections(self, period_seconds: int, limit: int = 1000) -> Dict[str, Any]:
        """Get vehicle detections from radar data
        
        Args:
            period_seconds: Time period in seconds to look back
            limit: Maximum number of detections to return
            
        Returns:
            Dict containing detections list and metadata
        """
        # Validate inputs
        period_seconds = validate_time_period(period_seconds)
        
        # Calculate time range
        end_time = datetime.now()
        start_time = end_time - timedelta(seconds=period_seconds)
        
        # Get radar data
        radar_data = self.redis_client.get_radar_stream_data(
            start_time=start_time,
            end_time=end_time,
            count=min(limit * 10, 5000)  # Get more data for grouping
        )
        
        if not radar_data:
            logger.info("No radar data found for detection analysis")
            return {
                'detections': [],
                'count': 0,
                'time_range': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat(),
                    'period_seconds': period_seconds
                },
                'metadata': {
                    'data_source': 'radar_stream',
                    'processing_method': 'ping_grouping'
                }
            }
        
        # Group radar pings into vehicle detections
        detections = self.redis_client.group_radar_detections(radar_data)
        
        # Limit results
        if len(detections) > limit:
            detections = detections[-limit:]  # Get most recent
        
        # Format detections for API response
        formatted_detections = []
        for detection in detections:
            formatted_detections.append({
                'id': detection['id'],
                'timestamp': detection['timestamp'].isoformat(),
                'confidence': detection['confidence'],
                'vehicle_type': 'vehicle',  # Radar detects vehicles generically
                'source': detection['source'],
                'metadata': {
                    'ping_count': detection['ping_count'],
                    'average_range_meters': detection['average_range'],
                    'range_variance': detection['range_variance'],
                    'detection_window_seconds': detection['window_seconds']
                }
            })
        
        return {
            'detections': formatted_detections,
            'count': len(formatted_detections),
            'time_range': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat(),
                'period_seconds': period_seconds
            },
            'metadata': {
                'data_source': 'radar_stream',
                'total_radar_entries': len(radar_data),
                'processing_method': 'ping_grouping',
                'detection_algorithm': f'min_{config.radar.min_pings_per_vehicle}_pings_in_{config.radar.detection_window_seconds}s'
            }
        }


class SpeedAnalysisService:
    """Service for vehicle speed analysis"""
    
    def __init__(self):
        self.redis_client = get_redis_client()
        logger.info("SpeedAnalysisService initialized")
    
    @monitor_performance("get_speed_analysis")
    def get_speeds(self, period_seconds: int, min_speed: float = None, 
                   max_speed: float = None, limit: int = 1000) -> Dict[str, Any]:
        """Get vehicle speed measurements
        
        Args:
            period_seconds: Time period in seconds to look back
            min_speed: Minimum speed filter (mph)
            max_speed: Maximum speed filter (mph) 
            limit: Maximum number of speed measurements to return
            
        Returns:
            Dict containing speed measurements and statistics
        """
        # Validate inputs
        period_seconds = validate_time_period(period_seconds)
        min_speed, max_speed = validate_speed_range(min_speed, max_speed)
        
        # Calculate time range
        end_time = datetime.now()
        start_time = end_time - timedelta(seconds=period_seconds)
        
        # Get radar data for speed calculation
        radar_data = self.redis_client.get_radar_stream_data(
            start_time=start_time,
            end_time=end_time,
            count=min(limit * 5, 3000)  # More data needed for speed calculation
        )
        
        if len(radar_data) < 2:
            logger.info("Insufficient radar data for speed calculation")
            return {
                'speeds': [],
                'count': 0,
                'statistics': self._empty_speed_stats(),
                'time_range': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat(),
                    'period_seconds': period_seconds
                }
            }
        
        # Calculate speeds from range measurements
        speed_measurements = self.redis_client.calculate_speeds_from_ranges(radar_data)
        
        # Apply speed filters
        if min_speed is not None:
            speed_measurements = [s for s in speed_measurements if s['speed_mph'] >= min_speed]
        if max_speed is not None:
            speed_measurements = [s for s in speed_measurements if s['speed_mph'] <= max_speed]
        
        # Limit results
        if len(speed_measurements) > limit:
            speed_measurements = speed_measurements[-limit:]  # Get most recent
        
        # Calculate statistics
        statistics = self._calculate_speed_statistics(speed_measurements)
        
        # Format for API response
        formatted_speeds = []
        for speed in speed_measurements:
            formatted_speeds.append({
                'timestamp': speed['timestamp'].isoformat(),
                'speed_mph': speed['speed_mph'],
                'speed_ms': speed['speed_ms'],
                'source': speed['source'],
                'metadata': {
                    'calculation_method': 'range_difference',
                    'time_difference_seconds': speed['time_diff'],
                    'range_change_meters': abs(speed['range_current'] - speed['range_previous'])
                }
            })
        
        return {
            'speeds': formatted_speeds,
            'count': len(formatted_speeds),
            'statistics': statistics,
            'time_range': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat(),
                'period_seconds': period_seconds
            },
            'filters': {
                'min_speed_mph': min_speed,
                'max_speed_mph': max_speed
            },
            'metadata': {
                'total_radar_entries': len(radar_data),
                'calculation_method': 'consecutive_range_differences',
                'speed_limit_mph': config.radar.speed_limit_mph
            }
        }
    
    def _calculate_speed_statistics(self, speed_measurements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate speed statistics from measurements"""
        if not speed_measurements:
            return self._empty_speed_stats()
        
        speeds = [s['speed_mph'] for s in speed_measurements]
        
        # Basic statistics
        count = len(speeds)
        average_speed = sum(speeds) / count
        min_speed = min(speeds)
        max_speed = max(speeds)
        
        # Speed limit violations
        violations = sum(1 for s in speeds if s > config.radar.speed_limit_mph)
        violation_rate = violations / count if count > 0 else 0
        
        # Speed distribution
        speed_distribution = defaultdict(int)
        for speed in speeds:
            bucket = f"{int(speed // 10) * 10}-{int(speed // 10) * 10 + 10}"
            speed_distribution[bucket] += 1
        
        # Percentiles (simple approximation)
        sorted_speeds = sorted(speeds)
        percentiles = {}
        for p in [25, 50, 75, 85, 95]:
            idx = int((p / 100) * (len(sorted_speeds) - 1))
            percentiles[f"p{p}"] = sorted_speeds[idx]
        
        return {
            'count': count,
            'average_mph': round(average_speed, 2),
            'min_mph': round(min_speed, 2),
            'max_mph': round(max_speed, 2),
            'violations': violations,
            'violation_rate': round(violation_rate, 3),
            'speed_limit_mph': config.radar.speed_limit_mph,
            'distribution': dict(speed_distribution),
            'percentiles': percentiles
        }
    
    def _empty_speed_stats(self) -> Dict[str, Any]:
        """Return empty speed statistics structure"""
        return {
            'count': 0,
            'average_mph': 0.0,
            'min_mph': 0.0,
            'max_mph': 0.0,
            'violations': 0,
            'violation_rate': 0.0,
            'speed_limit_mph': config.radar.speed_limit_mph,
            'distribution': {},
            'percentiles': {}
        }


class TrafficAnalyticsService:
    """Service for comprehensive traffic analytics"""
    
    def __init__(self):
        self.redis_client = get_redis_client()
        self.detection_service = TrafficDetectionService()
        self.speed_service = SpeedAnalysisService()
        logger.info("TrafficAnalyticsService initialized")
    
    @monitor_performance("get_traffic_analytics")
    def get_analytics(self, period: str = 'hour') -> Dict[str, Any]:
        """Get comprehensive traffic analytics
        
        Args:
            period: Analysis period ('hour', 'day', 'week')
            
        Returns:
            Dict containing comprehensive traffic analytics
        """
        # Convert period to seconds
        period_seconds = validate_time_period(period)
        
        # Get detections and speeds
        detections_data = self.detection_service.get_detections(period_seconds, limit=2000)
        speeds_data = self.speed_service.get_speeds(period_seconds, limit=2000)
        
        # Calculate hourly distribution
        hourly_counts = self._calculate_hourly_distribution(
            detections_data.get('detections', []), 
            period_seconds
        )
        
        # Get radar system health
        radar_stats = self.redis_client.get_radar_stats()
        stream_length = self.redis_client.get_stream_length()
        
        return {
            'period': period,
            'total_vehicles': detections_data['count'],
            'speed_measurements': speeds_data['count'],
            'speed_statistics': speeds_data.get('statistics', {}),
            'hourly_distribution': hourly_counts,
            'time_range': detections_data['time_range'],
            'system_health': {
                'radar_stream_entries': stream_length,
                'radar_stats': radar_stats,
                'data_availability': 'good' if stream_length > 0 else 'limited'
            },
            'metadata': {
                'generated_at': datetime.utcnow().isoformat() + 'Z',
                'radar_config': {
                    'detection_window_seconds': config.radar.detection_window_seconds,
                    'min_pings_per_vehicle': config.radar.min_pings_per_vehicle,
                    'speed_range_mph': f"{config.radar.min_speed_mph}-{config.radar.max_speed_mph}",
                    'speed_limit_mph': config.radar.speed_limit_mph
                }
            }
        }
    
    def _calculate_hourly_distribution(self, detections: List[Dict[str, Any]], 
                                     period_seconds: int) -> List[Dict[str, Any]]:
        """Calculate hourly distribution of vehicle detections"""
        hourly_counts = defaultdict(int)
        
        for detection in detections:
            try:
                # Parse timestamp and get hour
                timestamp = datetime.fromisoformat(detection['timestamp'].replace('Z', '+00:00'))
                hour = timestamp.hour
                hourly_counts[hour] += 1
            except (ValueError, KeyError):
                continue
        
        # Create complete 24-hour structure
        hourly_list = []
        for hour in range(24):
            hourly_list.append({
                'hour': hour,
                'count': hourly_counts.get(hour, 0),
                'hour_label': f"{hour:02d}:00"
            })
        
        return hourly_list


# Global service instances
detection_service = TrafficDetectionService()
speed_service = SpeedAnalysisService()
analytics_service = TrafficAnalyticsService()


def get_detection_service() -> TrafficDetectionService:
    """Get the global detection service instance"""
    return detection_service


def get_speed_service() -> SpeedAnalysisService:
    """Get the global speed service instance"""
    return speed_service


def get_analytics_service() -> TrafficAnalyticsService:
    """Get the global analytics service instance"""
    return analytics_service