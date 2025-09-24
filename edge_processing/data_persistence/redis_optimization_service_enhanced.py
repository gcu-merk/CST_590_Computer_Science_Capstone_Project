#!/usr/bin/env python3
"""
Enhanced Redis Optimization Service - WITH CENTRALIZED LOGGING
Implements intelligent TTL policies to manage Redis memory efficiently with full observability

This enhanced service reduces Redis memory usage by applying proper TTL policies with comprehensive logging:
- Sky analysis data: 24-hour TTL (manages 36K+ records)
- Vehicle detections: 7-day TTL for recent analysis  
- Weather data: 1-hour TTL (keep only current)
- Radar data: Current only (no accumulation)

Enhanced Features:
- Centralized logging with ServiceLogger and CorrelationContext integration
- Redis operation monitoring and performance tracking
- Memory usage optimization with detailed analytics
- Key lifecycle management with business event logging
- Intelligent cleanup strategies with correlation tracking
- Real-time Redis health and performance monitoring

The goal is to maintain system performance while reducing Redis storage
from 38,491+ keys to manageable levels with full observability.
"""

import time
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any
from pathlib import Path
import os
import sys
import uuid
from collections import defaultdict

# Add edge_processing to path for shared_logging
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))
from shared_logging import ServiceLogger, CorrelationContext

# Redis for data management with logging
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

# Initialize centralized logging
logger = ServiceLogger("redis_optimization_service")

