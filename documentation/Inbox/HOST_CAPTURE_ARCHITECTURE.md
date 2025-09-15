# Host-Capture Architecture Documentation

## Overview

This system implements a **host-capture/container-process architecture** to work around OpenCV 4.12.0 compatibility issues with the IMX500 AI camera's V4L2 backend in Docker containers.

### Problem Solved

**Issue**: The OpenCV 4.12.0 camera driver has compatibility issues with the IMX500 AI camera's V4L2 backend, preventing direct video capture within Docker containers.

**Solution**: Use `rpicam-still` on the host system to capture high-quality images (1.4MB, 4056x3040), then process the images in Docker containers via shared volume mounting. This approach maintains proven camera functionality while enabling containerized AI processing.

## Architecture Components

### 1. Host-Side Image Capture (`host-camera-capture.py`)

**Purpose**: Runs on the Raspberry Pi host system to capture images using `rpicam-still`

**Key Features**:

- High-quality image capture (4056x3040, ~1.4MB)
- Configurable capture intervals (default: 1 second)
- Automatic image rotation and cleanup
- Health monitoring and error recovery
- Shared volume coordination with Docker containers

**Location**: `/scripts/host-camera-capture.py`

**Usage**:

```bash
# Run directly
python3 scripts/host-camera-capture.py --capture-dir /mnt/storage/camera_capture

# Run as systemd service
sudo systemctl start host-camera-capture
sudo systemctl enable host-camera-capture  # Auto-start on boot
```

**Configuration**:

```bash
# Test camera functionality
python3 scripts/host-camera-capture.py --test-only

# Check status
python3 scripts/host-camera-capture.py --status

# Custom settings
python3 scripts/host-camera-capture.py \
  --capture-dir /custom/path \
  --interval 2.0 \
  --quality 85 \
  --max-images 200
```

### 2. Shared Volume Image Provider (`shared_volume_image_provider.py`)

**Purpose**: Provides images to container services from the shared volume

**Key Features**:

- Reads images captured by host-side service
- Background monitoring and caching
- OpenCV/Picamera2 compatible interfaces
- Automatic image age validation
- Performance optimized with image cache

**Location**: `/edge_processing/shared_volume_image_provider.py`

**Usage in Container Code**:

```python
from shared_volume_image_provider import SharedVolumeImageProvider

# Initialize provider
provider = SharedVolumeImageProvider()
provider.start_monitoring()

# Get latest image
success, image, metadata = provider.get_latest_image(max_age_seconds=5.0)
if success:
    # Process image
    result = analyze_image(image)

# Cleanup
provider.stop_monitoring()
```

### 3. Container Camera Interface (`ContainerCameraInterface`)

**Purpose**: Drop-in replacement for direct camera access in containers

**Key Features**:

- OpenCV `VideoCapture` compatible API
- Picamera2 compatible methods
- Seamless integration with existing code
- No code changes required for camera access

**Usage**:

```python
from shared_volume_image_provider import ContainerCameraInterface

# Replace cv2.VideoCapture(0) with:
camera = ContainerCameraInterface()

# Use normal OpenCV methods
ret, frame = camera.read()
if ret:
    process_frame(frame)

camera.release()
```

### 4. Image Synchronization Manager (`image-sync-manager.py`)

**Purpose**: Coordinates between host capture and container processing

**Key Features**:

- Monitors host capture service health
- Manages Docker container lifecycle
- Automatic cleanup of old images
- Disk space monitoring and emergency cleanup
- Health recovery and restart capabilities

**Location**: `/scripts/image-sync-manager.py`

**Usage**:

```bash
# Run sync manager
python3 scripts/image-sync-manager.py

# Check status
python3 scripts/image-sync-manager.py --status

# Custom configuration
python3 scripts/image-sync-manager.py \
  --capture-dir /custom/path \
  --check-interval 60 \
  --max-image-age 2.0
```

## Directory Structure

