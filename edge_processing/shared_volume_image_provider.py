#!/usr/bin/env python3
"""
Shared Volume Image Provider for Docker Container Processing
Reads images captured by host-side rpicam-still and provides them to container services

This module replaces direct camera access in Docker containers to work around
OpenCV 4.12.0 compatibility issues with the IMX500 AI camera's V4L2 backend.
"""

import os
import cv2
import json
import time
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List
import numpy as np
from collections import deque

logger = logging.getLogger(__name__)

class SharedVolumeImageProvider:
    """
    Provides images from shared volume captured by host-side camera service
    Replaces direct camera capture in Docker containers
    """
    
    def __init__(self, 
                 capture_dir: str = "/app/data/camera_capture",
                 max_age_seconds: float = 5.0,
                 fallback_timeout: float = 10.0,
                 image_cache_size: int = 10):
        
        self.capture_dir = Path(capture_dir)
        self.live_dir = self.capture_dir / "live"
        self.metadata_dir = self.capture_dir / "metadata"
        self.snapshots_dir = self.capture_dir / "periodic_snapshots"
        
        self.max_age_seconds = max_age_seconds
        self.fallback_timeout = fallback_timeout
        self.image_cache_size = image_cache_size
        
        # Image cache for performance
        self.image_cache = deque(maxlen=image_cache_size)
        self.cache_lock = threading.Lock()
        
        # State tracking
        self.last_image_path = None
        self.last_image_time = None
        self.consecutive_failures = 0
        self.total_images_processed = 0
        
        # Background monitoring
        self.monitoring_thread = None
        self.monitoring_active = False
        
        logger.info(f"SharedVolumeImageProvider initialized: {self.capture_dir}")
        self._verify_directories()
    
    def _verify_directories(self):
        """Verify that required directories exist"""
        for directory in [self.live_dir, self.metadata_dir, self.snapshots_dir]:
            if not directory.exists():
                logger.warning(f"Directory does not exist: {directory}")
            else:
                logger.debug(f"Directory verified: {directory}")
    
    def start_monitoring(self):
        """Start background monitoring of image directory"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info("Started background image monitoring")
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5)
        logger.info("Stopped background image monitoring")
    
    def _monitor_loop(self):
        """Background monitoring loop"""
        while self.monitoring_active:
            try:
                # Check for new images and update cache
                self._update_image_cache()
                time.sleep(1)  # Check every second
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                time.sleep(5)
    
    def _update_image_cache(self):
        """Update the image cache with recent images"""
        try:
            # Get recent image files
            image_files = list(self.live_dir.glob("*.jpg"))
            if not image_files:
                return
            
            # Sort by modification time (newest first)
            image_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Check if we have new images to cache
            with self.cache_lock:
                for image_file in image_files[:self.image_cache_size]:
                    # Check if already in cache
                    if any(cached['path'] == image_file for cached in self.image_cache):
                        continue
                    
                    # Load and cache the image
                    try:
                        image = cv2.imread(str(image_file))
                        if image is not None:
                            metadata = self._load_image_metadata(image_file)
                            cache_entry = {
                                'path': image_file,
                                'image': image,
                                'metadata': metadata,
                                'load_time': time.time()
                            }
                            self.image_cache.appendleft(cache_entry)
                            logger.debug(f"Cached image: {image_file.name}")
                    except Exception as e:
                        logger.warning(f"Failed to cache image {image_file}: {e}")
        
        except Exception as e:
            logger.error(f"Cache update error: {e}")
    
    def get_latest_image(self, max_age_seconds: Optional[float] = None) -> Tuple[bool, Optional[np.ndarray], Optional[Dict]]:
        """
        Get the latest image from shared volume
        
        Args:
            max_age_seconds: Maximum age of image to accept (None uses default)
            
        Returns:
            Tuple of (success, image_array, metadata)
        """
        if max_age_seconds is None:
            max_age_seconds = self.max_age_seconds
        
        try:
            # First try to get from cache
            with self.cache_lock:
                if self.image_cache:
                    cache_entry = self.image_cache[0]  # Most recent
                    image_age = time.time() - cache_entry['load_time']
                    if image_age <= max_age_seconds:
                        self.consecutive_failures = 0
                        self.total_images_processed += 1
                        return True, cache_entry['image'].copy(), cache_entry['metadata']
            
            # Cache miss or stale - load from disk
            return self._load_latest_image_from_disk(max_age_seconds)
            
        except Exception as e:
            logger.error(f"Failed to get latest image: {e}")
            self.consecutive_failures += 1
            return False, None, None
    
    def _load_latest_image_from_disk(self, max_age_seconds: float) -> Tuple[bool, Optional[np.ndarray], Optional[Dict]]:
        """Load the latest image directly from disk"""
        try:
            # Get all image files
            image_files = list(self.live_dir.glob("*.jpg"))
            if not image_files:
                logger.warning("No images found in capture directory")
                return False, None, None
            
            # Sort by modification time (newest first)
            image_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Check age of newest image
            newest_file = image_files[0]
            image_age = time.time() - newest_file.stat().st_mtime
            
            if image_age > max_age_seconds:
                logger.warning(f"Latest image too old: {image_age:.1f}s > {max_age_seconds:.1f}s")
                return False, None, None
            
            # Load the image
            image = cv2.imread(str(newest_file))
            if image is None:
                logger.error(f"Failed to load image: {newest_file}")
                return False, None, None
            
            # Load metadata
            metadata = self._load_image_metadata(newest_file)
            
            # Update tracking
            self.last_image_path = newest_file
            self.last_image_time = datetime.now()
            self.consecutive_failures = 0
            self.total_images_processed += 1
            
            logger.debug(f"Loaded image: {newest_file.name} (age: {image_age:.1f}s)")
            return True, image, metadata
            
        except Exception as e:
            logger.error(f"Failed to load image from disk: {e}")
            self.consecutive_failures += 1
            return False, None, None
    
    def _load_image_metadata(self, image_path: Path) -> Dict[str, Any]:
        """Load metadata for an image file"""
        metadata_path = self.metadata_dir / f"{image_path.name}.json"
        
        try:
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                return metadata
            else:
                # Create minimal metadata from file info
                stat = image_path.stat()
                return {
                    'filename': image_path.name,
                    'file_size': stat.st_size,
                    'timestamp': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'capture_time': stat.st_mtime,
                    'metadata_source': 'file_stat'
                }
        except Exception as e:
            logger.warning(f"Failed to load metadata for {image_path}: {e}")
            return {
                'filename': image_path.name,
                'error': str(e),
                'metadata_source': 'error'
            }
    
    def get_periodic_snapshot(self, max_age_hours: float = 1.0) -> Tuple[bool, Optional[np.ndarray], Optional[Dict]]:
        """
        Get a recent periodic snapshot for long-term analysis
        
        Args:
            max_age_hours: Maximum age of snapshot in hours
            
        Returns:
            Tuple of (success, image_array, metadata)
        """
        try:
            snapshot_files = list(self.snapshots_dir.glob("snapshot_*.jpg"))
            if not snapshot_files:
                logger.warning("No periodic snapshots found")
                return False, None, None
            
            # Sort by modification time (newest first)
            snapshot_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Check age of newest snapshot
            newest_snapshot = snapshot_files[0]
            snapshot_age_hours = (time.time() - newest_snapshot.stat().st_mtime) / 3600
            
            if snapshot_age_hours > max_age_hours:
                logger.warning(f"Latest snapshot too old: {snapshot_age_hours:.1f}h > {max_age_hours:.1f}h")
                return False, None, None
            
            # Load the snapshot
            image = cv2.imread(str(newest_snapshot))
            if image is None:
                logger.error(f"Failed to load snapshot: {newest_snapshot}")
                return False, None, None
            
            # Create metadata
            metadata = {
                'filename': newest_snapshot.name,
                'file_size': newest_snapshot.stat().st_size,
                'timestamp': datetime.fromtimestamp(newest_snapshot.stat().st_mtime).isoformat(),
                'age_hours': snapshot_age_hours,
                'type': 'periodic_snapshot'
            }
            
            logger.debug(f"Loaded snapshot: {newest_snapshot.name} (age: {snapshot_age_hours:.1f}h)")
            return True, image, metadata
            
        except Exception as e:
            logger.error(f"Failed to get periodic snapshot: {e}")
            return False, None, None
    
    def wait_for_new_image(self, timeout: float = 10.0, min_age_diff: float = 1.0) -> Tuple[bool, Optional[np.ndarray], Optional[Dict]]:
        """
        Wait for a new image to be captured
        
        Args:
            timeout: Maximum time to wait in seconds
            min_age_diff: Minimum age difference from current image
            
        Returns:
            Tuple of (success, image_array, metadata)
        """
        start_time = time.time()
        current_newest_time = 0
        
        # Get current newest image time
        try:
            image_files = list(self.live_dir.glob("*.jpg"))
            if image_files:
                image_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                current_newest_time = image_files[0].stat().st_mtime
        except Exception:
            pass
        
        while time.time() - start_time < timeout:
            try:
                success, image, metadata = self.get_latest_image(max_age_seconds=timeout)
                if success and metadata:
                    image_time = metadata.get('capture_time', 0)
                    if image_time > current_newest_time + min_age_diff:
                        logger.debug(f"New image detected after {time.time() - start_time:.1f}s")
                        return True, image, metadata
                
                time.sleep(0.5)  # Check every 500ms
                
            except Exception as e:
                logger.error(f"Error waiting for new image: {e}")
                time.sleep(1)
        
        logger.warning(f"Timeout waiting for new image after {timeout}s")
        return False, None, None
    
    def get_image_list(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get list of available images with metadata"""
        try:
            image_files = list(self.live_dir.glob("*.jpg"))
            image_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            image_list = []
            for image_file in image_files[:limit]:
                stat = image_file.stat()
                metadata = self._load_image_metadata(image_file)
                
                image_info = {
                    'filename': image_file.name,
                    'path': str(image_file),
                    'size': stat.st_size,
                    'mtime': stat.st_mtime,
                    'age_seconds': time.time() - stat.st_mtime,
                    'metadata': metadata
                }
                image_list.append(image_info)
            
            return image_list
            
        except Exception as e:
            logger.error(f"Failed to get image list: {e}")
            return []
    
    def get_status(self) -> Dict[str, Any]:
        """Get current provider status"""
        try:
            image_count = len(list(self.live_dir.glob("*.jpg")))
            snapshot_count = len(list(self.snapshots_dir.glob("*.jpg")))
            
            # Get newest image info
            newest_image_info = None
            image_files = list(self.live_dir.glob("*.jpg"))
            if image_files:
                image_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                newest = image_files[0]
                newest_image_info = {
                    'filename': newest.name,
                    'age_seconds': time.time() - newest.stat().st_mtime,
                    'size': newest.stat().st_size
                }
            
            return {
                'capture_dir': str(self.capture_dir),
                'live_images': image_count,
                'snapshots': snapshot_count,
                'cache_size': len(self.image_cache),
                'monitoring_active': self.monitoring_active,
                'consecutive_failures': self.consecutive_failures,
                'total_processed': self.total_images_processed,
                'newest_image': newest_image_info,
                'last_processed': self.last_image_time.isoformat() if self.last_image_time else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get status: {e}")
            return {'error': str(e)}
    
    def cleanup_old_images(self, max_age_hours: float = 24.0):
        """Clean up old images to prevent disk space issues"""
        try:
            cutoff_time = time.time() - (max_age_hours * 3600)
            
            # Clean up live images
            for image_file in self.live_dir.glob("*.jpg"):
                if image_file.stat().st_mtime < cutoff_time:
                    image_file.unlink()
                    
                    # Clean up corresponding metadata
                    metadata_file = self.metadata_dir / f"{image_file.name}.json"
                    if metadata_file.exists():
                        metadata_file.unlink()
                    
                    logger.debug(f"Cleaned up old image: {image_file.name}")
            
            # Clean up old snapshots
            for snapshot_file in self.snapshots_dir.glob("*.jpg"):
                if snapshot_file.stat().st_mtime < cutoff_time:
                    snapshot_file.unlink()
                    logger.debug(f"Cleaned up old snapshot: {snapshot_file.name}")
                    
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

# Compatibility wrapper for existing camera interfaces
class ContainerCameraInterface:
    """
    Drop-in replacement for direct camera access
    Provides familiar camera-like interface using shared volume images
    """
    
    def __init__(self, camera_index=0, **kwargs):
        self.image_provider = SharedVolumeImageProvider()
        self.camera_index = camera_index
        self.is_opened = True
        
        # Start monitoring
        self.image_provider.start_monitoring()
        
        logger.info(f"Container camera interface initialized (index: {camera_index})")
    
    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """OpenCV-compatible read method"""
        success, image, metadata = self.image_provider.get_latest_image()
        return success, image
    
    def capture_array(self) -> Optional[np.ndarray]:
        """Picamera2-compatible capture method"""
        success, image, metadata = self.image_provider.get_latest_image()
        return image if success else None
    
    def isOpened(self) -> bool:
        """Check if camera is available"""
        return self.is_opened
    
    def release(self):
        """Release camera resources"""
        self.image_provider.stop_monitoring()
        self.is_opened = False
    
    def set(self, prop, value):
        """Set camera property (no-op for compatibility)"""
        logger.debug(f"Camera property set ignored: {prop}={value}")
        return True
    
    def get(self, prop):
        """Get camera property (returns defaults)"""
        if prop == cv2.CAP_PROP_FRAME_WIDTH:
            return 4056
        elif prop == cv2.CAP_PROP_FRAME_HEIGHT:
            return 3040
        elif prop == cv2.CAP_PROP_FPS:
            return 30
        return 0