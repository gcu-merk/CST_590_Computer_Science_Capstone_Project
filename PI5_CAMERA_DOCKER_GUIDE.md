# Pi 5 Camera Docker Integration Guide

Based on research from:
- nagtsnegge/pi5-camera-in-docker
- souri-t/PiCamera2-Docker

## Issue
The Raspberry Pi 5 IMX500 AI camera requires special Docker configuration for proper hardware access.

## Pi 5 Camera Docker Requirements

### 1. Device Access
```yaml
devices:
  - /dev/video0:/dev/video0    # Camera device
  - /dev/video10:/dev/video10  # IMX500 neural processor
  - /dev/video11:/dev/video11  # IMX500 output
  - /dev/dri:/dev/dri         # GPU access for libcamera
```

### 2. Privileged Mode (for libcamera)
```yaml
privileged: true
```

### 3. Volume Mounts
```yaml
volumes:
  - /opt/vc:/opt/vc:ro           # VideoCore libraries
  - /sys/bus/i2c:/sys/bus/i2c:ro # I2C bus access
```

### 4. Environment Variables
```yaml
environment:
  - LIBCAMERA_LOG_LEVELS=*:INFO
  - DISPLAY=:0
```

## Implementation Plan

### Phase 1: Test Current Bypass (Immediate)
Use `docker-compose.quick-api.yml` to get Swagger API working without camera.

### Phase 2: Add Camera Support
Update `docker-compose.pi.yml` with proper Pi 5 camera configuration.

### Phase 3: Conditional Camera Loading
Implement runtime camera detection with graceful fallbacks.

## Commands to Test

### Quick API Test (No Camera)
```bash
docker-compose -f docker-compose.quick-api.yml up -d
```

### Full Pi 5 Camera Test
```bash
# After implementing camera device mapping
docker-compose -f docker-compose.pi.yml up -d
```

## Debugging Camera Issues

### Check Camera Devices
```bash
ls -la /dev/video*
```

### Check libcamera
```bash
libcamera-hello --list-cameras
```

### Test in Container
```bash
docker exec -it traffic-monitor python3 -c "from picamera2 import Picamera2; print('Camera OK')"
```