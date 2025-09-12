# Host-Capture Container-Process Deployment Guide

## Quick Start Deployment

This guide provides step-by-step instructions for deploying the **Host-Capture/Container-Process Architecture** to resolve IMX500 camera compatibility issues in Docker environments.

## Prerequisites

### System Requirements

- **Hardware**: Raspberry Pi 4B+ with Sony IMX500 AI Camera
- **OS**: Raspberry Pi OS (Bullseye or newer)
- **Docker**: Docker Engine 20.10+ and Docker Compose 2.0+
- **Storage**: Minimum 8GB free space for image cache
- **Network**: Local network access for container management

### Software Dependencies

```bash
# Install required packages
sudo apt update
sudo apt install -y python3 python3-pip docker.io docker-compose

# Install Python dependencies
pip3 install numpy opencv-python Pillow systemd-python

# Verify camera tools
which rpicam-still || sudo apt install -y camera-utils

# Test camera functionality
rpicam-still -o /tmp/test.jpg --immediate
```

## Deployment Steps

### Step 1: Prepare Shared Volume

```bash
# Create shared directory structure
sudo mkdir -p /mnt/storage/camera_capture/{live,metadata,snapshots,processed}

# Set correct permissions
sudo chown -R pi:pi /mnt/storage/camera_capture
sudo chmod -R 755 /mnt/storage/camera_capture

# Verify structure
tree /mnt/storage/camera_capture/
```

### Step 2: Deploy Host Camera Capture Service

#### Copy Service Files

```bash
# Copy service files to system location
sudo cp scripts/host-camera-capture.py /usr/local/bin/
sudo chmod +x /usr/local/bin/host-camera-capture.py

# Copy systemd service definition
sudo cp scripts/host-camera-capture.service /etc/systemd/system/
```

#### Configure Service

```bash
# Edit service configuration if needed
sudo nano /etc/systemd/system/host-camera-capture.service

# Example custom configuration:
# ExecStart=/usr/bin/python3 /usr/local/bin/host-camera-capture.py \
#   --capture-dir /mnt/storage/camera_capture \
#   --interval 1.0 \
#   --max-images 100 \
#   --quality 95
```

#### Enable and Start Service

```bash
# Reload systemd configuration
sudo systemctl daemon-reload

# Enable service for automatic startup
sudo systemctl enable host-camera-capture

# Start service
sudo systemctl start host-camera-capture

# Verify service status
sudo systemctl status host-camera-capture
```

#### Test Service Operation

```bash
# Watch for new images
watch -n 1 "ls -la /mnt/storage/camera_capture/live/ | tail -5"

# Check service logs
sudo journalctl -u host-camera-capture -f

# Manual test
python3 scripts/host-camera-capture.py --test-only
```

### Step 3: Update Docker Configuration

#### Update docker-compose.yml

The following changes have been made to `docker-compose.yml`:

```yaml
services:
  traffic-monitor:
    # REMOVED: Direct camera device access
    # devices:
    #   - /dev/video0:/dev/video0
    #   - /dev/video1:/dev/video1

    # UPDATED: Reduced device list to essential only
    devices:
      - /dev/ttyACM0:/dev/ttyACM0  # Radar sensor
      - /dev/gpiomem:/dev/gpiomem  # GPIO access

    # UPDATED: Reduced privileges 
    privileged: false
    cap_add:
      - NET_ADMIN
      - SYS_TIME

    # ADDED: Shared volume mount
    volumes:
      - /mnt/storage/camera_capture:/app/data/camera_capture:rw
      - ./config:/app/config:ro
      - ./logs:/app/logs:rw

    # ADDED: Environment configuration
    environment:
      - USE_SHARED_VOLUME_IMAGES=true
      - HOST_CAPTURE_ARCHITECTURE=true
      - CAMERA_CAPTURE_DIR=/app/data/camera_capture
      - IMAGE_MAX_AGE_SECONDS=5.0
```

#### Deploy Updated Configuration

```bash
# Stop existing containers
docker-compose down

# Pull any updated images
docker-compose pull

# Deploy with updated configuration
docker-compose up -d

# Verify container startup
docker-compose ps
docker-compose logs traffic-monitor
```

#### Verify Container Access

```bash
# Check shared volume mount
docker exec traffic-monitoring-edge ls -la /app/data/camera_capture/

# Verify image access
docker exec traffic-monitoring-edge ls -la /app/data/camera_capture/live/

# Test image loading
docker exec traffic-monitoring-edge python3 -c "
from shared_volume_image_provider import SharedVolumeImageProvider
provider = SharedVolumeImageProvider()
success, image, metadata = provider.get_latest_image()
print(f'Image loaded: {success}, Shape: {image.shape if success else None}')
"
```

### Step 4: Deploy Image Synchronization Manager (Optional)

The Image Sync Manager provides additional monitoring and coordination between host and container services.

#### Install as Systemd Service

```bash
# Create service definition
sudo tee /etc/systemd/system/image-sync-manager.service << EOF
[Unit]
Description=Image Synchronization Manager
After=network.target docker.service host-camera-capture.service
Requires=host-camera-capture.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/CST_590_Computer_Science_Capstone_Project
ExecStart=/usr/bin/python3 /home/pi/CST_590_Computer_Science_Capstone_Project/scripts/image-sync-manager.py
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable image-sync-manager
sudo systemctl start image-sync-manager

# Verify service status
sudo systemctl status image-sync-manager
```

#### Manual Operation

```bash
# Run in foreground for testing
python3 scripts/image-sync-manager.py

# Run in background
nohup python3 scripts/image-sync-manager.py > /var/log/image-sync-manager.log 2>&1 &

# Check status
python3 scripts/image-sync-manager.py --status
```