```text
/mnt/storage/camera_capture/          # Shared volume root
├── live/                             # Current images for processing
│   ├── capture_20241212_143022_123.jpg
│   ├── capture_20241212_143023_456.jpg
│   └── ...
├── metadata/                         # Image metadata files
│   ├── capture_20241212_143022_123.jpg.json
│   ├── capture_20241212_143023_456.jpg.json
│   └── ...
├── periodic_snapshots/               # Long-term monitoring snapshots
│   ├── snapshot_20241212_143000.jpg
│   └── ...
└── processed/                        # Archived processed images
    └── ...
```

## Docker Configuration Changes

### Updated `docker-compose.yml`

**Key Changes**:

- Removed direct camera device access (`/dev/video0`, `/dev/video1`)
- Removed VideoCore libraries and privileged mode
- Added shared volume mount for image capture
- Added environment variables for shared volume configuration

```yaml
services:
  traffic-monitor:
    # Removed camera devices
    devices:
      - /dev/ttyACM0:/dev/ttyACM0  # Radar sensor only
      - /dev/gpiomem:/dev/gpiomem  # GPIO access
    
    # Reduced privilege
    privileged: false
    cap_add:
      - NET_ADMIN
      - SYS_TIME
    
    # Shared volume for images
    volumes:
  - /mnt/storage/camera_capture:/mnt/storage/camera_capture
    
    # Configuration
    environment:
      - USE_SHARED_VOLUME_IMAGES=true
      - HOST_CAPTURE_ARCHITECTURE=true
  - CAMERA_CAPTURE_DIR=/mnt/storage/camera_capture
```

## Service Integration

### Updated Vehicle Detection Service

**Changes**:

- Added shared volume image provider integration
- Fallback chain: Shared Volume → Picamera2 → OpenCV → System-level → Mock
- Automatic detection of host-capture architecture
- Seamless integration with existing detection pipeline

### Updated Sky Analysis Service

**Changes**:

- Integrated with shared volume provider
- New `analyze_current_sky()` method for shared volume images
- Backward compatibility with direct image input
- Enhanced error handling and recovery

## System Services

### Host Camera Capture Service

**Systemd Service**: `host-camera-capture.service`

```bash
# Install service
sudo cp scripts/host-camera-capture.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable host-camera-capture
sudo systemctl start host-camera-capture

# Monitor service
sudo systemctl status host-camera-capture
sudo journalctl -u host-camera-capture -f
```

### Image Sync Manager Service

**Optional**: Can be run as a systemd service for automatic management

```bash
# Create service file
sudo tee /etc/systemd/system/image-sync-manager.service << EOF
[Unit]
Description=Image Synchronization Manager
After=network.target docker.service host-camera-capture.service

[Service]
Type=simple
User=pi
ExecStart=/usr/bin/python3 /home/pi/CST_590_Computer_Science_Capstone_Project/scripts/image-sync-manager.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable image-sync-manager
sudo systemctl start image-sync-manager
```

## Testing and Validation

### Test Script: `test_host_capture_architecture.py`

**Comprehensive Testing**:

```bash
# Run all tests
python3 test_host_capture_architecture.py --mode all

# Test specific components
python3 test_host_capture_architecture.py --mode host-service
python3 test_host_capture_architecture.py --mode shared-volume
python3 test_host_capture_architecture.py --mode image-provider
python3 test_host_capture_architecture.py --mode sky-analysis
python3 test_host_capture_architecture.py --mode end-to-end

# Performance testing
python3 test_host_capture_architecture.py --mode performance

# System status
python3 test_host_capture_architecture.py --status
```

**Test Coverage**:

- Host camera capture service functionality
- Shared volume directory structure and permissions
- Image provider operation and caching
- Container camera interface compatibility
- Sky analysis with shared volume images
- Docker integration and volume mounting
- End-to-end processing pipeline
- Performance benchmarking

## Deployment Guide

### 1. Prerequisites

```bash
# Ensure rpicam-still is available
which rpicam-still

# Create storage directory
sudo mkdir -p /mnt/storage/camera_capture
sudo chown pi:pi /mnt/storage/camera_capture
```

### 2. Deploy Host Capture Service

```bash
# Copy and install service
sudo cp scripts/host-camera-capture.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable host-camera-capture

# Test camera capture
python3 scripts/host-camera-capture.py --test-only

# Start service
sudo systemctl start host-camera-capture
```

