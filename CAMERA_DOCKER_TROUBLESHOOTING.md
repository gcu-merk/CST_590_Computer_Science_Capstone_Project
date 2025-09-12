# Camera Docker Troubleshooting Guide

# Camera Docker Troubleshooting Guide

**✅ SOLUTION FOUND:** Hybrid Host-Container Architecture

## Proven Working Solution

After extensive testing, the optimal approach is:
- **Capture on Host**: Use `rpicam-still` directly on Raspberry Pi 5  
- **Process in Container**: Mount shared volume and process images in Docker
- **Best Performance**: Native camera access + containerized processing benefits

### Working Implementation:
```bash
# Host capture (works perfectly)
rpicam-still -o /mnt/storage/traffic_$(date +%Y%m%d_%H%M%S).jpg

# Container processing (immediate access)
docker run --rm -v /mnt/storage:/shared traffic-monitoring-edge:latest \
  python3 /app/process_traffic.py /shared/traffic_image.jpg
```

## Quick Solution Implementation

### Step 1: Create Host Capture Script
```bash
# Create capture script on Pi
sudo tee /usr/local/bin/capture-traffic.sh << 'EOF'
#!/bin/bash
# Capture high-quality traffic image
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
IMAGE_PATH="/mnt/storage/traffic_${TIMESTAMP}.jpg"

rpicam-still -o "$IMAGE_PATH" \
  --width 4056 --height 3040 \
  --quality 95 \
  --immediate

echo "Captured: $IMAGE_PATH"
echo "$IMAGE_PATH"  # Return path for container processing
EOF

sudo chmod +x /usr/local/bin/capture-traffic.sh
```

### Step 2: Test the Hybrid Solution
```bash
# Test host capture
/usr/local/bin/capture-traffic.sh

# Test container processing
docker exec traffic-monitoring-edge python3 -c "
import os
import cv2
storage_path = '/mnt/storage'
images = [f for f in os.listdir(storage_path) if f.endswith('.jpg')]
if images:
    latest_image = os.path.join(storage_path, sorted(images)[-1])
    print(f'Processing: {latest_image}')
    frame = cv2.imread(latest_image)
    if frame is not None:
        print(f'✅ Successfully loaded image: {frame.shape}')
    else:
        print('❌ Failed to load image')
else:
    print('❌ No images found in storage')
"
```

## Step 1: Enter the Docker Container

```bash
docker exec -it traffic-monitoring-edge bash
```

## Step 2: Check Camera Hardware Detection

```bash
# Check if video devices exist
ls -la /dev/video*

# List all video devices with details
v4l2-ctl --list-devices

# Check device permissions
ls -la /dev/video0
```

## Step 3: Test System-Level Camera Tools

```bash
# Check if fswebcam is installed
which fswebcam
fswebcam --version

# If fswebcam is missing, install it
apt update && apt install -y fswebcam

# Test basic camera capture
fswebcam --device /dev/video0 --no-banner /tmp/test.jpg

# Check if image was created
ls -la /tmp/test.jpg
```

## Step 4: Test v4l2 Tools

```bash
# Check if v4l2-utils is installed
which v4l2-ctl

# If missing, install it
apt update && apt install -y v4l2-utils

# Get camera capabilities
v4l2-ctl --device=/dev/video0 --all

# List supported formats
v4l2-ctl --device=/dev/video0 --list-formats-ext
```

## Step 5: Test OpenCV Camera Access

```bash
# Test Python OpenCV camera access
python3 -c "
import cv2
print('OpenCV version:', cv2.__version__)
cap = cv2.VideoCapture(0)
if cap.isOpened():
    ret, frame = cap.read()
    if ret:
        print('✅ OpenCV camera capture successful')
        print('Frame shape:', frame.shape)
    else:
        print('❌ OpenCV camera capture failed')
    cap.release()
else:
    print('❌ OpenCV camera failed to open')
"
```

## Step 6: Check Container Environment

```bash
# Check user and permissions
whoami
id

# Check if running in container
cat /proc/1/cgroup | grep docker

# Check environment variables
env | grep -E "(CAMERA|VIDEO|DEVICE)"

# Check current working directory and Python path
pwd
python3 -c "import sys; print('\n'.join(sys.path))"
```

