# Camera Docker Troubleshooting Guide

Run these commands step by step to diagnose and fix camera issues in the Docker container.

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

## Common Fixes Based on Findings:

### If /dev/video0 doesn't exist:
- Camera hardware not connected
- Check physical camera connection
- Restart Raspberry Pi

### If fswebcam/v4l2-ctl missing:
- Add to Dockerfile:
```dockerfile
RUN apt-get update && apt-get install -y \
    fswebcam \
    v4l2-utils \
    && rm -rf /var/lib/apt/lists/*
```

### If permission denied:
- Add to docker-compose.yml:
```yaml
privileged: true
```
Or add user to video group:
```yaml
user: "1000:44"  # video group
```

### If OpenCV fails but fswebcam works:
- This confirms our fswebcam fallback approach is correct
- The existing code should handle this automatically

## Quick Test Commands Summary:
```bash
# One-liner camera test
docker exec traffic-monitoring-edge bash -c "ls /dev/video* && fswebcam --device /dev/video0 --no-banner /tmp/test.jpg && ls -la /tmp/test.jpg"

# One-liner application test
docker exec traffic-monitoring-edge python3 -c "from edge_processing.vehicle_detection.vehicle_detection_service import VehicleDetectionService; s=VehicleDetectionService(); print('Init:', s.initialize_camera()); print('Capture:', s.capture_frame()[0])"
```
