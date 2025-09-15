# Host-Capture Architecture API Reference

## Overview

This document provides a comprehensive API reference for the **Host-Capture/Container-Process Architecture** components. These APIs enable containerized services to access host-captured images while maintaining compatibility with existing OpenCV and Picamera2 interfaces.

## Table of Contents

- [SharedVolumeImageProvider](#sharedvolumeimageprovider)
- [ContainerCameraInterface](#containercamerainterface)
- [HostCameraCaptureService](#hostcameracaptureservice)
- [ImageSyncManager](#imagesyncmanager)
- [Configuration Classes](#configuration-classes)
- [Error Handling](#error-handling)
- [Usage Examples](#usage-examples)

## SharedVolumeImageProvider

The core component that provides containerized services with access to host-captured images.

### SharedVolumeImageProvider Class Definition

```python
class SharedVolumeImageProvider:
    """
    Provides access to images captured by the host system via shared volume.
    
    This class monitors a shared volume for new images captured by the host
    camera service and provides them to containerized processing services.
    """
```

### SharedVolumeImageProvider Constructor

```python
def __init__(
    self,
    shared_volume_dir: str = "/mnt/storage/camera_capture",
    cache_size: int = 10,
    background_monitoring: bool = True,
    monitor_interval: float = 0.1,
    max_age_seconds: float = 5.0
):
    """
    Initialize the SharedVolumeImageProvider.
    
    Args:
        shared_volume_dir: Path to shared volume directory
        cache_size: Number of images to keep in memory cache
        background_monitoring: Enable background image monitoring
        monitor_interval: Seconds between monitoring checks
        max_age_seconds: Maximum acceptable image age in seconds
    """
```

### HostCameraCaptureService Methods

#### get_latest_image()

```python
def get_latest_image(
    self,
    max_age_seconds: Optional[float] = None
) -> Tuple[bool, Optional[np.ndarray], Optional[Dict[str, Any]]]:
    """
    Get the latest captured image.
    
    Args:
        max_age_seconds: Override default maximum age for this request
        
    Returns:
        Tuple of:
        - success: Boolean indicating if image was retrieved
        - image: NumPy array in BGR format (OpenCV compatible) or None
        - metadata: Dictionary with capture information or None
        
    Example:
        >>> provider = SharedVolumeImageProvider()
        >>> success, image, metadata = provider.get_latest_image(max_age_seconds=3.0)
        >>> if success:
        >>>     print(f"Image shape: {image.shape}")
        >>>     print(f"Captured at: {metadata['timestamp']}")
    """
```

#### start_monitoring() (ImageSyncManager)

```python
def start_monitoring(self) -> None:
    """
    Start background monitoring for new images.
    
    This method starts a background thread that continuously monitors
    the shared volume for new images and updates the internal cache.
    
    Example:
        >>> provider = SharedVolumeImageProvider()
        >>> provider.start_monitoring()
        >>> # Provider now automatically updates cache
    """
```

#### stop_monitoring()

```python
def stop_monitoring(self) -> None:
    """
    Stop background monitoring.
    
    Gracefully stops the background monitoring thread and cleans up resources.
    
    Example:
        >>> provider.stop_monitoring()
    """
```

#### get_status()

```python
def get_status(self) -> Dict[str, Any]:
    """
    Get current provider status and statistics.
    
    Returns:
        Dictionary containing:
        - monitoring_active: Boolean indicating if monitoring is running
        - cache_size: Current number of cached images
        - latest_image_age: Age of newest image in seconds
        - total_images_loaded: Total images loaded since start
        - cache_hit_rate: Percentage of requests served from cache
        - last_update: Timestamp of last cache update
        
    Example:
        >>> status = provider.get_status()
        >>> print(f"Cache hit rate: {status['cache_hit_rate']:.1f}%")
        >>> print(f"Latest image age: {status['latest_image_age']:.1f}s")
    """
```

### Advanced Methods

#### force_refresh()

```python
def force_refresh(self) -> bool:
    """
    Force immediate refresh of image cache.
    
    Returns:
        True if new images were found and loaded, False otherwise
        
    Example:
        >>> if provider.force_refresh():
        >>>     print("Cache updated with new images")
    """
```

#### get_cached_images()

```python
def get_cached_images(self) -> List[Tuple[str, np.ndarray, Dict[str, Any]]]:
    """
    Get all currently cached images.
    
    Returns:
        List of tuples containing (filename, image_array, metadata)
        
    Example:
        >>> cached = provider.get_cached_images()
        >>> for filename, image, metadata in cached:
        >>>     print(f"Cached: {filename}, Age: {metadata['age']:.1f}s")
    """
```

## ContainerCameraInterface

Drop-in replacement for OpenCV VideoCapture and Picamera2 interfaces.

### ContainerCameraInterface Class Definition

```python
class ContainerCameraInterface:
    """
    Camera interface that provides OpenCV-compatible API using shared volume images.
    
    This class acts as a drop-in replacement for cv2.VideoCapture in containerized
    environments where direct camera access is not available.
    """
```

### ContainerCameraInterface Constructor

```python
def __init__(
    self,
    shared_volume_dir: str = "/mnt/storage/camera_capture",
    max_age_seconds: float = 5.0
):
    """
    Initialize container camera interface.
    
    Args:
        shared_volume_dir: Path to shared volume directory
        max_age_seconds: Maximum acceptable image age
    """
```

### OpenCV-Compatible Methods

#### read()

```python
def read(self) -> Tuple[bool, Optional[np.ndarray]]:
    """
    Read a frame from the camera (OpenCV VideoCapture compatible).
    
    Returns:
        Tuple of (success, frame) where:
        - success: Boolean indicating if frame was captured
        - frame: NumPy array in BGR format or None
        
    Example:
        >>> camera = ContainerCameraInterface()
        >>> ret, frame = camera.read()  # Same as cv2.VideoCapture
        >>> if ret:
        >>>     cv2.imshow("Frame", frame)
    """
```

#### isOpened()

```python
def isOpened(self) -> bool:
    """
    Check if camera connection is available (OpenCV compatible).
    
    Returns:
        True if recent images are available, False otherwise
        
    Example:
        >>> camera = ContainerCameraInterface()
        >>> if camera.isOpened():
        >>>     ret, frame = camera.read()
    """
```

#### release()

```python
def release(self) -> None:
    """
    Release camera resources (OpenCV compatible).
    
    Example:
        >>> camera = ContainerCameraInterface()
        >>> # ... use camera ...
        >>> camera.release()
    """
```

### Picamera2-Compatible Methods

#### capture_array()

```python
def capture_array(self, name: str = "main") -> Optional[np.ndarray]:
    """
    Capture image as NumPy array (Picamera2 compatible).
    
    Args:
        name: Stream name (ignored, for compatibility)
        
    Returns:
        NumPy array in RGB format or None
        
    Example:
        >>> camera = ContainerCameraInterface()
        >>> rgb_array = camera.capture_array()  # Same as Picamera2
        >>> if rgb_array is not None:
        >>>     print(f"Captured RGB image: {rgb_array.shape}")
    """
```

#### start()

```python
def start(self) -> None:
    """
    Start camera (Picamera2 compatible).
    
    Example:
        >>> camera = ContainerCameraInterface()
        >>> camera.start()
        >>> rgb_array = camera.capture_array()
    """
```

#### stop()

```python
def stop(self) -> None:
    """
    Stop camera (Picamera2 compatible).
    
    Example:
        >>> camera.stop()
    """
```

## HostCameraCaptureService

Host-side service that captures images using rpicam-still.

### HostCameraCaptureService Class Definition

```python
class HostCameraCaptureService:
    """
    Host-side camera capture service using rpicam-still.
    
    This service runs on the Raspberry Pi host system and captures
    high-quality images using the native camera tools.
    """
```

### HostCameraCaptureService Constructor

```python
def __init__(
    self,
    capture_dir: str = "/mnt/storage/camera_capture",
    interval: float = 1.0,
    width: int = 4056,
    height: int = 3040,
    quality: int = 95,
    max_images: int = 100
):
    """
    Initialize host camera capture service.
    
    Args:
        capture_dir: Directory to store captured images
        interval: Capture interval in seconds
        width: Image width in pixels
        height: Image height in pixels  
        quality: JPEG quality (1-100)
        max_images: Maximum images to retain
    """
```

### HostCameraCaptureService Core Methods

#### start_capture()

```python
def start_capture(self) -> None:
    """
    Start continuous image capture.
    
    Begins the capture loop that periodically takes images and
    saves them to the shared volume.
    
    Example:
        >>> service = HostCameraCaptureService()
        >>> service.start_capture()  # Runs until stopped
    """
```

#### capture_single_image()

```python
def capture_single_image(self) -> bool:
    """
    Capture a single image immediately.
    
    Returns:
        True if image was successfully captured, False otherwise
        
    Example:
        >>> service = HostCameraCaptureService()
        >>> if service.capture_single_image():
        >>>     print("Image captured successfully")
    """
```

#### get_capture_status()

```python
def get_capture_status(self) -> Dict[str, Any]:
    """
    Get current capture service status.
    
    Returns:
        Dictionary containing:
        - is_running: Boolean indicating if capture is active
        - images_captured: Total number of images captured
        - last_capture_time: Timestamp of last successful capture
        - error_count: Number of capture errors
        - disk_usage: Current disk usage information
        
    Example:
        >>> status = service.get_capture_status()
        >>> print(f"Images captured: {status['images_captured']}")
        >>> print(f"Error rate: {status['error_count']}")
    """
```

## ImageSyncManager

Coordination service that manages the handoff between host and container.

### Class Definition

```python
class ImageSyncManager:
    """
    Manages synchronization between host capture and container processing.
    
    This service monitors both host capture and container health,
    ensuring reliable image handoff and automatic recovery.
    """
```

### Constructor

```python
def __init__(
    self,
    shared_volume_dir: str = "/mnt/storage/camera_capture",
    check_interval: float = 60.0,
    max_image_age: float = 10.0,
    cleanup_interval: float = 300.0
):
    """
    Initialize image synchronization manager.
    
    Args:
        shared_volume_dir: Path to shared volume directory
        check_interval: Health check interval in seconds
        max_image_age: Maximum acceptable image age for alerts
        cleanup_interval: Cleanup interval in seconds
    """
```

### Core Methods

#### start_monitoring()

```python
def start_monitoring(self) -> None:
    """
    Start comprehensive system monitoring.
    
    Begins monitoring of:
    - Host capture service health
    - Container health and accessibility
    - Image freshness and availability
    - Disk space and cleanup needs
    
    Example:
        >>> manager = ImageSyncManager()
        >>> manager.start_monitoring()  # Runs until stopped
    """
```

#### get_system_status()

```python
def get_system_status(self) -> Dict[str, Any]:
    """
    Get comprehensive system status report.
    
    Returns:
        Dictionary containing:
        - host_capture_healthy: Boolean for host service health
        - container_accessible: Boolean for container accessibility
        - latest_image_age: Age of newest image in seconds
        - disk_usage_percent: Disk usage percentage
        - images_in_queue: Number of unprocessed images
        - error_alerts: List of current error conditions
        
    Example:
        >>> status = manager.get_system_status()
        >>> if not status['host_capture_healthy']:
        >>>     print("Host capture service needs attention")
    """
```

#### trigger_cleanup()

```python
def trigger_cleanup(self) -> Dict[str, int]:
    """
    Manually trigger cleanup of old images.
    
    Returns:
        Dictionary with cleanup statistics:
        - images_removed: Number of images deleted
        - metadata_removed: Number of metadata files deleted
        - space_freed_mb: Disk space freed in megabytes
        
    Example:
        >>> cleanup_stats = manager.trigger_cleanup()
        >>> print(f"Freed {cleanup_stats['space_freed_mb']} MB")
    """
```

## Configuration Classes

### ImageProviderConfig

```python
@dataclass
class ImageProviderConfig:
    """Configuration for SharedVolumeImageProvider."""
    shared_volume_dir: str = "/mnt/storage/camera_capture"
    cache_size: int = 10
    background_monitoring: bool = True
    monitor_interval: float = 0.1
    max_age_seconds: float = 5.0
    enable_performance_monitoring: bool = False
```

### CaptureServiceConfig

```python
@dataclass
class CaptureServiceConfig:
    """Configuration for HostCameraCaptureService."""
    capture_dir: str = "/mnt/storage/camera_capture"
    interval: float = 1.0
    width: int = 4056
    height: int = 3040
    quality: int = 95
    max_images: int = 100
    enable_metadata: bool = True
```

## Error Handling

### Exception Classes

#### SharedVolumeError

```python
class SharedVolumeError(Exception):
    """Base exception for shared volume operations."""
    pass

class ImageNotFoundError(SharedVolumeError):
    """Raised when no valid images are found."""
    pass

class ImageTooOldError(SharedVolumeError):
    """Raised when available images exceed maximum age."""
    pass

class CacheError(SharedVolumeError):
    """Raised when image cache operations fail."""
    pass
```

#### CaptureServiceError

```python
class CaptureServiceError(Exception):
    """Base exception for capture service operations."""
    pass

class CameraNotAvailableError(CaptureServiceError):
    """Raised when camera hardware is not accessible."""
    pass

class CaptureFailedError(CaptureServiceError):
    """Raised when image capture fails."""
    pass
```

### Error Handling Patterns

#### Graceful Degradation

```python
def get_latest_image_with_fallback(provider, max_retries=3):
    """Example of graceful error handling with fallback."""
    for attempt in range(max_retries):
        try:
            success, image, metadata = provider.get_latest_image()
            if success:
                return image, metadata
        except ImageTooOldError:
            # Wait for newer image
            time.sleep(0.5)
        except ImageNotFoundError:
            # Check if capture service is running
            if attempt == max_retries - 1:
                raise
            time.sleep(1.0)
    
    raise CaptureServiceError("Failed to get image after retries")
```

#### Health Check Integration

```python
def check_system_health():
    """Example health check implementation."""
    try:
        provider = SharedVolumeImageProvider()
        success, _, metadata = provider.get_latest_image(max_age_seconds=10.0)
        
        return {
            "status": "healthy" if success else "degraded",
            "latest_image_age": metadata.get("age", float("inf")) if metadata else None,
            "provider_status": provider.get_status()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
```

## Usage Examples

### Basic Integration

```python
# Replace direct camera access with shared volume provider
# OLD: camera = cv2.VideoCapture(0)
# NEW:
from shared_volume_image_provider import ContainerCameraInterface

camera = ContainerCameraInterface()

# Same API as OpenCV
ret, frame = camera.read()
if ret:
    # Process frame normally
    processed = cv2.GaussianBlur(frame, (15, 15), 0)
    cv2.imshow("Processed", processed)

camera.release()
```

### Service Integration

```python
class VehicleDetectionService:
    def __init__(self):
        self.camera = ContainerCameraInterface(max_age_seconds=3.0)
        
    def detect_vehicles(self):
        ret, frame = self.camera.read()
        if not ret:
            return []
            
        # Standard OpenCV processing
        vehicles = self._detect_vehicles_in_frame(frame)
        return vehicles
```

### Performance Monitoring

```python
class MonitoredImageProvider:
    def __init__(self):
        self.provider = SharedVolumeImageProvider(
            cache_size=15,
            enable_performance_monitoring=True
        )
        self.provider.start_monitoring()
        
    def get_performance_metrics(self):
        status = self.provider.get_status()
        return {
            "cache_hit_rate": status["cache_hit_rate"],
            "average_age": status["average_image_age"],
            "throughput": status["images_per_second"]
        }
```

This API reference provides complete documentation for integrating the host-capture architecture into existing and new containerized services.