## Verification and Testing

### Step 5: Run Integration Tests

```bash
# Run comprehensive test suite
python3 test_host_capture_architecture.py --mode all

# Test specific components
python3 test_host_capture_architecture.py --mode basic
python3 test_host_capture_architecture.py --mode performance
python3 test_host_capture_architecture.py --mode integration
```

### Step 6: Verify End-to-End Operation

#### Check Image Capture Pipeline

```bash
# 1. Verify host capture is working
ls -la /mnt/storage/camera_capture/live/

# 2. Check newest image age
newest=$(ls -t /mnt/storage/camera_capture/live/*.jpg | head -1)
age=$(($(date +%s) - $(stat -c %Y "$newest")))
echo "Newest image age: $age seconds"

# 3. Verify container can access images
docker exec traffic-monitoring-edge ls -la /app/data/camera_capture/live/
```

#### Test Processing Services

```bash
# Test vehicle detection service
docker exec traffic-monitoring-edge python3 -c "
from edge_processing.vehicle_detection.vehicle_detection_service import VehicleDetectionService
service = VehicleDetectionService()
service.initialize_camera()
success, frame = service.capture_frame()
print(f'Frame captured: {success}, Shape: {frame.shape if success else None}')
"

# Test sky analysis service
docker exec traffic-monitoring-edge python3 -c "
from edge_processing.vehicle_detection.sky_analyzer import SkyAnalyzer
analyzer = SkyAnalyzer()
result = analyzer.analyze_current_sky()
print(f'Sky analysis: {result}')
"
```

## Configuration Options

### Host Camera Capture Service Configuration

```bash
# Service configuration options
python3 scripts/host-camera-capture.py --help

# Key parameters:
# --capture-dir: Directory for image storage (default: /mnt/storage/camera_capture)
# --interval: Capture interval in seconds (default: 1.0)
# --width: Image width in pixels (default: 4056)
# --height: Image height in pixels (default: 3040)
# --quality: JPEG quality 1-100 (default: 95)
# --max-images: Maximum images to retain (default: 100)
```

### Shared Volume Image Provider Configuration

```python
# In processing services, configure provider
from shared_volume_image_provider import SharedVolumeImageProvider

provider = SharedVolumeImageProvider(
    shared_volume_dir="/app/data/camera_capture",
    cache_size=10,                    # Number of images to cache
    background_monitoring=True,        # Enable background monitoring
    monitor_interval=0.1,             # Monitor interval in seconds
    max_age_seconds=5.0               # Maximum image age
)
```

### Docker Container Configuration

```yaml
# Additional environment variables
environment:
  - USE_SHARED_VOLUME_IMAGES=true
  - HOST_CAPTURE_ARCHITECTURE=true
  - CAMERA_CAPTURE_DIR=/app/data/camera_capture
  - IMAGE_MAX_AGE_SECONDS=5.0
  - IMAGE_CACHE_SIZE=10
  - ENABLE_PERFORMANCE_MONITORING=true
```

## Post-Deployment Validation

### Performance Benchmarks

```bash
# Run performance test
python3 test_host_capture_architecture.py --mode performance

# Expected results:
# - Image capture: 1-3 seconds per image
# - Image detection: <100ms
# - Cache hit: <50ms
# - End-to-end: <1 second for recent images
```

### Health Monitoring

```bash
# Check all service status
sudo systemctl status host-camera-capture image-sync-manager

# Check Docker container health
docker-compose ps
docker stats traffic-monitoring-edge --no-stream

# Monitor disk usage
df -h /mnt/storage/
du -sh /mnt/storage/camera_capture/*
```

### Log Monitoring

```bash
# Monitor service logs
sudo journalctl -u host-camera-capture -f
sudo journalctl -u image-sync-manager -f

# Monitor container logs
docker-compose logs -f traffic-monitor

# Check for errors
grep -i error /var/log/*.log
docker-compose logs traffic-monitor | grep -i error
```

## Rollback Procedure

If issues occur, you can rollback to the original direct camera access:

### Step 1: Stop New Services

```bash
# Stop host-capture services
sudo systemctl stop host-camera-capture image-sync-manager
sudo systemctl disable host-camera-capture image-sync-manager
```

### Step 2: Restore Original Docker Configuration

```bash
# Restore original docker-compose.yml (if backed up)
cp docker-compose.yml.backup docker-compose.yml

# Or manually restore camera device access:
# devices:
#   - /dev/video0:/dev/video0
#   - /dev/video1:/dev/video1
# privileged: true
```

### Step 3: Restart Container

```bash
# Deploy original configuration
docker-compose down
docker-compose up -d
```

## Troubleshooting Common Issues

### Service Won't Start

```bash
# Check service logs
sudo journalctl -u host-camera-capture --no-pager

# Common issues:
# - Camera not connected: Check hardware
# - Permission denied: Check file permissions
# - Directory not found: Verify shared volume structure
```

### No Images in Shared Volume

```bash
# Test camera manually
rpicam-still -o /tmp/test.jpg --immediate

# Check service configuration
sudo systemctl cat host-camera-capture

# Check directory permissions
ls -la /mnt/storage/camera_capture/
```

### Container Cannot Access Images

```bash
# Check volume mount
docker inspect traffic-monitoring-edge | grep -A 10 Mounts

# Verify directory structure in container
docker exec traffic-monitoring-edge find /app/data/camera_capture -type f

# Check file permissions
ls -la /mnt/storage/camera_capture/live/
```

This deployment guide ensures a systematic and reliable installation of the host-capture architecture solution.