## Step 7: Test the Actual Application

```bash
# Check if the application is running
ps aux | grep python

# Check recent application logs
tail -f /var/log/app.log 2>/dev/null || echo "No app log found"

# Test the camera service directly
cd /app
python3 -c "
from edge_processing.vehicle_detection.vehicle_detection_service import VehicleDetectionService
service = VehicleDetectionService()
print('Testing camera initialization...')
if service.initialize_camera():
    print('✅ Camera initialization successful')
    ret, frame = service.capture_frame()
    if ret:
        print('✅ Frame capture successful')
        print('Frame shape:', frame.shape)
    else:
        print('❌ Frame capture failed')
else:
    print('❌ Camera initialization failed')
"
```

## Step 8: Check Docker Configuration

Exit the container and run these on the host:

```bash
# Check docker-compose configuration
cat docker-compose.yml | grep -A 10 -B 5 devices

# Check if devices are properly mounted
docker inspect traffic-monitoring-edge | grep -A 20 "Devices"

# Restart container with fresh configuration
docker-compose down
docker-compose up -d

# Check container logs
docker logs traffic-monitoring-edge --tail=50
```

## Common Fixes Based on Findings

### If /dev/video0 doesn't exist

- Camera hardware not connected
- Check physical camera connection
- Restart Raspberry Pi

### If fswebcam/v4l2-ctl missing

- Add to Dockerfile:

```dockerfile
RUN apt-get update && apt-get install -y \
    fswebcam \
    v4l2-utils \
    && rm -rf /var/lib/apt/lists/*
```

### If permission denied

- Add to docker-compose.yml:

```yaml
privileged: true
```

Or add user to video group:

```yaml
user: "1000:44"  # video group
```

### If OpenCV fails but fswebcam works

- This confirms our fswebcam fallback approach is correct
- The existing code should handle this automatically

## Quick Test Commands Summary

```bash
# One-liner camera test
docker exec traffic-monitoring-edge bash -c "ls /dev/video* && fswebcam --device /dev/video0 --no-banner /tmp/test.jpg && ls -la /tmp/test.jpg"

# One-liner application test
docker exec traffic-monitoring-edge python3 -c "from edge_processing.vehicle_detection.vehicle_detection_service import VehicleDetectionService; s=VehicleDetectionService(); print('Init:', s.initialize_camera()); print('Capture:', s.capture_frame()[0])"
```

## Complete Troubleshooting Commands (Copy-Paste Block)