class EnhancedRedisOptimizationService:
    """
    Enhanced intelligent Redis data lifecycle management with comprehensive logging
    Reduces memory usage while maintaining operational data availability with full observability
    """
    
    def __init__(self,
                 redis_host: str = "redis",
                 redis_port: int = 6379,
                 optimization_interval: int = 3600,  # 1 hour
                 memory_threshold_mb: int = 1000):    # 1GB threshold
        
        if not REDIS_AVAILABLE:
            logger.error("Redis required for optimization service", extra={
                "business_event": "service_initialization_failure",
                "error": "redis_unavailable"
            })
            raise RuntimeError("Redis required for optimization service")
        
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.optimization_interval = optimization_interval
        self.memory_threshold_mb = memory_threshold_mb
        
        # Service state
        self.running = False
        self.redis_client = None
        
        # Processing threads
        self.optimization_thread = None
        self.monitoring_thread = None
        
        # Statistics tracking
        self.stats = {
            "keys_processed": 0,
            "keys_deleted": 0,
            "keys_with_ttl_set": 0,
            "memory_saved_mb": 0.0,
            "optimization_cycles": 0,
            "last_optimization": None,
            "startup_time": None,
            "redis_memory_usage_mb": 0.0,
            "total_keys_count": 0
        }
        
        # TTL policies for different data types
        self.ttl_policies = {
            "sky:analysis:*": 86400,           # 24 hours for sky analysis
            "vehicle:detection:*": 604800,    # 7 days for vehicle detections
            "vehicle:track:*": 604800,        # 7 days for vehicle tracks
            "weather:*": 3600,                # 1 hour for weather data
            "radar:current": 300,             # 5 minutes for current radar
            "radar:history:*": 3600,          # 1 hour for radar history
            "consolidator:*": 1800,           # 30 minutes for consolidator data
            "camera:capture:*": 86400,        # 24 hours for camera captures
            "system:health:*": 300,           # 5 minutes for health data
            "api:cache:*": 900                # 15 minutes for API cache
        }
        
        # Priority cleanup order (highest priority first)
        self.cleanup_priorities = [
            "sky:analysis:*",
            "radar:history:*", 
            "vehicle:track:*",
            "camera:capture:*",
            "consolidator:*",
            "weather:*",
            "api:cache:*"
        ]
        
        logger.info("Enhanced Redis Optimization Service initialized", extra={
            "business_event": "service_initialization",
            "redis_host": self.redis_host,
            "optimization_interval_sec": self.optimization_interval,
            "memory_threshold_mb": self.memory_threshold_mb,
            "ttl_policies_count": len(self.ttl_policies)
        })
    
    def connect_redis(self) -> bool:
        """Connect to Redis with enhanced logging"""
        try:
            self.redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=10
            )
            
            # Test connection
            start_time = time.time()
            self.redis_client.ping()
            connection_time_ms = (time.time() - start_time) * 1000
            
            logger.info("Redis connection established successfully", extra={
                "business_event": "redis_connection_established",
                "redis_host": self.redis_host,
                "redis_port": self.redis_port,
                "connection_time_ms": round(connection_time_ms, 2)
            })
            return True
            
        except Exception as e:
            logger.error("Failed to connect to Redis", extra={
                "business_event": "redis_connection_failure",
                "redis_host": self.redis_host,
                "redis_port": self.redis_port,
                "error": str(e)
            })
            return False
    
    @logger.monitor_performance("redis_memory_analysis")
    def analyze_redis_memory(self) -> Dict[str, Any]:
        """Analyze Redis memory usage with performance monitoring"""
        correlation_id = CorrelationContext.get_correlation_id() or str(uuid.uuid4())[:8]
        
        try:
            with CorrelationContext.set_correlation_id(correlation_id):
                # Get Redis memory info
                memory_info = self.redis_client.info('memory')
                
                # Get key statistics
                keyspace_info = self.redis_client.info('keyspace')
                total_keys = sum(
                    int(db_info.split(',')[0].split('=')[1]) 
                    for db_info in keyspace_info.values()
                ) if keyspace_info else 0
                
                # Analyze key patterns
                key_patterns = defaultdict(int)
                sample_keys = self.redis_client.keys('*')
                
                for key in sample_keys[:1000]:  # Sample first 1000 keys
                    pattern = self._get_key_pattern(key)
                    key_patterns[pattern] += 1
                
                memory_analysis = {
                    "used_memory_mb": round(memory_info.get('used_memory', 0) / (1024 * 1024), 2),
                    "used_memory_peak_mb": round(memory_info.get('used_memory_peak', 0) / (1024 * 1024), 2),
                    "total_keys": total_keys,
                    "key_patterns": dict(key_patterns),
                    "fragmentation_ratio": memory_info.get('mem_fragmentation_ratio', 1.0),
                    "timestamp": datetime.now().isoformat()
                }
                
                # Update stats
                self.stats["redis_memory_usage_mb"] = memory_analysis["used_memory_mb"]
                self.stats["total_keys_count"] = total_keys
                
                logger.info("Redis memory analysis completed", extra={
                    "business_event": "redis_memory_analysis",
                    "correlation_id": correlation_id,
                    "memory_usage_mb": memory_analysis["used_memory_mb"],
                    "total_keys": total_keys,
                    "fragmentation_ratio": memory_analysis["fragmentation_ratio"],
                    "key_pattern_count": len(key_patterns)
                })
                
                return memory_analysis
                
        except Exception as e:
            logger.error("Redis memory analysis failed", extra={
                "business_event": "redis_memory_analysis_failure",
                "correlation_id": correlation_id,
                "error": str(e)
            })
            return {}
    
    def _get_key_pattern(self, key: str) -> str:
        """Extract pattern from Redis key"""
        # Match against known patterns
        for pattern in self.ttl_policies.keys():
            if pattern.endswith('*'):
                prefix = pattern[:-1]
                if key.startswith(prefix):
                    return pattern
            elif pattern == key:
                return pattern
        
        # Generate generic pattern
        parts = key.split(':')
        if len(parts) > 1:
            return f"{parts[0]}:*"
        else:
            return "other"
    
    @logger.monitor_performance("redis_optimization_cycle")
    def run_optimization_cycle(self) -> Dict[str, Any]:
        """Run complete optimization cycle with correlation tracking"""
        correlation_id = str(uuid.uuid4())[:8]
        
        with CorrelationContext.set_correlation_id(correlation_id):
            logger.info("Starting Redis optimization cycle", extra={
                "business_event": "optimization_cycle_start",
                "correlation_id": correlation_id,
                "cycle_number": self.stats["optimization_cycles"] + 1
            })
            
            try:
                optimization_results = {
                    "keys_processed": 0,
                    "keys_deleted": 0,
                    "keys_ttl_set": 0,
                    "memory_before_mb": self.stats["redis_memory_usage_mb"],
                    "memory_after_mb": 0.0,
                    "patterns_processed": {},
                    "start_time": datetime.now().isoformat()
                }
                
                # Analyze current memory usage
                memory_analysis = self.analyze_redis_memory()
                optimization_results["memory_before_mb"] = memory_analysis.get("used_memory_mb", 0)
                
                # Process TTL policies
                for pattern, ttl_seconds in self.ttl_policies.items():
                    pattern_results = self._apply_ttl_policy(pattern, ttl_seconds, correlation_id)
                    optimization_results["keys_processed"] += pattern_results["keys_processed"]
                    optimization_results["keys_ttl_set"] += pattern_results["keys_ttl_set"]
                    optimization_results["patterns_processed"][pattern] = pattern_results
                
                # Cleanup expired keys if memory threshold exceeded
                if memory_analysis.get("used_memory_mb", 0) > self.memory_threshold_mb:
                    cleanup_results = self._emergency_cleanup(correlation_id)
                    optimization_results["keys_deleted"] += cleanup_results["keys_deleted"]
                
                # Final memory analysis
                final_memory = self.analyze_redis_memory()
                optimization_results["memory_after_mb"] = final_memory.get("used_memory_mb", 0)
                optimization_results["memory_saved_mb"] = round(
                    optimization_results["memory_before_mb"] - optimization_results["memory_after_mb"], 2
                )
                optimization_results["end_time"] = datetime.now().isoformat()
                
                # Update service statistics
                self.stats["keys_processed"] += optimization_results["keys_processed"]
                self.stats["keys_deleted"] += optimization_results["keys_deleted"]
                self.stats["keys_with_ttl_set"] += optimization_results["keys_ttl_set"]
                self.stats["memory_saved_mb"] += optimization_results["memory_saved_mb"]
                self.stats["optimization_cycles"] += 1
                self.stats["last_optimization"] = optimization_results["end_time"]
                
                logger.info("Redis optimization cycle completed", extra={
                    "business_event": "optimization_cycle_completed",
                    "correlation_id": correlation_id,
                    "keys_processed": optimization_results["keys_processed"],
                    "keys_deleted": optimization_results["keys_deleted"],
                    "memory_saved_mb": optimization_results["memory_saved_mb"],
                    "cycle_duration_sec": round(
                        (datetime.fromisoformat(optimization_results["end_time"]) - 
                         datetime.fromisoformat(optimization_results["start_time"])).total_seconds(), 2
                    )
                })
                
                return optimization_results
                
            except Exception as e:
                logger.error("Redis optimization cycle failed", extra={
                    "business_event": "optimization_cycle_failure",
                    "correlation_id": correlation_id,
                    "error": str(e)
                })
                return {"error": str(e)}
    
    def _apply_ttl_policy(self, pattern: str, ttl_seconds: int, correlation_id: str) -> Dict[str, Any]:
        """Apply TTL policy to keys matching pattern"""
        try:
            # Get matching keys
            if pattern.endswith('*'):
                matching_keys = self.redis_client.keys(pattern)
            else:
                matching_keys = [pattern] if self.redis_client.exists(pattern) else []
            
            keys_processed = len(matching_keys)
            keys_ttl_set = 0
            
            # Apply TTL to keys that don't have one
            for key in matching_keys:
                try:
                    current_ttl = self.redis_client.ttl(key)
                    if current_ttl == -1:  # Key has no TTL
                        self.redis_client.expire(key, ttl_seconds)
                        keys_ttl_set += 1
                except Exception as e:
                    logger.warning("Failed to set TTL for key", extra={
                        "correlation_id": correlation_id,
                        "key": key,
                        "error": str(e)
                    })
            
            logger.debug("TTL policy applied", extra={
                "business_event": "ttl_policy_applied",
                "correlation_id": correlation_id,
                "pattern": pattern,
                "ttl_seconds": ttl_seconds,
                "keys_processed": keys_processed,
                "keys_ttl_set": keys_ttl_set
            })
            
            return {
                "keys_processed": keys_processed,
                "keys_ttl_set": keys_ttl_set,
                "pattern": pattern,
                "ttl_seconds": ttl_seconds
            }
            
        except Exception as e:
            logger.error("Failed to apply TTL policy", extra={
                "business_event": "ttl_policy_failure",
                "correlation_id": correlation_id,
                "pattern": pattern,
                "error": str(e)
            })
            return {"keys_processed": 0, "keys_ttl_set": 0, "error": str(e)}
    
    def _emergency_cleanup(self, correlation_id: str) -> Dict[str, Any]:
        """Perform emergency cleanup when memory threshold exceeded"""
        logger.warning("Performing emergency Redis cleanup", extra={
            "business_event": "emergency_cleanup_start",
            "correlation_id": correlation_id,
            "memory_threshold_mb": self.memory_threshold_mb,
            "current_memory_mb": self.stats["redis_memory_usage_mb"]
        })
        
        keys_deleted = 0
        
        try:
            # Process cleanup priorities
            for pattern in self.cleanup_priorities:
                # Find old keys (no TTL or TTL > 1 day)
                if pattern.endswith('*'):
                    keys_to_check = self.redis_client.keys(pattern)
                else:
                    keys_to_check = [pattern] if self.redis_client.exists(pattern) else []
                
                for key in keys_to_check:
                    try:
                        ttl = self.redis_client.ttl(key)
                        # Delete keys with no TTL or TTL > 86400 seconds (1 day)
                        if ttl == -1 or ttl > 86400:
                            # Check key age if possible
                            key_age_seconds = time.time() - self.redis_client.object('idletime', key) if self.redis_client.exists(key) else 0
                            
                            if key_age_seconds > 86400:  # Older than 1 day
                                self.redis_client.delete(key)
                                keys_deleted += 1
                                
                    except Exception as e:
                        logger.debug("Error checking key for cleanup", extra={
                            "key": key,
                            "error": str(e)
                        })
                
                # Check if we've freed enough memory (rough estimation)
                if keys_deleted > 100:  # Stop after deleting 100 keys per pattern
                    break
            
            logger.warning("Emergency Redis cleanup completed", extra={
                "business_event": "emergency_cleanup_completed",
                "correlation_id": correlation_id,
                "keys_deleted": keys_deleted
            })
            
        except Exception as e:
            logger.error("Emergency cleanup failed", extra={
                "business_event": "emergency_cleanup_failure",
                "correlation_id": correlation_id,
                "error": str(e)
            })
        
        return {"keys_deleted": keys_deleted}
    
    def start(self) -> bool:
        """Start the enhanced optimization service"""
        try:
            logger.info("Starting Enhanced Redis Optimization Service", extra={
                "business_event": "service_startup",
                "optimization_interval_sec": self.optimization_interval,
                "memory_threshold_mb": self.memory_threshold_mb
            })
            
            if not self.connect_redis():
                logger.error("Cannot start without Redis connection")
                return False
            
            self.running = True
            self.stats["startup_time"] = time.time()
            
            # Start background threads
            self.optimization_thread = threading.Thread(
                target=self._optimization_loop,
                daemon=True
            )
            self.optimization_thread.start()
            
            self.monitoring_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True
            )
            self.monitoring_thread.start()
            
            logger.info("Enhanced Redis Optimization Service started successfully", extra={
                "business_event": "service_startup_success",
                "redis_connection_established": self.redis_client is not None
            })
            return True
            
        except Exception as e:
            logger.error("Failed to start Enhanced Redis Optimization Service", extra={
                "business_event": "service_startup_failure",
                "error": str(e)
            })
            return False
    
    def _optimization_loop(self):
        """Background optimization loop with correlation tracking"""
        logger.info("Starting Redis optimization loop", extra={
            "business_event": "optimization_loop_start",
            "optimization_interval_sec": self.optimization_interval
        })
        
        while self.running:
            try:
                # Wait for next optimization cycle
                time.sleep(self.optimization_interval)
                
                if self.running:  # Check if still running after sleep
                    self.run_optimization_cycle()
                    
            except Exception as e:
                logger.error("Error in optimization loop", extra={
                    "business_event": "optimization_loop_error",
                    "error": str(e)
                })
                time.sleep(60)  # Wait 1 minute before retrying
    
    def _monitoring_loop(self):
        """Background monitoring loop for Redis health"""
        logger.info("Starting Redis monitoring loop", extra={
            "business_event": "monitoring_loop_start"
        })
        
        while self.running:
            try:
                time.sleep(300)  # Monitor every 5 minutes
                
                if self.running:
                    self._perform_health_monitoring()
                    
            except Exception as e:
                logger.error("Error in monitoring loop", extra={
                    "business_event": "monitoring_loop_error",
                    "error": str(e)
                })
    
    def _perform_health_monitoring(self):
        """Perform Redis health and performance monitoring"""
        correlation_id = str(uuid.uuid4())[:8]
        
        try:
            with CorrelationContext.set_correlation_id(correlation_id):
                # Get Redis info
                info = self.redis_client.info()
                
                # Extract key metrics
                health_metrics = {
                    "connected_clients": info.get('connected_clients', 0),
                    "blocked_clients": info.get('blocked_clients', 0),
                    "used_memory_mb": round(info.get('used_memory', 0) / (1024 * 1024), 2),
                    "keyspace_hits": info.get('keyspace_hits', 0),
                    "keyspace_misses": info.get('keyspace_misses', 0),
                    "expired_keys": info.get('expired_keys', 0),
                    "evicted_keys": info.get('evicted_keys', 0),
                    "commands_processed": info.get('total_commands_processed', 0),
                    "uptime_seconds": info.get('uptime_in_seconds', 0)
                }
                
                # Calculate hit rate
                total_requests = health_metrics["keyspace_hits"] + health_metrics["keyspace_misses"]
                hit_rate = (health_metrics["keyspace_hits"] / total_requests * 100) if total_requests > 0 else 0
                health_metrics["hit_rate_percent"] = round(hit_rate, 2)
                
                logger.info("Redis health monitoring completed", extra={
                    "business_event": "redis_health_monitoring",
                    "correlation_id": correlation_id,
                    "health_metrics": health_metrics
                })
                
        except Exception as e:
            logger.error("Redis health monitoring failed", extra={
                "business_event": "redis_health_monitoring_failure",
                "correlation_id": correlation_id,
                "error": str(e)
            })
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get comprehensive service statistics"""
        uptime_seconds = (time.time() - self.stats["startup_time"]) if self.stats["startup_time"] else 0
        
        return {
            **self.stats,
            "uptime_seconds": uptime_seconds,
            "service_running": self.running,
            "ttl_policies": self.ttl_policies,
            "optimization_efficiency_percent": round(
                (self.stats["keys_with_ttl_set"] / max(1, self.stats["keys_processed"])) * 100, 2
            )
        }
    
    def stop(self):
        """Stop the optimization service"""
        logger.info("Stopping Enhanced Redis Optimization Service", extra={
            "business_event": "service_shutdown",
            "final_stats": self.get_service_stats()
        })
        
        self.running = False
        
        if self.redis_client:
            self.redis_client.close()
        
        logger.info("Enhanced Redis Optimization Service stopped", extra={
            "business_event": "service_shutdown_complete"
        })


def main():
    """Main entry point for enhanced Redis optimization service"""
    try:
        # Configuration from environment
        service = EnhancedRedisOptimizationService(
            redis_host=os.environ.get('REDIS_HOST', 'redis'),
            redis_port=int(os.environ.get('REDIS_PORT', 6379)),
            optimization_interval=int(os.environ.get('OPTIMIZATION_INTERVAL', 3600)),
            memory_threshold_mb=int(os.environ.get('MEMORY_THRESHOLD_MB', 1000))
        )
        
        # Start service
        if service.start():
            logger.info("Enhanced Redis Optimization Service running successfully")
            
            # Keep running until interrupted
            try:
                while service.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Shutdown requested by user")
            finally:
                service.stop()
        else:
            logger.error("Failed to start Enhanced Redis Optimization Service")
            sys.exit(1)
            
    except Exception as e:
        logger.error("Enhanced Redis Optimization Service failed", extra={
            "business_event": "service_failure",
            "error": str(e)
        })
        sys.exit(1)


if __name__ == "__main__":
    main()