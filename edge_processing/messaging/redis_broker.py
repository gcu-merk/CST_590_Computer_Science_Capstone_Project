#!/usr/bin/env python3
"""
Redis Message Broker for Traffic Monitoring System
Provides real-time pub/sub messaging between services
Replaces file watching with instant event notifications
"""

import redis
import json
import logging
import time
import threading
from typing import Dict, Any, Callable, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class RedisMessageBroker:
    """
    Redis-based message broker for real-time inter-service communication
    Handles pub/sub messaging with error recovery and health monitoring
    """
    
    # Message channels
    CHANNELS = {
        'camera_capture': 'traffic:camera:capture',      # New image captured
        'image_processed': 'traffic:image:processed',    # Image processing completed
        'vehicle_detected': 'traffic:vehicle:detected',  # Vehicle detection event
        'system_health': 'traffic:system:health',        # System health updates
        'maintenance': 'traffic:maintenance:event',      # Maintenance events
        'alerts': 'traffic:alerts:critical'             # Critical system alerts
    }
    
    def __init__(self, 
                 host: str = 'redis', 
                 port: int = 6379, 
                 db: int = 0,
                 retry_interval: int = 5,
                 max_retries: int = 10):
        """
        Initialize Redis message broker
        
        Args:
            host: Redis server hostname
            port: Redis server port
            db: Redis database number
            retry_interval: Retry interval in seconds
            max_retries: Maximum retry attempts
        """
        self.host = host
        self.port = port
        self.db = db
        self.retry_interval = retry_interval
        self.max_retries = max_retries
        
        self.redis_client = None
        self.pubsub = None
        self.subscribers = {}
        self.is_connected = False
        self.subscriber_thread = None
        self.running = False
        
        self._connect()
    
    def _connect(self) -> bool:
        """Establish Redis connection with retry logic"""
        for attempt in range(self.max_retries):
            try:
                self.redis_client = redis.Redis(
                    host=self.host,
                    port=self.port,
                    db=self.db,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30
                )
                
                # Test connection
                self.redis_client.ping()
                self.is_connected = True
                logger.info(f"Connected to Redis at {self.host}:{self.port}")
                return True
                
            except redis.ConnectionError as e:
                logger.warning(f"Redis connection attempt {attempt + 1}/{self.max_retries} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_interval)
                else:
                    logger.error("Failed to connect to Redis after maximum retries")
                    self.is_connected = False
                    return False
        
        return False
    
    def publish_message(self, channel_key: str, message: Dict[str, Any]) -> bool:
        """
        Publish a message to a Redis channel
        
        Args:
            channel_key: Channel key from CHANNELS dict
            message: Message data to publish
            
        Returns:
            True if published successfully, False otherwise
        """
        if not self.is_connected or not self.redis_client:
            logger.warning(f"Cannot publish to {channel_key}: Redis not connected")
            return False
        
        try:
            channel = self.CHANNELS.get(channel_key)
            if not channel:
                logger.error(f"Invalid channel key: {channel_key}")
                return False
            
            # Add timestamp and source info
            enriched_message = {
                **message,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'source': 'traffic_monitor',
                'channel': channel_key
            }
            
            # Publish JSON message
            result = self.redis_client.publish(channel, json.dumps(enriched_message))
            logger.debug(f"Published to {channel}: {result} subscribers received message")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish message to {channel_key}: {e}")
            return False
    
    def subscribe_to_channel(self, channel_key: str, callback: Callable[[Dict[str, Any]], None]):
        """
        Subscribe to a Redis channel with callback
        
        Args:
            channel_key: Channel key from CHANNELS dict
            callback: Function to call when message received
        """
        channel = self.CHANNELS.get(channel_key)
        if not channel:
            logger.error(f"Invalid channel key: {channel_key}")
            return
        
        self.subscribers[channel] = callback
        logger.info(f"Subscribed to channel: {channel}")
        
        # Start subscriber thread if not running
        if not self.running:
            self.start_subscriber()
    
    def start_subscriber(self):
        """Start the subscriber thread"""
        if self.running:
            return
        
        if not self.is_connected:
            logger.warning("Cannot start subscriber: Redis not connected")
            return
        
        try:
            self.pubsub = self.redis_client.pubsub()
            for channel in self.subscribers.keys():
                self.pubsub.subscribe(channel)
            
            self.running = True
            self.subscriber_thread = threading.Thread(target=self._subscriber_loop, daemon=True)
            self.subscriber_thread.start()
            logger.info("Started Redis subscriber thread")
            
        except Exception as e:
            logger.error(f"Failed to start subscriber: {e}")
    
    def _subscriber_loop(self):
        """Main subscriber loop - runs in background thread"""
        while self.running:
            try:
                if not self.pubsub:
                    break
                
                message = self.pubsub.get_message(timeout=1.0)
                if message and message['type'] == 'message':
                    try:
                        # Parse JSON message
                        data = json.loads(message['data'])
                        channel = message['channel']
                        
                        # Call registered callback
                        if channel in self.subscribers:
                            self.subscribers[channel](data)
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON in message from {message['channel']}: {e}")
                    except Exception as e:
                        logger.error(f"Error processing message from {message['channel']}: {e}")
                
            except Exception as e:
                logger.error(f"Subscriber loop error: {e}")
                time.sleep(1)
    
    def stop_subscriber(self):
        """Stop the subscriber thread"""
        self.running = False
        if self.pubsub:
            self.pubsub.close()
        if self.subscriber_thread and self.subscriber_thread.is_alive():
            self.subscriber_thread.join(timeout=5)
        logger.info("Stopped Redis subscriber")
    
    def health_check(self) -> Dict[str, Any]:
        """Check Redis connection health"""
        try:
            if not self.redis_client:
                return {'status': 'disconnected', 'error': 'No Redis client'}
            
            # Test connection
            start_time = time.time()
            self.redis_client.ping()
            latency = (time.time() - start_time) * 1000
            
            # Get Redis info
            info = self.redis_client.info()
            
            return {
                'status': 'connected',
                'latency_ms': round(latency, 2),
                'connected_clients': info.get('connected_clients', 0),
                'used_memory_human': info.get('used_memory_human', 'unknown'),
                'uptime_in_seconds': info.get('uptime_in_seconds', 0),
                'subscriber_count': len(self.subscribers),
                'subscriber_running': self.running
            }
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def close(self):
        """Clean shutdown of Redis connections"""
        logger.info("Closing Redis message broker...")
        self.stop_subscriber()
        if self.redis_client:
            self.redis_client.close()
        self.is_connected = False


# Convenience functions for common message types
def publish_camera_capture(broker: RedisMessageBroker, image_path: str, metadata: Dict[str, Any] = None):
    """Publish camera capture event"""
    message = {
        'event_type': 'image_captured',
        'image_path': image_path,
        'metadata': metadata or {}
    }
    return broker.publish_message('camera_capture', message)

def publish_vehicle_detection(broker: RedisMessageBroker, vehicle_data: Dict[str, Any]):
    """Publish vehicle detection event"""
    message = {
        'event_type': 'vehicle_detected',
        'vehicle_data': vehicle_data
    }
    return broker.publish_message('vehicle_detected', message)

def publish_system_health(broker: RedisMessageBroker, health_data: Dict[str, Any]):
    """Publish system health update"""
    message = {
        'event_type': 'health_update',
        'health_data': health_data
    }
    return broker.publish_message('system_health', message)

def publish_alert(broker: RedisMessageBroker, alert_level: str, alert_message: str, details: Dict[str, Any] = None):
    """Publish system alert"""
    message = {
        'event_type': 'system_alert',
        'level': alert_level,
        'message': alert_message,
        'details': details or {}
    }
    return broker.publish_message('alerts', message)


# Global broker instance (initialized by main application)
_global_broker: Optional[RedisMessageBroker] = None

def get_broker() -> Optional[RedisMessageBroker]:
    """Get the global broker instance"""
    return _global_broker

def initialize_broker(host: str = 'redis', port: int = 6379, db: int = 0) -> RedisMessageBroker:
    """Initialize the global broker instance"""
    global _global_broker
    _global_broker = RedisMessageBroker(host=host, port=port, db=db)
    return _global_broker

def close_broker():
    """Close the global broker instance"""
    global _global_broker
    if _global_broker:
        _global_broker.close()
        _global_broker = None


if __name__ == "__main__":
    # Test the Redis broker
    logging.basicConfig(level=logging.INFO)
    
    def test_callback(message):
        print(f"Received message: {message}")
    
    # Initialize broker
    broker = initialize_broker()
    
    # Test subscription
    broker.subscribe_to_channel('camera_capture', test_callback)
    
    # Test publishing
    time.sleep(1)  # Let subscriber start
    publish_camera_capture(broker, "/test/image.jpg", {"test": True})
    
    # Health check
    health = broker.health_check()
    print(f"Redis health: {health}")
    
    time.sleep(2)  # Let message process
    
    # Cleanup
    close_broker()