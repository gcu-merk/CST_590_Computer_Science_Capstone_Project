import cv2
import numpy as np
import logging
from datetime import datetime
from typing import Dict, Tuple, Optional
import warnings

# DEPRECATION WARNING
warnings.warn(
    "sky_analyzer_legacy.py is deprecated. Use sky_analysis_service.py instead. "
    "This legacy module will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2
)

logger = logging.getLogger(__name__)
logger.warning("DEPRECATED: sky_analyzer_legacy.py is deprecated. Use sky_analysis_service.py instead.")

# Import shared volume image provider for host-capture architecture
try:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from shared_volume_image_provider import SharedVolumeImageProvider
    SHARED_VOLUME_AVAILABLE = True
except ImportError:
    SHARED_VOLUME_AVAILABLE = False

logger = logging.getLogger(__name__)

class SkyAnalyzer:
    """
    DEPRECATED: Analyzes sky conditions using camera feed for weather assessment
    
    WARNING: This class is deprecated. Use SkyAnalysisService instead.
    This legacy implementation will be removed in a future version.
    """
    
    def __init__(self, use_shared_volume: bool = True):
        warnings.warn(
            "SkyAnalyzer is deprecated. Use SkyAnalysisService from sky_analysis_service.py instead.",
            DeprecationWarning,
            stacklevel=2
        )
        logger.warning("DEPRECATED: SkyAnalyzer is deprecated. Use SkyAnalysisService instead.")
        self.sky_region_ratio = 0.3  # Top 30% of image is sky
        self.confidence_threshold = 0.7
        
        # Initialize shared volume image provider if available
        self.shared_image_provider = None
        if use_shared_volume and SHARED_VOLUME_AVAILABLE:
            try:
                self.shared_image_provider = SharedVolumeImageProvider()
                self.shared_image_provider.start_monitoring()
                logger.info("Sky analyzer initialized with shared volume image provider")
            except Exception as e:
                logger.warning(f"Failed to initialize shared volume provider: {e}")
        
        if not self.shared_image_provider:
            logger.info("Sky analyzer using direct image input (no shared volume)")
        
    def analyze_sky_condition(self, image: np.ndarray) -> Dict:
        """
        Analyze sky condition from camera image
        
        Args:
            image: OpenCV image array (BGR format)
            
        Returns:
            Dict with condition, confidence, and metrics
        """
        try:
            # Extract sky region (top portion of image)
            height, width = image.shape[:2]
            sky_region = image[0:int(height * self.sky_region_ratio), :]
            
            # Perform multiple analysis methods
            color_result = self._analyze_color(sky_region)
            brightness_result = self._analyze_brightness(sky_region)
            texture_result = self._analyze_texture(sky_region)
            
            # Combine results with weighted voting
            condition, confidence = self._combine_results(
                color_result, brightness_result, texture_result
            )
            
            return {
                'condition': condition,  # 'clear', 'partly_cloudy', 'cloudy'
                'confidence': confidence,
                'timestamp': datetime.now().isoformat(),
                'analysis_methods': {
                    'color': color_result,
                    'brightness': brightness_result,
                    'texture': texture_result
                },
                'sky_region_size': sky_region.shape
            }
            
        except Exception as e:
            return {
                'condition': 'unknown',
                'confidence': 0.0,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _analyze_color(self, sky_region: np.ndarray) -> Dict:
        """Analyze sky condition based on color distribution"""
        hsv = cv2.cvtColor(sky_region, cv2.COLOR_BGR2HSV)
        
        # Define color ranges for different sky conditions
        blue_sky = cv2.inRange(hsv, (100, 50, 50), (130, 255, 255))
        gray_clouds = cv2.inRange(hsv, (0, 0, 50), (180, 30, 200))
        white_clouds = cv2.inRange(hsv, (0, 0, 200), (180, 30, 255))
        
        total_pixels = sky_region.shape[0] * sky_region.shape[1]
        blue_ratio = np.sum(blue_sky > 0) / total_pixels
        gray_ratio = np.sum(gray_clouds > 0) / total_pixels
        white_ratio = np.sum(white_clouds > 0) / total_pixels
        cloud_ratio = gray_ratio + white_ratio
        
        # Classify based on color ratios
        if blue_ratio > 0.7:
            condition = 'clear'
            confidence = min(blue_ratio, 0.95)
        elif cloud_ratio > 0.6:
            condition = 'cloudy'
            confidence = min(cloud_ratio, 0.95)
        else:
            condition = 'partly_cloudy'
            confidence = 0.7
            
        return {
            'condition': condition,
            'confidence': confidence,
            'blue_ratio': blue_ratio,
            'cloud_ratio': cloud_ratio,
            'metrics': {
                'blue_pixels': blue_ratio,
                'gray_cloud_pixels': gray_ratio,
                'white_cloud_pixels': white_ratio
            }
        }
    
    def _analyze_brightness(self, sky_region: np.ndarray) -> Dict:
        """Analyze sky condition based on brightness and contrast"""
        gray_sky = cv2.cvtColor(sky_region, cv2.COLOR_BGR2GRAY)
        
        mean_brightness = np.mean(gray_sky)
        std_brightness = np.std(gray_sky)
        contrast = std_brightness / mean_brightness if mean_brightness > 0 else 0
        
        # Classification based on brightness patterns
        if mean_brightness > 180 and contrast < 0.3:
            condition = 'clear'
            confidence = 0.8
        elif mean_brightness < 120 or contrast > 0.6:
            condition = 'cloudy'
            confidence = 0.8
        else:
            condition = 'partly_cloudy'
            confidence = 0.7
            
        return {
            'condition': condition,
            'confidence': confidence,
            'mean_brightness': float(mean_brightness),
            'contrast': float(contrast),
            'std_brightness': float(std_brightness)
        }
    
    def _analyze_texture(self, sky_region: np.ndarray) -> Dict:
        """Analyze sky condition based on texture patterns"""
        gray = cv2.cvtColor(sky_region, cv2.COLOR_BGR2GRAY)
        
        # Calculate local variance for texture analysis
        kernel = np.ones((5, 5), np.float32) / 25
        mean_filtered = cv2.filter2D(gray.astype(np.float32), -1, kernel)
        variance = cv2.filter2D((gray.astype(np.float32) - mean_filtered) ** 2, -1, kernel)
        texture_variance = np.mean(variance)
        
        # Edge detection for cloud boundaries
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / (gray.shape[0] * gray.shape[1])
        
        # Classification based on texture
        if texture_variance < 100 and edge_density < 0.05:
            condition = 'clear'
            confidence = 0.75
        elif texture_variance > 400 or edge_density > 0.15:
            condition = 'cloudy'
            confidence = 0.75
        else:
            condition = 'partly_cloudy'
            confidence = 0.7
            
        return {
            'condition': condition,
            'confidence': confidence,
            'texture_variance': float(texture_variance),
            'edge_density': float(edge_density)
        }
    
    def _combine_results(self, color_result: Dict, brightness_result: Dict, 
                        texture_result: Dict) -> Tuple[str, float]:
        """Combine results from multiple analysis methods"""
        
        # Weight the different methods
        weights = {'color': 0.5, 'brightness': 0.3, 'texture': 0.2}
        
        # Count votes for each condition
        votes = {'clear': 0, 'partly_cloudy': 0, 'cloudy': 0}
        confidence_sum = 0
        
        results = [
            ('color', color_result),
            ('brightness', brightness_result),
            ('texture', texture_result)
        ]
        
        for method, result in results:
            condition = result['condition']
            confidence = result['confidence']
            weight = weights[method]
            
            votes[condition] += weight * confidence
            confidence_sum += weight * confidence
        
        # Find the condition with highest weighted vote
        final_condition = max(votes, key=votes.get)
        final_confidence = min(votes[final_condition], 0.95)
        
        return final_condition, final_confidence
    
    def get_visibility_estimate(self, condition: str, confidence: float) -> str:
        """Estimate visibility based on sky condition"""
        if condition == 'clear' and confidence > 0.8:
            return 'excellent'
        elif condition == 'clear':
            return 'good'
        elif condition == 'partly_cloudy':
            return 'fair'
        elif condition == 'cloudy' and confidence > 0.8:
            return 'poor'
        else:
            return 'variable'
    
    def analyze_current_sky(self, max_age_seconds: float = 5.0) -> Dict:
        """
        Analyze current sky condition using shared volume image provider
        
        Args:
            max_age_seconds: Maximum age of image to use for analysis
            
        Returns:
            Dict with analysis results or error information
        """
        if not self.shared_image_provider:
            return {
                'error': 'Shared volume image provider not available',
                'condition': 'unknown',
                'confidence': 0.0,
                'timestamp': datetime.now().isoformat()
            }
        
        try:
            # Get latest image from shared volume
            success, image, metadata = self.shared_image_provider.get_latest_image(max_age_seconds)
            
            if not success or image is None:
                return {
                    'error': 'No recent image available from shared volume',
                    'condition': 'unknown',
                    'confidence': 0.0,
                    'timestamp': datetime.now().isoformat(),
                    'max_age_seconds': max_age_seconds
                }
            
            # Analyze the image
            analysis_result = self.analyze_sky_condition(image)
            
            # Add source information
            analysis_result['image_source'] = 'shared_volume'
            analysis_result['image_metadata'] = metadata
            analysis_result['image_age_seconds'] = metadata.get('capture_time', 0) if metadata else None
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error analyzing current sky: {e}")
            return {
                'error': str(e),
                'condition': 'unknown',
                'confidence': 0.0,
                'timestamp': datetime.now().isoformat()
            }
    
    def get_latest_image(self, max_age_seconds: float = 10.0) -> Tuple[bool, Optional[np.ndarray], Optional[Dict]]:
        """
        Get the latest image for analysis
        
        Args:
            max_age_seconds: Maximum age of image to accept
            
        Returns:
            Tuple of (success, image_array, metadata)
        """
        if self.shared_image_provider:
            return self.shared_image_provider.get_latest_image(max_age_seconds)
        else:
            return False, None, {'error': 'No image provider available'}
    
    def get_provider_status(self) -> Dict:
        """Get status of the image provider"""
        if self.shared_image_provider:
            return self.shared_image_provider.get_status()
        else:
            return {'status': 'no_provider', 'shared_volume_available': SHARED_VOLUME_AVAILABLE}
    
    def cleanup(self):
        """Clean up resources"""
        if self.shared_image_provider:
            self.shared_image_provider.stop_monitoring()
            logger.info("Sky analyzer cleaned up shared volume provider")