### 3. Update Docker Configuration

```bash
# Update docker-compose.yml with new configuration
docker-compose down
docker-compose up -d

# Verify container can access shared volume
docker exec traffic-monitoring-edge ls -la /mnt/storage/camera_capture/
```

### 4. Validate System

```bash
# Run comprehensive tests
python3 test_host_capture_architecture.py --mode all

# Monitor for a few minutes
python3 scripts/image-sync-manager.py --status
```

## Troubleshooting

### Common Issues

### 1. No Images Being Captured

```bash
# Check service status
sudo systemctl status host-camera-capture

# Check camera access
rpicam-still -o test.jpg --immediate

# Check permissions
ls -la /mnt/storage/camera_capture/
```

### 2. Container Cannot Access Images

```bash
# Check volume mount
docker inspect traffic-monitoring-edge | grep camera_capture

# Check directory permissions
docker exec traffic-monitoring-edge ls -la /mnt/storage/camera_capture/
```

### 3. Old Images Accumulating

```bash
# Check disk space
df -h /mnt/storage/

# Run manual cleanup
python3 scripts/image-sync-manager.py --status
```

#### 4. Performance Issues

```bash
# Run performance test
python3 test_host_capture_architecture.py --mode performance

# Check system resources
top
iostat -x 1
```

### Log Files

**Host Capture Service**:

```bash
sudo journalctl -u host-camera-capture -f
tail -f /var/log/host-camera-capture.log
```

**Image Sync Manager**:

```bash
tail -f /var/log/image-sync-manager.log
```

**Container Logs**:

```bash
docker logs -f traffic-monitoring-edge
```

## Performance Characteristics

### Typical Performance Metrics

- **Image Capture**: 1-3 seconds per image (including write to disk)
- **Image Retrieval**: <100ms average from shared volume
- **Sky Analysis**: 200-500ms per image
- **Total Pipeline**: <1 second for recent images
- **Disk Usage**: ~1.4MB per image, auto-cleanup after 4 hours
- **Memory Usage**: <100MB for image provider cache

### Optimization Tips

1. **Capture Interval**: Adjust based on processing speed requirements
2. **Image Quality**: Balance quality vs. file size (default: 95%)
3. **Cache Size**: Increase for better performance with multiple consumers
4. **Cleanup Frequency**: Adjust based on disk space and retention needs

## Migration from Direct Camera Access

### Code Changes Required

**Before (Direct Camera)**:

```python
camera = cv2.VideoCapture(0)
ret, frame = camera.read()
```

**After (Shared Volume)**:

```python
from shared_volume_image_provider import ContainerCameraInterface
camera = ContainerCameraInterface()
ret, frame = camera.read()  # Same API!
```

**Sky Analysis Before**:

```python
# Capture image directly
ret, frame = camera.read()
result = sky_analyzer.analyze_sky_condition(frame)
```

**Sky Analysis After**:

```python
# Use shared volume
result = sky_analyzer.analyze_current_sky(max_age_seconds=5.0)
```

### Deployment Steps

1. **Update Code**: Integrate shared volume image provider
2. **Deploy Host Service**: Install and start host camera capture
3. **Update Docker Config**: Remove camera devices, add shared volume
4. **Test System**: Validate end-to-end functionality
5. **Monitor**: Ensure stable operation and performance

## Benefits of Host-Capture Architecture

1. **Reliability**: Eliminates OpenCV/IMX500 compatibility issues
2. **Performance**: High-quality images with proven camera tools
3. **Flexibility**: Easy to switch between direct and shared volume modes
4. **Maintenance**: Host service can be updated independently
5. **Debugging**: Clear separation between capture and processing
6. **Scalability**: Multiple containers can share the same image stream

## Limitations and Considerations

1. **Latency**: Slight additional latency due to file system operations
2. **Disk I/O**: Increased disk usage for image storage
3. **Synchronization**: Images are not perfectly synchronized with processing
4. **Complexity**: Additional service to manage and monitor
5. **Storage**: Requires sufficient disk space for image buffering

This architecture provides a robust solution for IMX500 camera integration in containerized environments while maintaining high image quality and system reliability.
