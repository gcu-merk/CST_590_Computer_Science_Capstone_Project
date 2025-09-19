#!/usr/bin/env python3
"""
Motion-Triggered Image Analysis Service
Orchestrates image capture and analysis when motion is detected by radar or other sensors

Features:
- Listens for motion trigger events (radar, manual, scheduled)
- Coordinates vehicle detection and sky analysis services
- Manages image capture timing and processing
- Stores consolidated results in Redis
- Provides fallback mechanisms for service failures
"""

import asyncio
import time
import logging
import os
import json
import uuid
import threading
from datetime import datetime, timezone
from typing import Dict, Optional, List, Any, Callable
from pathlib import Path
import concurrent.futures

# Redis and data models
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.warning("Redis not available - motion service will work in standalone mode")

# Import our services and models
try:
    from ..redis_models import (
        ImageAnalysisResult, VehicleDetection, SkyAnalysis, 
        RedisDataManager, RedisKeys
    )
    from ..weather_analysis.sky_analysis_service import SkyAnalysisService
    from ..vehicle_detection.enhanced_vehicle_detection_service import EnhancedVehicleDetectionService
    SERVICES_AVAILABLE = True
except ImportError:
    try:
        from redis_models import (
            ImageAnalysisResult, VehicleDetection, SkyAnalysis,
            RedisDataManager, RedisKeys
        )
        from weather_analysis.sky_analysis_service import SkyAnalysisService
        from vehicle_detection.enhanced_vehicle_detection_service import EnhancedVehicleDetectionService
        SERVICES_AVAILABLE = True
    except ImportError:
        SERVICES_AVAILABLE = False
        logging.warning("Analysis services not available - motion service will work in limited mode")

# Shared volume image provider for image access
try:
    from ..shared_volume_image_provider import SharedVolumeImageProvider
    SHARED_VOLUME_AVAILABLE = True
except ImportError:
    try:
        from shared_volume_image_provider import SharedVolumeImageProvider
        SHARED_VOLUME_AVAILABLE = True
    except ImportError:
        SHARED_VOLUME_AVAILABLE = False
        logging.warning("Shared volume image provider not available")

logger = logging.getLogger(__name__)

