#!/usr/bin/env python3
"""
Sky Analysis Service for Weather Condition Detection
Analyzes sky conditions from camera images to determine weather and lighting conditions

Features:
- Sky condition classification (clear, overcast, night, etc.)
- Light level analysis for day/night detection
- Cloud coverage estimation
- Weather pattern recognition
- Redis integration for data storage and retrieval
"""

import cv2
import numpy as np
import time
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Optional, Tuple, Dict, Any
from pathlib import Path

# Redis and data models
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.warning("Redis not available - sky analysis will work in standalone mode")

# Import our Redis models
try:
    from .redis_models import (
        SkyAnalysis, SkyCondition, RedisDataManager, RedisKeys
    )
    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False
    logging.warning("Redis models not available - using fallback data structures")

logger = logging.getLogger(__name__)

class SkyAnalysisService:
    """
    Analyzes sky conditions from camera images
    Detects weather conditions, lighting, and cloud coverage
    """
    
    def __init__(self, 
                 redis_host: str = "localhost",
                 redis_port: int = 6379,
                 redis_db: int = 0,
                 enable_redis: bool = True):
        
        self.redis_enabled = enable_redis and REDIS_AVAILABLE and MODELS_AVAILABLE
        self.redis_manager = None
        
        # Initialize Redis connection if available
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
                self.redis_client.ping()  # Test connection
                self.redis_manager = RedisDataManager(self.redis_client)
                logger.info(f"Sky analysis service connected to Redis: {redis_host}:{redis_port}")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}. Running in standalone mode.")
                self.redis_enabled = False
        
        # Analysis thresholds (tunable parameters)
        self.night_threshold = 50  # Average brightness below this = night
        self.overcast_threshold = 0.6  # Cloud coverage above this = overcast
        self.clear_threshold = 0.2  # Cloud coverage below this = clear
        
        # Performance tracking
        self.total_analyses = 0
        self.avg_processing_time = 0.0
        
        logger.info("Sky Analysis Service initialized")
    
    def analyze_image(self, image_path: str, image_id: Optional[str] = None) -> Optional[Dict]:
        """
        Analyze sky conditions in an image
        
        Args:
            image_path: Path to the image file
            image_id: Optional image identifier
            
        Returns:
            Dictionary with analysis results or None if analysis fails
        """
        start_time = time.time()
        
        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return None
        
        try:
            # Load and validate image
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"Failed to load image: {image_path}")
                return None
            
            # Perform sky analysis
            analysis_result = self._analyze_sky_conditions(image)
            
            # Calculate processing time
            processing_time = (time.time() - start_time) * 1000
            
            # Create analysis ID and timestamp
            analysis_id = str(uuid.uuid4())
            timestamp = time.time()
            
            # Prepare result data
            result_data = {
                "analysis_id": analysis_id,
                "image_id": image_id or f"img_{int(timestamp)}",
                "image_path": image_path,
                "timestamp": timestamp,
                "condition": analysis_result["condition"],
                "confidence": analysis_result["confidence"],
                "light_level": analysis_result["light_level"],
                "cloud_coverage": analysis_result["cloud_coverage"],
                "processing_time_ms": processing_time,
                "additional_metadata": {
                    "image_size": f"{image.shape[1]}x{image.shape[0]}",
                    "color_dominance": analysis_result.get("color_dominance", {}),
                    "brightness_stats": analysis_result.get("brightness_stats", {}),
                    "analysis_version": "1.0"
                }
            }
            
            # Store in Redis if available
            if self.redis_enabled and MODELS_AVAILABLE:
                try:
                    sky_analysis = SkyAnalysis(
                        analysis_id=analysis_id,
                        condition=SkyCondition(analysis_result["condition"]),
                        confidence=analysis_result["confidence"],
                        timestamp=timestamp,
                        light_level=analysis_result["light_level"],
                        cloud_coverage=analysis_result["cloud_coverage"],
                        additional_metadata=result_data["additional_metadata"]
                    )
                    
                    self.redis_manager.store_sky_analysis(
                        sky_analysis, 
                        result_data["image_id"]
                    )
                    
                    # Record statistics
                    self.redis_manager.record_sky_condition(sky_analysis.condition)
                    
                    logger.info(f"Sky analysis stored in Redis: {analysis_id}")
                except Exception as e:
                    logger.warning(f"Failed to store sky analysis in Redis: {e}")
            
            # Update performance metrics
            self._update_performance_metrics(processing_time)
            
            logger.info(f"Sky analysis completed: {analysis_result['condition']} "
                       f"(confidence: {analysis_result['confidence']:.2f}, "
                       f"processing: {processing_time:.1f}ms)")
            
            return result_data
            
        except Exception as e:
            logger.error(f"Sky analysis failed for {image_path}: {e}")
            return None
    
    def _analyze_sky_conditions(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Perform the actual sky condition analysis
        
        Args:
            image: OpenCV image array
            
        Returns:
            Dictionary with analysis results
        """
        # Convert to different color spaces for analysis
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Extract sky region (assume top 40% of image is sky)
        height, width = gray.shape
        sky_region = gray[:int(height * 0.4), :]
        sky_region_color = image[:int(height * 0.4), :]
        sky_region_hsv = hsv[:int(height * 0.4), :]
        
        # Calculate basic statistics
        brightness_stats = self._calculate_brightness_stats(sky_region)
        color_dominance = self._analyze_color_dominance(sky_region_color)
        cloud_coverage = self._estimate_cloud_coverage(sky_region, sky_region_hsv)
        
        # Determine primary condition and confidence
        condition, confidence = self._classify_sky_condition(
            brightness_stats, color_dominance, cloud_coverage
        )
        
        return {
            "condition": condition,
            "confidence": confidence,
            "light_level": brightness_stats["normalized_brightness"],
            "cloud_coverage": cloud_coverage,
            "brightness_stats": brightness_stats,
            "color_dominance": color_dominance
        }
    
    def _calculate_brightness_stats(self, gray_region: np.ndarray) -> Dict[str, float]:
        """Calculate brightness statistics for the sky region"""
        mean_brightness = np.mean(gray_region)
        std_brightness = np.std(gray_region)
        max_brightness = np.max(gray_region)
        min_brightness = np.min(gray_region)
        
        # Normalize brightness to 0-1 scale
        normalized_brightness = mean_brightness / 255.0
        
        return {
            "mean": float(mean_brightness),
            "std": float(std_brightness),
            "max": float(max_brightness),
            "min": float(min_brightness),
            "normalized_brightness": float(normalized_brightness)
        }
    
    def _analyze_color_dominance(self, color_region: np.ndarray) -> Dict[str, float]:
        """Analyze color dominance in the sky region"""
        # Calculate mean color values
        mean_bgr = np.mean(color_region.reshape(-1, 3), axis=0)
        
        # Convert to normalized values
        total_intensity = np.sum(mean_bgr)
        if total_intensity > 0:
            blue_dominance = mean_bgr[0] / total_intensity
            green_dominance = mean_bgr[1] / total_intensity
            red_dominance = mean_bgr[2] / total_intensity
        else:
            blue_dominance = green_dominance = red_dominance = 0.33
        
        return {
            "blue": float(blue_dominance),
            "green": float(green_dominance),
            "red": float(red_dominance),
            "blue_green_ratio": float(blue_dominance / (green_dominance + 0.001)),
            "red_blue_ratio": float(red_dominance / (blue_dominance + 0.001))
        }
    
    def _estimate_cloud_coverage(self, gray_region: np.ndarray, hsv_region: np.ndarray) -> float:
        """Estimate cloud coverage percentage"""
        # Use texture analysis and brightness variation to detect clouds
        
        # Calculate local standard deviation (texture measure)
        kernel_size = 15
        kernel = np.ones((kernel_size, kernel_size), np.float32) / (kernel_size * kernel_size)
        local_mean = cv2.filter2D(gray_region.astype(np.float32), -1, kernel)
        local_variance = cv2.filter2D((gray_region.astype(np.float32) - local_mean) ** 2, -1, kernel)
        local_std = np.sqrt(local_variance)
        
        # Threshold for detecting cloud texture
        texture_threshold = np.mean(local_std) + 0.5 * np.std(local_std)
        cloud_pixels = np.sum(local_std > texture_threshold)
        total_pixels = gray_region.size
        
        # Combine with brightness-based detection
        # Clouds often appear as bright regions in contrast to clear sky
        brightness_threshold = np.mean(gray_region) + 0.3 * np.std(gray_region)
        bright_pixels = np.sum(gray_region > brightness_threshold)
        
        # Weighted combination of texture and brightness indicators
        texture_coverage = cloud_pixels / total_pixels
        brightness_coverage = bright_pixels / total_pixels
        
        # Combine measures (texture is more reliable)
        cloud_coverage = 0.7 * texture_coverage + 0.3 * brightness_coverage
        
        return min(1.0, max(0.0, float(cloud_coverage)))
    
    def _classify_sky_condition(self, brightness_stats: Dict, color_dominance: Dict, cloud_coverage: float) -> Tuple[str, float]:
        """
        Classify sky condition based on analysis results
        
        Returns:
            Tuple of (condition_string, confidence_score)
        """
        brightness = brightness_stats["normalized_brightness"]
        blue_dominance = color_dominance["blue"]
        red_blue_ratio = color_dominance["red_blue_ratio"]
        
        # Night detection (low brightness)
        if brightness < 0.2:
            if cloud_coverage > 0.5:
                return "night_cloudy", 0.9
            else:
                return "night_clear", 0.9
        
        # Dawn/dusk detection (moderate brightness with high red)
        if 0.2 <= brightness <= 0.4 and red_blue_ratio > 0.8:
            return "dawn_dusk", 0.8
        
        # Day conditions
        if brightness > 0.4:
            if cloud_coverage > self.overcast_threshold:
                # Check for storm indicators (dark clouds)
                if brightness < 0.5 and color_dominance["blue"] < 0.3:
                    return "stormy", 0.7
                else:
                    return "overcast", 0.8
            elif cloud_coverage < self.clear_threshold:
                return "clear", 0.9
            else:
                return "partly_cloudy", 0.8
        
        # Fallback for unclear conditions
        return "unknown", 0.3
    
    def _update_performance_metrics(self, processing_time: float):
        """Update internal performance tracking"""
        self.total_analyses += 1
        self.avg_processing_time = (
            (self.avg_processing_time * (self.total_analyses - 1) + processing_time) / 
            self.total_analyses
        )
        
        # Update service status in Redis
        if self.redis_enabled:
            try:
                status = {
                    "service": "sky_analysis",
                    "status": "running",
                    "total_analyses": self.total_analyses,
                    "avg_processing_time_ms": self.avg_processing_time,
                    "last_analysis": time.time()
                }
                self.redis_manager.update_service_status("sky_service", status)
            except Exception as e:
                logger.warning(f"Failed to update service status: {e}")
    
    def get_analysis_by_image_id(self, image_id: str) -> Optional[Dict]:
        """Retrieve sky analysis result by image ID"""
        if not self.redis_enabled:
            logger.warning("Redis not available - cannot retrieve stored analysis")
            return None
        
        try:
            key = RedisKeys.format_key(RedisKeys.SKY_ANALYSIS_BY_IMAGE, image_id=image_id)
            data = self.redis_client.get(key)
            if data:
                import json
                return json.loads(data)
        except Exception as e:
            logger.error(f"Failed to retrieve sky analysis for image {image_id}: {e}")
        
        return None
    
    def get_latest_analysis(self) -> Optional[Dict]:
        """Get the most recent sky analysis"""
        if not self.redis_enabled:
            logger.warning("Redis not available - cannot retrieve latest analysis")
            return None
        
        try:
            # This would need to be implemented in RedisDataManager
            # For now, we'll implement a simple approach
            # In practice, you might want to maintain a "latest" key
            pass
        except Exception as e:
            logger.error(f"Failed to retrieve latest sky analysis: {e}")
        
        return None
    
    def cleanup(self):
        """Cleanup resources"""
        if self.redis_enabled and hasattr(self, 'redis_client'):
            try:
                self.redis_client.close()
                logger.info("Sky analysis service Redis connection closed")
            except Exception as e:
                logger.warning(f"Error closing Redis connection: {e}")

def analyze_image_standalone(image_path: str) -> Optional[Dict]:
    """
    Standalone function to analyze a single image
    Useful for testing and manual analysis
    """
    service = SkyAnalysisService(enable_redis=False)
    return service.analyze_image(image_path)

def main():
    """Main function for testing the sky analysis service"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Sky Analysis Service")
    parser.add_argument("--image", type=str, help="Path to image for analysis")
    parser.add_argument("--redis-host", type=str, default="localhost", help="Redis host")
    parser.add_argument("--redis-port", type=int, default=6379, help="Redis port")
    parser.add_argument("--no-redis", action="store_true", help="Disable Redis integration")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize service
    service = SkyAnalysisService(
        redis_host=args.redis_host,
        redis_port=args.redis_port,
        enable_redis=not args.no_redis
    )
    
    try:
        if args.image:
            # Analyze single image
            result = service.analyze_image(args.image)
            if result:
                print(f"\nSky Analysis Results:")
                print(f"Condition: {result['condition']}")
                print(f"Confidence: {result['confidence']:.2f}")
                print(f"Light Level: {result['light_level']:.2f}")
                print(f"Cloud Coverage: {result['cloud_coverage']:.2f}")
                print(f"Processing Time: {result['processing_time_ms']:.1f}ms")
            else:
                print("Analysis failed")
        else:
            print("Sky Analysis Service is running. Use --image to analyze a specific image.")
    
    finally:
        service.cleanup()

if __name__ == "__main__":
    main()