#!/usr/bin/env python3
"""
Redis Optimization Service
Implements intelligent TTL policies to manage Redis memory efficiently

This service reduces Redis memory usage by applying proper TTL policies:
- Sky analysis data: 24-hour TTL (currently 36K+ records)
- Vehicle detections: 7-day TTL for recent analysis
- Weather data: 1-hour TTL (keep only current)
- Radar data: Current only (no accumulation)

The goal is to maintain system performance while reducing Redis storage
from 38,491 keys to manageable levels focused on operational data.
"""

import time
import json
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
import os

# Redis for data management
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.error("Redis required for optimization service")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RedisOptimizationService:
    """
    Intelligent Redis data lifecycle management
    Reduces memory usage while maintaining operational data availability
    """
    
    def __init__(self,
                 redis_host: str = "redis",
                 redis_port: int = 6379,
                 optimization_interval: int = 3600):  # 1 hour
        
        if not REDIS_AVAILABLE:
            raise RuntimeError("Redis required for optimization service")
        
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.optimization_interval = optimization_interval
        
        # Service state
        self.running = False
        self.redis_client = None
        self.optimization_thread = None
        
        # Optimization policies (sky analysis removed for optimal performance)
        self.ttl_policies = {
            # Vehicle detections - keep 7 days for trending
            'vehicle_detection:*': 604800,  # 7 days
            
            # Weather data - keep 1 hour (current conditions only)
            'weather:dht22:*': 3600,  # 1 hour
            'weather:airport:*': 3600,  # 1 hour
            
            # Radar data - current only (handled by service)
            'radar:latest': 600,  # 10 minutes
            'radar:speed:*': 600,  # 10 minutes
            
            # Consolidation data - keep for database persistence
            'consolidation:history:*': 172800,  # 48 hours
            'consolidation:latest': 3600,  # 1 hour
            
            # System health - recent only
            'health:*': 1800,  # 30 minutes
            'status:*': 1800,  # 30 minutes
        }
        
        # Statistics
        self.keys_processed = 0
        self.keys_expired = 0
        self.memory_freed = 0
        self.startup_time = None
        
        logger.info("Redis Optimization Service initialized")
        logger.info("TTL policies configured for intelligent data lifecycle")
    
    def connect_redis(self) -> bool:
        """Connect to Redis"""
        try:
            self.redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=10
            )
            
            # Test connection
            self.redis_client.ping()
            
            logger.info(f"✅ Connected to Redis at {self.redis_host}:{self.redis_port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            return False
    
    def start(self) -> bool:
        """Start the optimization service"""
        if not self.connect_redis():
            logger.error("Cannot start without Redis connection")
            return False
        
        self.running = True
        self.startup_time = time.time()
        logger.info("⚡ Starting Redis Optimization Service")
        
        # Start optimization thread
        self.optimization_thread = threading.Thread(
            target=self._optimization_loop,
            daemon=True
        )
        self.optimization_thread.start()
        
        # Run initial optimization
        self._run_optimization()
        
        logger.info("✅ Redis optimization service started")
        return True
    
    def _optimization_loop(self):
        """Main optimization loop"""
        logger.info("Redis optimization loop started")
        
        while self.running:
            try:
                time.sleep(self.optimization_interval)
                if self.running:
                    self._run_optimization()
            except Exception as e:
                logger.error(f"Optimization loop error: {e}")
                time.sleep(60)  # Wait before retry
    
    def _run_optimization(self):
        """Run comprehensive Redis optimization"""
        logger.info("🧹 Running Redis optimization...")
        
        start_time = time.time()
        keys_before = self._count_total_keys()
        
        # Apply TTL policies
        self._apply_ttl_policies()
        
        # Clean up expired keys
        self._cleanup_expired_keys()
        
        # Analyze key patterns
        self._analyze_key_patterns()
        
        # Update statistics
        keys_after = self._count_total_keys()
        duration = time.time() - start_time
        
        logger.info(f"✅ Optimization complete in {duration:.2f}s")
        logger.info(f"   Keys before: {keys_before:,}")
        logger.info(f"   Keys after: {keys_after:,}")
        logger.info(f"   Keys processed: {self.keys_processed:,}")
        logger.info(f"   Keys expired: {self.keys_expired:,}")
    
    def _apply_ttl_policies(self):
        """Apply TTL policies to matching key patterns"""
        logger.info("Applying TTL policies...")
        
        for pattern, ttl_seconds in self.ttl_policies.items():
            try:
                # Get keys matching pattern
                keys = self.redis_client.keys(pattern)
                
                if not keys:
                    continue
                
                applied_count = 0
                for key in keys:
                    try:
                        # Check if key already has TTL
                        current_ttl = self.redis_client.ttl(key)
                        
                        # Apply TTL if:
                        # - No TTL set (-1)
                        # - TTL is longer than policy
                        if current_ttl == -1 or (current_ttl > ttl_seconds):
                            self.redis_client.expire(key, ttl_seconds)
                            applied_count += 1
                            self.keys_processed += 1
                    
                    except Exception as e:
                        logger.warning(f"Error setting TTL for {key}: {e}")
                
                if applied_count > 0:
                    hours = ttl_seconds / 3600
                    logger.info(f"   Applied {hours:.1f}h TTL to {applied_count:,} keys matching '{pattern}'")
                
            except Exception as e:
                logger.error(f"Error processing pattern '{pattern}': {e}")
    
    def _cleanup_expired_keys(self):
        """Clean up keys that should be immediately expired"""
        logger.info("Cleaning up stale data...")
        
        # Sky analysis data cleanup removed - sky analysis eliminated
        print("Sky analysis cleanup skipped - feature removed for optimization")
        
        # No sky analysis cleanup needed
        logger.info("   Sky analysis cleanup skipped - feature removed")
    
    def _analyze_key_patterns(self):
        """Analyze current key distribution for insights"""
        try:
            # Count keys by pattern (sky analysis removed)
            patterns = {
                'vehicle_detection': 'vehicle_detection:*',
                'weather_dht22': 'weather:dht22:*',
                'weather_airport': 'weather:airport:*',
                'radar': 'radar:*',
                'consolidation': 'consolidation:*',
                'health': 'health:*',
                'status': 'status:*'
            }
            
            total_keys = 0
            for name, pattern in patterns.items():
                count = len(self.redis_client.keys(pattern))
                total_keys += count
                if count > 0:
                    logger.info(f"   {name}: {count:,} keys")
            
            logger.info(f"   Total managed keys: {total_keys:,}")
            
        except Exception as e:
            logger.error(f"Error analyzing key patterns: {e}")
    
    def _count_total_keys(self) -> int:
        """Count total keys in Redis"""
        try:
            return len(self.redis_client.keys('*'))
        except Exception as e:
            logger.error(f"Error counting keys: {e}")
            return 0
    
    def get_optimization_stats(self) -> Dict[str, any]:
        """Get optimization statistics"""
        uptime = time.time() - self.startup_time if self.startup_time else 0
        
        return {
            'service_uptime': uptime,
            'keys_processed': self.keys_processed,
            'keys_expired': self.keys_expired,
            'memory_freed_mb': self.memory_freed / (1024 * 1024),
            'total_keys': self._count_total_keys(),
            'optimization_interval': self.optimization_interval,
            'ttl_policies': len(self.ttl_policies)
        }
    
    def force_optimization(self):
        """Force immediate optimization run"""
        logger.info("🔧 Force optimization triggered")
        self._run_optimization()
    
    def stop(self):
        """Stop the optimization service"""
        self.running = False
        
        if self.redis_client:
            self.redis_client.close()
        
        logger.info("Redis Optimization Service stopped")

def main():
    """Main entry point"""
    # Configuration
    config = {
        'redis_host': os.getenv('REDIS_HOST', 'localhost'),
        'redis_port': int(os.getenv('REDIS_PORT', '6379')),
        'optimization_interval': int(os.getenv('OPTIMIZATION_INTERVAL', '3600'))
    }
    
    logger.info("=== Redis Optimization Service ===")
    logger.info("Intelligent TTL management for efficient Redis usage")
    
    try:
        optimizer = RedisOptimizationService(**config)
        
        if optimizer.start():
            logger.info("Service running. Press Ctrl+C to stop.")
            
            try:
                while optimizer.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received")
            finally:
                optimizer.stop()
                
            return 0
        else:
            logger.error("Failed to start optimization service")
            return 1
        
    except Exception as e:
        logger.error(f"Service failed: {e}")
        return 1

if __name__ == '__main__':
    import sys
    sys.exit(main())