```bash
# ===============================================
# COMPLETE CAMERA TROUBLESHOOTING SCRIPT
# Copy and paste this entire block to troubleshoot
# ===============================================

echo "🔍 Starting Complete Camera Troubleshooting..."
echo "=============================================="

# Step 1: Check container status
echo -e "\n📋 1. Container Status Check"
echo "----------------------------"
docker ps | grep traffic-monitoring
docker stats traffic-monitoring-edge --no-stream

# Step 2: Enter container and check hardware
echo -e "\n📋 2. Hardware Detection (Inside Container)"
echo "--------------------------------------------"
docker exec traffic-monitoring-edge bash -c "
echo 'Video devices:'
ls -la /dev/video* 2>/dev/null || echo 'No video devices found'
echo -e '\nDevice permissions:'
ls -la /dev/video0 2>/dev/null || echo '/dev/video0 not found'
echo -e '\nUser info:'
whoami && id
echo -e '\nContainer check:'
cat /proc/1/cgroup | grep docker
"

# Step 3: Test camera tools
echo -e "\n📋 3. Camera Tools Test"
echo "-----------------------"
docker exec traffic-monitoring-edge bash -c "
echo 'fswebcam availability:'
which fswebcam && fswebcam --version
echo -e '\nv4l2-ctl availability:'
which v4l2-ctl && v4l2-ctl --list-devices
"

# Step 4: Test manual camera capture
echo -e "\n📋 4. Manual Camera Capture Test"
echo "--------------------------------"
docker exec traffic-monitoring-edge bash -c "
echo 'Testing rpicam-still (modern Raspberry Pi camera):'
if command -v rpicam-still >/dev/null 2>&1; then
    timeout 10 rpicam-still -o /tmp/test_rpicam.jpg --immediate 2>&1
    if [ -f /tmp/test_rpicam.jpg ]; then
        ls -la /tmp/test_rpicam.jpg
        echo \"✅ Success with rpicam-still\"
        rm -f /tmp/test_rpicam.jpg
    else
        echo \"❌ Failed with rpicam-still\"
    fi
else
    echo \"❌ rpicam-still not available\"
fi

echo -e '\nTesting fswebcam (legacy method):'
for dev in /dev/video{0..7}; do
    if [ -e \$dev ]; then
        echo \"Testing \$dev:\"
        timeout 10 fswebcam --device \$dev --no-banner /tmp/test_\$(basename \$dev).jpg 2>&1 | head -3
        if [ -f /tmp/test_\$(basename \$dev).jpg ]; then
            ls -la /tmp/test_\$(basename \$dev).jpg
            echo \"✅ Success with \$dev\"
            rm -f /tmp/test_\$(basename \$dev).jpg
            break
        else
            echo \"❌ Failed with \$dev\"
        fi
    fi
done
"

# Step 5: Check Python application
echo -e "\n📋 5. Python Application Test"
echo "-----------------------------"
docker exec traffic-monitoring-edge bash -c "
echo 'Current Python processes:'
ps aux | grep python | grep -v grep
echo -e '\nPython path and working directory:'
cd /app && pwd
python3 -c 'import sys; print(\"Python path:\", sys.path[0:3])'
"

# Step 6: Test camera service
echo -e "\n📋 6. Camera Service Test"
echo "-------------------------"
docker exec traffic-monitoring-edge python3 -c "
from edge_processing.vehicle_detection.vehicle_detection_service import VehicleDetectionService
import logging
logging.basicConfig(level=logging.DEBUG)
service = VehicleDetectionService()
print('=== Testing Camera Service ===')
print('Camera initialization:', service.initialize_camera())
ret, frame = service.capture_frame()
print(f'Frame capture: ret={ret}, frame_shape={frame.shape if ret and frame is not None else None}')
"

# Step 7: Test enhanced fallback
echo -e "\n📋 7. Enhanced Fallback Test"
echo "----------------------------"
docker exec traffic-monitoring-edge python3 -c "
from edge_processing.vehicle_detection.vehicle_detection_service import VehicleDetectionService
import logging
logging.basicConfig(level=logging.DEBUG)
service = VehicleDetectionService()
print('=== Testing System-Level Capture (rpicam-still + fswebcam fallback) ===')
ret, frame = service._capture_frame_system_level()
print(f'System capture result: ret={ret}, frame_shape={frame.shape if ret and frame is not None else None}')
"

# Step 8: Check storage and snapshots
echo -e "\n📋 8. Storage and Snapshot Check"
echo "--------------------------------"
docker exec traffic-monitoring-edge bash -c "
echo 'Storage directory check:'
ls -la /mnt/storage/ 2>/dev/null || echo '/mnt/storage not found'
echo -e '\nSnapshot directories:'
for dir in '/mnt/storage/periodic_snapshots' '/tmp/periodic_snapshots' '/app/periodic_snapshots'; do
    if [ -d \$dir ]; then
        echo \"✅ \$dir exists:\"
        ls -la \$dir | tail -5
    else
        echo \"❌ \$dir not found\"
    fi
done
echo -e '\nTesting write permissions:'
mkdir -p /mnt/storage/test_write 2>/dev/null && echo '✅ /mnt/storage writable' || echo '❌ /mnt/storage not writable'
"

# Step 9: Check application logs
echo -e "\n📋 9. Application Logs"
echo "----------------------"
docker logs traffic-monitoring-edge --tail=30 | grep -i 'camera\|snapshot\|frame\|error' || echo "No camera-related logs found"

# Step 10: Final status
echo -e "\n📋 10. Final Health Check"
echo "-------------------------"
curl -s http://localhost:5000/api/health 2>/dev/null | grep -A 5 -B 5 camera || echo "Health endpoint not accessible"

echo -e "\n🏁 Troubleshooting Complete!"
echo "=============================="
```