class MotionTriggeredImageService:
    """
    Orchestrates image analysis when motion is detected
    Coordinates multiple analysis services and consolidates results
    """
    
    def __init__(self,
                 redis_host: str = "localhost",
                 redis_port: int = 6379,
                 redis_db: int = 0,
                 enable_redis: bool = True,
                 image_capture_dir: str = None,
                 max_concurrent_analyses: int = 3,
                 analysis_timeout: float = 30.0):
        
        self.redis_enabled = enable_redis and REDIS_AVAILABLE
        self.redis_manager = None
        self.max_concurrent_analyses = max_concurrent_analyses
        self.analysis_timeout = analysis_timeout
        
        # Initialize Redis connection
        if self.redis_enabled:
            try:
                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    db=redis_db,
                    decode_responses=True,
                    socket_timeout=5,
                    socket_connect_timeout=5
                )
                self.redis_client.ping()
                if SERVICES_AVAILABLE:
                    self.redis_manager = RedisDataManager(self.redis_client)
                logger.info(f"Motion service connected to Redis: {redis_host}:{redis_port}")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}. Running in standalone mode.")
                self.redis_enabled = False
        
        # Initialize image provider
        self.image_provider = None
        if SHARED_VOLUME_AVAILABLE:
            try:
                self.image_provider = SharedVolumeImageProvider(capture_dir=image_capture_dir)
                logger.info("Shared volume image provider initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize image provider: {e}")
        
        # Initialize analysis services
        self.sky_service = None
        self.vehicle_service = None
        
        if SERVICES_AVAILABLE:
            try:
                self.sky_service = SkyAnalysisService(
                    redis_host=redis_host,
                    redis_port=redis_port,
                    redis_db=redis_db,
                    enable_redis=enable_redis
                )
                logger.info("Sky analysis service initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize sky analysis service: {e}")
            
            try:
                self.vehicle_service = EnhancedVehicleDetectionService(
                    redis_host=redis_host,
                    redis_port=redis_port,
                    redis_db=redis_db,
                    enable_redis=enable_redis
                )
                logger.info("Enhanced vehicle detection service initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize vehicle detection service: {e}")
        
        # Service state
        self.is_running = False
        self.motion_listener_thread = None
        self.analysis_executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=max_concurrent_analyses
        )
        
        # Performance tracking
        self.total_triggers = 0
        self.successful_analyses = 0
        self.failed_analyses = 0
        self.avg_analysis_time = 0.0
        
        # Trigger callbacks (for extensibility)
        self.trigger_callbacks: List[Callable] = []
        
        logger.info("Motion-Triggered Image Service initialized")
    
    def start(self):
        """Start the motion-triggered image service"""
        if self.is_running:
            logger.warning("Motion service is already running")
            return
        
        self.is_running = True
        
        # Start motion listener thread
        if self.redis_enabled:
            self.motion_listener_thread = threading.Thread(
                target=self._motion_listener_loop,
                daemon=True
            )
            self.motion_listener_thread.start()
            logger.info("Motion listener started - waiting for radar triggers")
        else:
            logger.info("Motion service started in standalone mode")
        
        # Update service status
        self._update_service_status("running")
    
    def stop(self):
        """Stop the motion-triggered image service"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Wait for motion listener to stop
        if self.motion_listener_thread:
            self.motion_listener_thread.join(timeout=5.0)
        
        # Shutdown analysis executor
        self.analysis_executor.shutdown(wait=True)
        
        # Update service status
        self._update_service_status("stopped")
        
        logger.info("Motion-triggered image service stopped")
    
    def _motion_listener_loop(self):
        """Main loop for listening to motion trigger events from Redis"""
        logger.info("Starting motion listener loop")
        
        while self.is_running:
            try:
                # Listen for motion trigger events
                # For now, we'll check for queued analysis requests
                if self.redis_manager:
                    pending_request = self.redis_manager.get_pending_analysis()
                    if pending_request:
                        logger.info(f"Motion trigger received: {pending_request.get('trigger_source', 'unknown')}")
                        self._handle_motion_trigger(pending_request)
                    else:
                        time.sleep(0.1)  # Short sleep when no requests
                else:
                    time.sleep(1.0)  # Longer sleep when Redis unavailable
                    
            except Exception as e:
                logger.error(f"Error in motion listener loop: {e}")
                time.sleep(1.0)
        
        logger.info("Motion listener loop stopped")
    
    def _handle_motion_trigger(self, trigger_data: Dict):
        """Handle a motion trigger event"""
        try:
            self.total_triggers += 1
            
            # Extract trigger information
            image_path = trigger_data.get("image_path")
            trigger_source = trigger_data.get("trigger_source", "unknown")
            timestamp = trigger_data.get("timestamp", time.time())
            
            logger.info(f"Processing motion trigger: {trigger_source} -> {image_path}")
            
            # Submit analysis task to executor
            future = self.analysis_executor.submit(
                self._analyze_triggered_image,
                image_path,
                trigger_source,
                timestamp
            )
            
            # Register completion callback
            future.add_done_callback(self._analysis_completed)
            
            # Call registered trigger callbacks
            for callback in self.trigger_callbacks:
                try:
                    callback(trigger_data)
                except Exception as e:
                    logger.warning(f"Trigger callback failed: {e}")
            
        except Exception as e:
            logger.error(f"Failed to handle motion trigger: {e}")
            self.failed_analyses += 1
    
    def _analyze_triggered_image(self, image_path: str, trigger_source: str, timestamp: float) -> Optional[Dict]:
        """
        Analyze an image triggered by motion detection
        Coordinates both vehicle detection and sky analysis
        """
        start_time = time.time()
        image_id = f"motion_{int(timestamp)}_{str(uuid.uuid4())[:8]}"
        
        try:
            # Verify image exists
            if not image_path or not os.path.exists(image_path):
                logger.error(f"Image not found: {image_path}")
                return None
            
            logger.info(f"Starting analysis for image: {image_id} ({image_path})")
            
            # Run vehicle detection and sky analysis concurrently
            vehicle_future = None
            sky_future = None
            
            if self.vehicle_service:
                vehicle_future = self.analysis_executor.submit(
                    self.vehicle_service.analyze_image,
                    image_path, image_id, trigger_source
                )
            
            if self.sky_service:
                sky_future = self.analysis_executor.submit(
                    self.sky_service.analyze_image,
                    image_path, image_id
                )
            
            # Wait for both analyses to complete
            vehicle_result = None
            sky_result = None
            
            if vehicle_future:
                try:
                    vehicle_result = vehicle_future.result(timeout=self.analysis_timeout)
                except concurrent.futures.TimeoutError:
                    logger.warning(f"Vehicle detection timed out for {image_id}")
                except Exception as e:
                    logger.error(f"Vehicle detection failed for {image_id}: {e}")
            
            if sky_future:
                try:
                    sky_result = sky_future.result(timeout=self.analysis_timeout)
                except concurrent.futures.TimeoutError:
                    logger.warning(f"Sky analysis timed out for {image_id}")
                except Exception as e:
                    logger.error(f"Sky analysis failed for {image_id}: {e}")
            
            # Calculate total processing time
            processing_time = (time.time() - start_time) * 1000
            
            # Create consolidated result
            result = self._create_consolidated_result(
                image_id, image_path, timestamp, trigger_source,
                vehicle_result, sky_result, processing_time
            )
            
            # Store consolidated result
            if result and self.redis_enabled and SERVICES_AVAILABLE:
                try:
                    consolidated_data = self._create_redis_consolidated_data(result)
                    self.redis_manager.store_consolidated_data(consolidated_data)
                    logger.info(f"Consolidated analysis stored for {image_id}")
                except Exception as e:
                    logger.warning(f"Failed to store consolidated data: {e}")
            
            logger.info(f"Analysis completed for {image_id}: "
                       f"{len(vehicle_result.get('vehicle_detections', []) if vehicle_result else [])} vehicles, "
                       f"sky: {sky_result.get('condition', 'unknown') if sky_result else 'unknown'} "
                       f"(total: {processing_time:.1f}ms)")
            
            return result
            
        except Exception as e:
            logger.error(f"Image analysis failed for {image_id}: {e}")
            return None
    
    def _create_consolidated_result(self, image_id: str, image_path: str, timestamp: float,
                                  trigger_source: str, vehicle_result: Optional[Dict],
                                  sky_result: Optional[Dict], processing_time: float) -> Dict:
        """Create consolidated analysis result"""
        
        # Extract vehicle detections
        vehicle_detections = []
        if vehicle_result and vehicle_result.get('vehicle_detections'):
            vehicle_detections = vehicle_result['vehicle_detections']
        
        # Extract sky analysis
        sky_analysis = {
            "analysis_id": str(uuid.uuid4()),
            "condition": "unknown",
            "confidence": 0.0,
            "timestamp": timestamp,
            "light_level": None,
            "cloud_coverage": None,
            "additional_metadata": {}
        }
        
        if sky_result:
            sky_analysis.update({
                "analysis_id": sky_result.get("analysis_id", sky_analysis["analysis_id"]),
                "condition": sky_result.get("condition", "unknown"),
                "confidence": sky_result.get("confidence", 0.0),
                "light_level": sky_result.get("light_level"),
                "cloud_coverage": sky_result.get("cloud_coverage"),
                "additional_metadata": sky_result.get("additional_metadata", {})
            })
        
        return {
            "image_id": image_id,
            "image_path": image_path,
            "timestamp": timestamp,
            "trigger_source": trigger_source,
            "vehicle_detections": vehicle_detections,
            "sky_analysis": sky_analysis,
            "processing_time_ms": processing_time,
            "image_metadata": {
                "analysis_version": "1.0",
                "services_used": {
                    "vehicle_detection": vehicle_result is not None,
                    "sky_analysis": sky_result is not None
                }
            }
        }
    
    def _create_redis_consolidated_data(self, result: Dict):
        """Create Redis consolidated data object"""
        if not SERVICES_AVAILABLE:
            raise ValueError("Services not available for Redis data creation")
        
        # This would create the proper Redis data structures
        # For now, we'll store as JSON in a simpler format
        return result
    
    def _analysis_completed(self, future: concurrent.futures.Future):
        """Callback for when an analysis task completes"""
        try:
            result = future.result()
            if result:
                self.successful_analyses += 1
            else:
                self.failed_analyses += 1
        except Exception as e:
            logger.error(f"Analysis task failed: {e}")
            self.failed_analyses += 1
        
        # Update performance metrics
        self._update_performance_metrics()
    
    def _update_performance_metrics(self):
        """Update internal performance tracking"""
        total_analyses = self.successful_analyses + self.failed_analyses
        if total_analyses > 0:
            success_rate = self.successful_analyses / total_analyses
        else:
            success_rate = 0.0
        
        # Update service status in Redis
        if self.redis_enabled:
            try:
                status = {
                    "service": "motion_triggered_image",
                    "status": "running" if self.is_running else "stopped",
                    "total_triggers": self.total_triggers,
                    "successful_analyses": self.successful_analyses,
                    "failed_analyses": self.failed_analyses,
                    "success_rate": success_rate,
                    "last_trigger": time.time()
                }
                if self.redis_manager:
                    self.redis_manager.update_service_status("image_service", status)
            except Exception as e:
                logger.warning(f"Failed to update service status: {e}")
    
    def _update_service_status(self, status: str):
        """Update service status"""
        if self.redis_enabled and self.redis_manager:
            try:
                status_data = {
                    "service": "motion_triggered_image",
                    "status": status,
                    "timestamp": time.time()
                }
                self.redis_manager.update_service_status("image_service", status_data)
            except Exception as e:
                logger.warning(f"Failed to update service status: {e}")
    
    def trigger_manual_analysis(self, image_path: str) -> Optional[str]:
        """
        Manually trigger image analysis
        
        Args:
            image_path: Path to image for analysis
            
        Returns:
            Analysis task ID or None if failed
        """
        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return None
        
        try:
            # Queue for analysis
            if self.redis_enabled and self.redis_manager:
                task_id = self.redis_manager.queue_image_for_analysis(image_path, "manual")
                logger.info(f"Manual analysis queued: {image_path}")
                return task_id
            else:
                # Direct analysis in standalone mode
                trigger_data = {
                    "image_path": image_path,
                    "timestamp": time.time(),
                    "trigger_source": "manual"
                }
                self._handle_motion_trigger(trigger_data)
                return str(uuid.uuid4())
        
        except Exception as e:
            logger.error(f"Failed to trigger manual analysis: {e}")
            return None
    
    def add_trigger_callback(self, callback: Callable):
        """Add callback function to be called when motion is triggered"""
        self.trigger_callbacks.append(callback)
    
    def get_analysis_status(self) -> Dict:
        """Get current service status and statistics"""
        return {
            "is_running": self.is_running,
            "total_triggers": self.total_triggers,
            "successful_analyses": self.successful_analyses,
            "failed_analyses": self.failed_analyses,
            "success_rate": (self.successful_analyses / max(1, self.successful_analyses + self.failed_analyses)),
            "services": {
                "redis_enabled": self.redis_enabled,
                "sky_service": self.sky_service is not None,
                "vehicle_service": self.vehicle_service is not None,
                "image_provider": self.image_provider is not None
            }
        }
    
    def cleanup(self):
        """Cleanup resources"""
        self.stop()
        
        if self.sky_service and hasattr(self.sky_service, 'cleanup'):
            self.sky_service.cleanup()
        
        if self.vehicle_service and hasattr(self.vehicle_service, 'cleanup'):
            self.vehicle_service.cleanup()
        
        if self.redis_enabled and hasattr(self, 'redis_client'):
            try:
                self.redis_client.close()
                logger.info("Motion service Redis connection closed")
            except Exception as e:
                logger.warning(f"Error closing Redis connection: {e}")

def main():
    """Main function for testing the motion-triggered image service"""
    import argparse
    import signal
    
    parser = argparse.ArgumentParser(description="Motion-Triggered Image Analysis Service")
    parser.add_argument("--redis-host", type=str, default="localhost", help="Redis host")
    parser.add_argument("--redis-port", type=int, default=6379, help="Redis port")
    parser.add_argument("--no-redis", action="store_true", help="Disable Redis integration")
    parser.add_argument("--image-dir", type=str, help="Image capture directory")
    parser.add_argument("--test-image", type=str, help="Trigger analysis for test image")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize service
    service = MotionTriggeredImageService(
        redis_host=args.redis_host,
        redis_port=args.redis_port,
        enable_redis=not args.no_redis,
        image_capture_dir=args.image_dir
    )
    
    def signal_handler(signum, frame):
        logger.info("Shutdown signal received")
        service.cleanup()
        exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        service.start()
        
        if args.test_image:
            # Test with specific image
            task_id = service.trigger_manual_analysis(args.test_image)
            if task_id:
                print(f"Test analysis triggered: {task_id}")
            else:
                print("Test analysis failed")
        
        print("Motion-triggered image service is running...")
        print("Status:", service.get_analysis_status())
        print("Press Ctrl+C to stop")
        
        # Keep running
        while service.is_running:
            time.sleep(1)
    
    finally:
        service.cleanup()

if __name__ == "__main__":
    main()