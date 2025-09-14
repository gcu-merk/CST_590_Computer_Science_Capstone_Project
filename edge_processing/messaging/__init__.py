"""
Messaging module for Traffic Monitoring System
Provides Redis-based real-time messaging between services
"""

from .redis_broker import (
    RedisMessageBroker,
    publish_camera_capture,
    publish_vehicle_detection,
    publish_system_health,
    publish_alert,
    get_broker,
    initialize_broker,
    close_broker
)

__all__ = [
    'RedisMessageBroker',
    'publish_camera_capture',
    'publish_vehicle_detection', 
    'publish_system_health',
    'publish_alert',
    'get_broker',
    'initialize_broker',
    'close_broker'
]