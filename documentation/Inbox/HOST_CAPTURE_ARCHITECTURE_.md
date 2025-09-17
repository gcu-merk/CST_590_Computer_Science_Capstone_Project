# Host-Capture Container-Process Architecture

## Overview

This document describes the **Host-Capture/Container-Process Architecture** implemented to resolve OpenCV 4.12.0 compatibility issues with the Sony IMX500 AI camera in Docker containers. This architecture separates image capture (host-side) from image processing (container-side) via shared volume mounting.

## Table of Contents

- [Problem Statement](#problem-statement)
- [Architecture Overview](#architecture-overview)
- [Components](#components)
- [Data Flow](#data-flow)
- [Performance Characteristics](#performance-characteristics)
- [Deployment](#deployment)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

## Problem Statement

### Original Issue

The OpenCV 4.12.0 camera driver has compatibility issues with the Sony IMX500 AI camera's V4L2 backend, preventing direct video capture within Docker containers. This manifested as:

- **Camera Access Failures**: `cv2.VideoCapture(0)` fails in Docker containers
- **Device Permission Issues**: Camera devices not accessible in containerized environment
- **Driver Conflicts**: IMX500 AI camera requires specific Raspberry Pi libraries
- **Performance Degradation**: Workarounds resulted in poor image quality

### Solution Approach

Implement a **host-capture/container-process** architecture where:

1. **Host System** captures images using proven `rpicam-still` tool
2. **Shared Volume** transfers images between host and container
3. **Container Services** process images from shared volume
4. **Coordination Layer** manages handoff and cleanup

## Architecture Overview

```text
┌─────────────────────────────────────────────────────────────────┐
│                    Raspberry Pi Host System                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌──────────────────┐    ┌────────────────┐ │
│  │ IMX500      │───▶│ Host Camera      │───▶│ Shared Volume  │ │
│  │ AI Camera   │    │ Capture Service  │    │ /mnt/storage/  │ │
│  └─────────────┘    └──────────────────┘    │ camera_capture │ │
│                                              └────────────────┘ │
│                           │                           ▲         │
│                           ▼                           │         │
│                  ┌─────────────────┐         ┌──────────────┐   │
│                  │ Image Sync      │         │ Systemd      │   │
│                  │ Manager         │         │ Services     │   │
│                  └─────────────────┘         └──────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Docker Container                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌────────────────┐    ┌──────────────────┐    ┌─────────────┐ │
│  │ Shared Volume  │───▶│ Image Provider   │───▶│ Processing  │ │
│  │ Mount          │    │ Service          │    │ Services    │ │
│  │ /mnt/storage/data/     │    └──────────────────┘    └─────────────┘ │
│  │ camera_capture │              │                     ▲       │
│  └────────────────┘              ▼                     │       │
│                           ┌──────────────┐             │       │
│                           │ Image Cache  │─────────────┘       │
│                           │ Management   │                     │
│                           └──────────────┘                     │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Processing Services:                                    │   │
│  │ • Vehicle Detection Service                             │   │
│  │ • Sky Analysis Service                                  │   │
│  │ • Edge API Gateway                                      │   │
│  │ • System Health Monitor                                 │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Host Camera Capture Service

**Location**: `scripts/host-camera-capture.py`

**Purpose**: Captures high-quality images on the Raspberry Pi host system using `rpicam-still`

**Key Features**:

- **High-Quality Capture**: 4056x3040 resolution, JPEG quality 95
- **Reliable Operation**: Uses proven `rpicam-still` tool instead of OpenCV
- **Automatic Management**: Configurable capture intervals and cleanup
- **Health Monitoring**: Error detection and automatic recovery
- **Systemd Integration**: Runs as system service with auto-restart

**Configuration Options**:

```bash
# Basic usage
python3 scripts/host-camera-capture.py

# Custom configuration
python3 scripts/host-camera-capture.py \
  --capture-dir /mnt/storage/camera_capture \
  --interval 1.0 \
  --width 4056 \
  --height 3040 \
  --quality 95 \
  --max-images 100
```

### 2. Shared Volume Image Provider

**Location**: `edge_processing/shared_volume_image_provider.py`

**Purpose**: Provides containerized services with access to host-captured images

**Key Features**:

- **Background Monitoring**: Continuously watches for new images
- **Performance Caching**: Maintains in-memory cache of recent images
- **Age Validation**: Ensures images are recent enough for processing
- **Compatible Interfaces**: OpenCV and Picamera2 compatible APIs
- **Error Handling**: Graceful degradation and fallback mechanisms

**API Examples**:

```python
# Initialize provider
provider = SharedVolumeImageProvider()
provider.start_monitoring()

# Get latest image
success, image, metadata = provider.get_latest_image(max_age_seconds=5.0)

# Check provider status
status = provider.get_status()
```

### 3. Container Camera Interface

**Location**: `edge_processing/shared_volume_image_provider.py`

**Purpose**: Drop-in replacement for direct camera access in containers

**Key Features**:

- **OpenCV Compatibility**: `cv2.VideoCapture`-like interface
- **Picamera2 Compatibility**: `capture_array()` method support
- **Seamless Integration**: No code changes required for existing services
- **Transparent Operation**: Automatically uses shared volume images

**Usage Example**:

```python
# Replace cv2.VideoCapture(0) with:
from shared_volume_image_provider import ContainerCameraInterface

camera = ContainerCameraInterface()
ret, frame = camera.read()  # Same API as OpenCV
camera.release()
```

### 4. Image Synchronization Manager

**Location**: `scripts/image-sync-manager.py`

**Purpose**: Coordinates between host capture and container processing

**Key Features**:

- **Service Health Monitoring**: Monitors host capture service status
- **Container Management**: Tracks Docker container health
- **Automatic Recovery**: Restarts failed services
- **Disk Space Management**: Automatic cleanup of old images
- **Performance Monitoring**: Tracks system metrics and performance

**Usage**:

```bash
# Run sync manager
python3 scripts/image-sync-manager.py

# Check status
python3 scripts/image-sync-manager.py --status

# Custom configuration
python3 scripts/image-sync-manager.py \
  --check-interval 60 \
  --max-image-age 2.0 \
  --cleanup-interval 1.0
```

## Data Flow

### 1. Image Capture Flow

```text
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│ IMX500      │    │ rpicam-still │    │ Shared Volume   │
│ Camera      │───▶│ Command      │───▶│ File System     │
│             │    │              │    │                 │
│ 4056x3040   │    │ --immediate  │    │ /live/*.jpg     │
│ Hardware    │    │ --quality 95 │    │ /metadata/*.json│
└─────────────┘    └──────────────┘    └─────────────────┘
```

**Process Steps**:

1. **Trigger**: Host capture service timer triggers image capture
2. **Execute**: `rpicam-still` command captures image to temporary file
3. **Validate**: Check image file size and quality
4. **Atomic Move**: Move to shared volume with timestamp filename
5. **Metadata**: Create JSON metadata file with capture details
6. **Cleanup**: Remove old images based on retention policy

### 2. Image Processing Flow

```text
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Background      │    │ Processing       │    │ Service         │
│ Monitor         │───▶│ Request          │───▶│ Response        │
│                 │    │                  │    │                 │
│ File Discovery  │    │ get_latest_image │    │ Analysis Result │
│ Cache Update    │    │ Age Validation   │    │ Detection Data  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

**Process Steps**:

1. **Monitor**: Background thread scans shared volume for new images
2. **Cache**: Load recent images into memory cache for fast access
3. **Request**: Processing service requests latest image
4. **Validate**: Check image age against maximum age threshold
5. **Serve**: Return image data and metadata to processing service
6. **Process**: Service performs analysis (vehicle detection, sky analysis, etc.)

### 3. Coordination Flow

```text
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Systemd         │    │ Image Sync       │    │ Docker          │
│ Services        │───▶│ Manager          │───▶│ Container       │
│                 │    │                  │    │                 │
│ host-camera-    │    │ Health Monitor   │    │ traffic-        │
│ capture.service │    │ Auto Recovery    │    │ monitoring-edge │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

**Process Steps**:

1. **Monitor**: Sync manager monitors service and container health
2. **Detect**: Identify service failures or performance issues
3. **Recover**: Restart failed services automatically
4. **Cleanup**: Manage disk space and remove old images
5. **Report**: Log status and performance metrics

## Performance Characteristics

### Timing Metrics

| **Operation** | **Typical Time** | **Maximum Time** | **Notes** |
|---------------|------------------|------------------|-----------|
| Image Capture | 1-3 seconds | 5 seconds | Host `rpicam-still` execution |
| File Detection | <100ms | 500ms | Container monitoring discovery |
| Cache Hit | <50ms | 100ms | In-memory cache access |
| Disk Load | 100-300ms | 1 second | Load image from shared volume |
| Total Pipeline | <1 second | 3 seconds | For images <5 seconds old |

### Throughput Metrics

- **Capture Rate**: 1 image/second (configurable)
- **Processing Rate**: Limited by analysis complexity, not handoff
- **Cache Hit Rate**: >90% for active processing
- **Storage Efficiency**: ~1.4MB per image, auto-cleanup

### Resource Usage

- **Host CPU**: 5-10% during capture
- **Container CPU**: <5% for image provider
- **Memory**: ~100MB for image cache (10 images)
- **Disk I/O**: Sequential writes, minimal fragmentation
- **Network**: None (local file system only)

## Deployment

### Prerequisites

```bash
# Verify rpicam-still availability
which rpicam-still

# Create shared volume directory
sudo mkdir -p /mnt/storage/camera_capture
sudo chown pi:pi /mnt/storage/camera_capture

# Test camera access
rpicam-still -o test.jpg --immediate
```

### Installation Steps

#### 1. Deploy Host Capture Service

```bash
# Copy service definition
sudo cp scripts/host-camera-capture.service /etc/systemd/system/

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable host-camera-capture

# Test camera functionality
python3 scripts/host-camera-capture.py --test-only

# Start service
sudo systemctl start host-camera-capture

# Verify service status
sudo systemctl status host-camera-capture
```

#### 2. Update Docker Configuration

The `docker-compose.yml` has been updated with the following key changes:

```yaml
services:
  traffic-monitor:
    # Removed direct camera device access
    devices:
      - /dev/ttyACM0:/dev/ttyACM0  # Radar only
      - /dev/gpiomem:/dev/gpiomem  # GPIO only
    
    # Reduced privileges
    privileged: false
    cap_add:
      - NET_ADMIN
      - SYS_TIME
    
    # Added shared volume mount
    volumes:
  - /mnt/storage/camera_capture:/mnt/storage/camera_capture
    
    # Added configuration
    environment:
      - USE_SHARED_VOLUME_IMAGES=true
      - HOST_CAPTURE_ARCHITECTURE=true
  - CAMERA_CAPTURE_DIR=/mnt/storage/camera_capture
```

Deploy updated configuration:

```bash
# Stop existing container
docker-compose down

# Deploy updated configuration
docker-compose up -d

# Verify container access to shared volume
docker exec $(docker ps -q --filter "label=com.docker.compose.service=traffic-monitor" | head -1) ls -la /mnt/storage/camera_capture/
```

#### 3. Optional: Deploy Image Sync Manager

```bash
# Run sync manager in background
nohup python3 scripts/image-sync-manager.py > /var/log/image-sync-manager.log 2>&1 &

# Or install as systemd service
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

## Monitoring

### Service Health Monitoring

#### Host Camera Capture Service

```bash
# Check service status
sudo systemctl status host-camera-capture

# View service logs
sudo journalctl -u host-camera-capture -f

# Check image creation
ls -la /mnt/storage/camera_capture/live/

# Service performance
python3 scripts/host-camera-capture.py --status
```

#### Docker Container Health

```bash
# Check container status
docker ps | grep traffic-monitoring

# Container logs
docker compose logs -f traffic-monitor

# Verify shared volume access
docker exec $(docker ps -q --filter "label=com.docker.compose.service=traffic-monitor" | head -1) ls -la /mnt/storage/camera_capture/live/
```

#### Image Sync Manager

```bash
# Check sync manager status
python3 scripts/image-sync-manager.py --status

# View sync manager logs
tail -f /var/log/image-sync-manager.log

# System resource usage
df -h /mnt/storage/
iostat -x 1
```

### Performance Monitoring

#### Key Metrics to Track

1. **Image Capture Rate**

   ```bash
   # Count images in last minute
   find /mnt/storage/camera_capture/live/ -name "*.jpg" -newermt "1 minute ago" | wc -l
   ```

2. **Image Age Distribution**

   ```bash
   # Check age of newest image
   newest=$(ls -t /mnt/storage/camera_capture/live/*.jpg | head -1)
   echo "Age: $(($(date +%s) - $(stat -c %Y "$newest"))) seconds"
   ```

3. **Disk Usage**

   ```bash
   # Check shared volume disk usage
   du -sh /mnt/storage/camera_capture/*
   df -h /mnt/storage/
   ```

4. **Container Processing Performance**

   ```bash
   # Test end-to-end processing
   python3 test_host_capture_architecture.py --mode performance
   ```

### Automated Health Checks

The system includes several automated health checks:

- **Service Monitoring**: Systemd monitors host capture service
- **Container Health**: Docker health checks for container
- **Image Freshness**: Automatic detection of stale images
- **Disk Space**: Emergency cleanup when space is low
- **Error Recovery**: Automatic restart of failed services

## Troubleshooting

### Common Issues and Solutions

#### 1. No Images Being Captured

**Symptoms**: Empty `/mnt/storage/camera_capture/live/` directory

**Diagnosis**:

```bash
# Check service status
sudo systemctl status host-camera-capture

# Check camera access
rpicam-still -o test.jpg --immediate

# Check permissions
ls -la /mnt/storage/camera_capture/
```

**Solutions**:

- Restart capture service: `sudo systemctl restart host-camera-capture`
- Check camera hardware connection
- Verify directory permissions: `sudo chown -R pi:pi /mnt/storage/camera_capture`

#### 2. Container Cannot Access Images

**Symptoms**: Container services report "No images found" errors

**Diagnosis**:

```bash
# Check volume mount
docker inspect $(docker ps -q --filter "label=com.docker.compose.service=traffic-monitor" | head -1) | grep camera_capture

# Check container directory
docker exec $(docker ps -q --filter "label=com.docker.compose.service=traffic-monitor" | head -1) ls -la /app/data/camera_capture/live/

# Check file permissions
ls -la /mnt/storage/camera_capture/live/
```

**Solutions**:

- Restart container: `docker-compose restart`
- Fix volume permissions: `sudo chown -R pi:pi /mnt/storage/camera_capture`
- Verify docker-compose.yml volume mount configuration

#### 3. Images Too Old

**Symptoms**: Processing services report "Image too old" errors

**Diagnosis**:

```bash
# Check newest image age
newest=$(ls -t /mnt/storage/camera_capture/live/*.jpg | head -1)
age=$(($(date +%s) - $(stat -c %Y "$newest")))
echo "Newest image age: $age seconds"

# Check capture service activity
sudo journalctl -u host-camera-capture --since "5 minutes ago"
```

**Solutions**:

- Restart capture service if not creating new images
- Increase `max_age_seconds` in processing services if needed
- Check system clock synchronization

#### 4. Disk Space Issues

**Symptoms**: "No space left on device" errors or excessive disk usage

**Diagnosis**:

```bash
# Check disk usage
df -h /mnt/storage/
du -sh /mnt/storage/camera_capture/*

# Count images
find /mnt/storage/camera_capture/ -name "*.jpg" | wc -l
```

**Solutions**:

- Run manual cleanup: `python3 scripts/image-sync-manager.py --status`
- Reduce image retention time in configuration
- Increase cleanup frequency
- Move to larger storage device

#### 5. Performance Issues

**Symptoms**: Slow image processing or high latency

**Diagnosis**:

```bash
# Run performance test
python3 test_host_capture_architecture.py --mode performance

# Check system resources
top
iostat -x 1
free -h
```

**Solutions**:

- Increase image cache size in provider configuration
- Reduce image capture quality if acceptable
- Optimize cleanup intervals
- Check for disk I/O bottlenecks

### Log Analysis

#### Important Log Locations

- **Host Capture Service**: `/var/log/host-camera-capture.log` and `journalctl -u host-camera-capture`
- **Image Sync Manager**: `/var/log/image-sync-manager.log`
- **Container Logs**: `docker compose logs traffic-monitor` (or `docker logs <container-id>`)
- **System Logs**: `/var/log/syslog` and `dmesg`

#### Key Log Messages

**Normal Operation**:

```text
INFO - Successfully captured frame using rpicam-still
INFO - Sky analyzer initialized with shared volume image provider
INFO - Retrieved image via shared volume: (3040, 4056, 3)
```

**Warning Signs**:

```text
WARNING - Latest image too old: 15.2s > 5.0s
WARNING - No recent images detected (newest: 65.3s old)
WARNING - Low disk space: 8.5% free
```

**Error Conditions**:

```text
ERROR - rpicam-still failed: Device not found
ERROR - Failed to load image from shared volume
ERROR - Too many consecutive capture errors - restarting camera
```

### Recovery Procedures

#### Service Recovery

```bash
# Full service restart
sudo systemctl restart host-camera-capture
docker-compose restart

# Clean restart with cache clear
sudo systemctl stop host-camera-capture
rm -f /mnt/storage/camera_capture/live/*
sudo systemctl start host-camera-capture
```

#### Emergency Cleanup

```bash
# Emergency disk space cleanup
find /mnt/storage/camera_capture/live/ -name "*.jpg" -mtime +1 -delete
find /mnt/storage/camera_capture/metadata/ -name "*.json" -mtime +1 -delete
find /mnt/storage/camera_capture/processed/ -name "*.jpg" -mtime +1 -delete
```

This architecture provides a robust, high-performance solution for camera integration in containerized environments while maintaining reliability and ease of maintenance.
