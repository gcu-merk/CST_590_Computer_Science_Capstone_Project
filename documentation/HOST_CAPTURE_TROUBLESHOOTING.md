# Host-Capture Architecture Troubleshooting Guide

## Overview

This guide provides comprehensive troubleshooting procedures for the **Host-Capture/Container-Process Architecture**. It covers common issues, diagnostic procedures, and resolution steps for maintaining reliable operation.

## Table of Contents

- [Quick Diagnostics](#quick-diagnostics)
- [Service Issues](#service-issues)
- [Image Capture Problems](#image-capture-problems)
- [Container Access Issues](#container-access-issues)
- [Performance Problems](#performance-problems)
- [Storage and Cleanup Issues](#storage-and-cleanup-issues)
- [Advanced Diagnostics](#advanced-diagnostics)
- [Recovery Procedures](#recovery-procedures)

## Quick Diagnostics

### System Health Check

Run this comprehensive health check to quickly identify issues:

```bash
#!/bin/bash
# Quick system health check script

echo "=== Host-Capture Architecture Health Check ==="
echo

# Check service status
echo "1. Service Status:"
systemctl is-active host-camera-capture
systemctl is-active image-sync-manager
docker-compose ps | grep traffic-monitor
echo

# Check recent images
echo "2. Recent Images:"
latest_count=$(find /mnt/storage/camera_capture/live/ -name "*.jpg" -newermt "1 minute ago" | wc -l)
echo "Images in last minute: $latest_count"

if [ -n "$(ls -A /mnt/storage/camera_capture/live/ 2>/dev/null)" ]; then
    newest=$(ls -t /mnt/storage/camera_capture/live/*.jpg | head -1)
    age=$(($(date +%s) - $(stat -c %Y "$newest")))
    echo "Newest image age: ${age}s"
else
    echo "No images found"
fi
echo

# Check disk space
echo "3. Disk Usage:"
df -h /mnt/storage/ | grep -v "^Filesystem"
echo

# Check container access
echo "4. Container Access:"
if docker exec traffic-monitoring-edge ls /app/data/camera_capture/live/ >/dev/null 2>&1; then
    container_count=$(docker exec traffic-monitoring-edge ls /app/data/camera_capture/live/ | wc -l)
    echo "Container can access shared volume: $container_count files visible"
else
    echo "Container cannot access shared volume"
fi
echo

echo "=== Health Check Complete ==="
```

### Status Command Summary

```bash
# Essential status commands
sudo systemctl status host-camera-capture image-sync-manager
docker-compose ps
ls -la /mnt/storage/camera_capture/live/ | tail -5
df -h /mnt/storage/
```

## Service Issues

### Docker Container Startup Issues

#### Container Fails to Start with Device Mapping Errors

**Symptoms:**

- Container fails to start with error: `error gathering device information while adding custom device "/dev/ttyACM0": no such file or directory`
- Similar errors for `/dev/gpiomem` or other device mappings

**Diagnosis:**

```bash
# Check available devices on the system
ls -la /dev/ttyACM*  # Check for radar sensor device
ls -la /dev/gpio*    # Check for GPIO devices

# Check container logs
docker logs traffic-monitoring-edge

# Check docker-compose configuration
grep -A 10 "devices:" docker-compose.yml
```

**Solutions:**

1. **Update Device Mappings Based on Available Hardware**

   ```bash
   # Check what GPIO devices are actually available
   ls -la /dev/gpiomem*
   
   # Edit docker-compose.yml to use available devices
   nano docker-compose.yml
   
   # Comment out unavailable devices:
   devices:
     # - /dev/ttyACM0:/dev/ttyACM0  # Commented out if not available
     - /dev/gpiomem0:/dev/gpiomem   # Use gpiomem0 instead of gpiomem
   ```

2. **Remove Old Container and Recreate**

   ```bash
   # Remove container with old configuration
   docker rm traffic-monitoring-edge
   
   # Recreate with updated configuration
   docker-compose up -d
   ```

3. **Verify Container Startup**

   ```bash
   # Check container status
   docker-compose ps
   
   # Verify container is running
   docker logs traffic-monitoring-edge
   ```

### Host Camera Capture Service Problems

#### Service Won't Start

**Symptoms:**

- `systemctl status host-camera-capture` shows "failed" or "inactive"
- No images appearing in shared volume

**Diagnosis:**

```bash
# Check service logs
sudo journalctl -u host-camera-capture --no-pager -n 50

# Check camera hardware
rpicam-still -o /tmp/test.jpg --immediate
ls -la /tmp/test.jpg

# Check file permissions
ls -la /mnt/storage/camera_capture/
stat /usr/local/bin/host-camera-capture.py
```

**Common Issues and Solutions:**

1. **Camera Not Available**

   ```bash
   # Error: "rpicam-still: command not found"
   sudo apt install camera-utils
   
   # Error: "No cameras available"
   # Check hardware connection
   dmesg | grep -i camera
   lsmod | grep bcm2835
   ```

2. **Permission Denied**

   ```bash
   # Fix service file permissions
   sudo chmod 644 /etc/systemd/system/host-camera-capture.service
   sudo chmod +x /usr/local/bin/host-camera-capture.py
   
   # Fix directory permissions
   sudo chown -R pi:pi /mnt/storage/camera_capture
   sudo chmod -R 755 /mnt/storage/camera_capture
   ```

3. **Directory Not Found**

   ```bash
   # Recreate directory structure
   sudo mkdir -p /mnt/storage/camera_capture/{live,metadata,snapshots,processed}
   sudo chown -R pi:pi /mnt/storage/camera_capture
   ```

#### Service Starts But No Images

**Symptoms:**

- Service shows "active (running)" but no images in `/mnt/storage/camera_capture/live/`

**Diagnosis:**

```bash
# Check service logs for errors
sudo journalctl -u host-camera-capture -f

# Manual test capture
python3 /usr/local/bin/host-camera-capture.py --test-only

# Check rpicam-still directly
rpicam-still -o /tmp/manual_test.jpg --immediate --width 4056 --height 3040
```

**Solutions:**

1. **Configuration Issues**

   ```bash
   # Check service configuration
   sudo systemctl cat host-camera-capture
   
   # Verify capture directory
   # Edit service if needed:
   sudo systemctl edit host-camera-capture
   ```

2. **Camera Busy**

   ```bash
   # Check for other processes using camera
   sudo lsof /dev/video*
   
   # Stop conflicting services
   sudo systemctl stop any-camera-service
   ```

### Image Sync Manager Issues

#### Sync Manager Won't Start

**Diagnosis:**

```bash
# Check sync manager logs
sudo journalctl -u image-sync-manager --no-pager -n 50

# Manual test
python3 scripts/image-sync-manager.py --status
```

**Common Solutions:**

```bash
# Check Python dependencies
pip3 install -r requirements.txt

# Fix working directory
sudo systemctl edit image-sync-manager
# Add:
# [Service]
# WorkingDirectory=/home/pi/CST_590_Computer_Science_Capstone_Project
```

## Image Capture Problems

### No Images Being Created

**Systematic Diagnosis:**

```bash
# Step 1: Test camera hardware
rpicam-still -o /tmp/hw_test.jpg --immediate
if [ $? -eq 0 ]; then
    echo "Camera hardware OK"
    ls -la /tmp/hw_test.jpg
else
    echo "Camera hardware issue"
fi

# Step 2: Test with same parameters as service
rpicam-still -o /tmp/service_test.jpg --immediate --width 4056 --height 3040 --quality 95
if [ $? -eq 0 ]; then
    echo "Service parameters OK"
else
    echo "Service parameters issue"
fi

# Step 3: Test directory access
touch /mnt/storage/camera_capture/live/test_file
if [ $? -eq 0 ]; then
    echo "Directory writable"
    rm /mnt/storage/camera_capture/live/test_file
else
    echo "Directory not writable"
fi
```

### Images Created But Too Infrequent

**Symptoms:**

- Images created but gaps longer than configured interval
- Service logs show occasional capture failures

**Diagnosis:**

```bash
# Check capture timing
find /mnt/storage/camera_capture/live/ -name "*.jpg" -printf "%T@ %p\n" | sort -n | tail -10 | awk '{
    if (prev != "") {
        gap = $1 - prev
        printf "Gap: %.1fs - %s\n", gap, $2
    }
    prev = $1
}'

# Check system load
uptime
iostat -x 1 5
```

**Solutions:**

1. **Reduce Capture Resolution**

   ```bash
   # Edit service to use lower resolution temporarily
   sudo systemctl edit host-camera-capture
   # Add lower resolution parameters
   ```

2. **Increase Capture Interval**

   ```bash
   # Modify service configuration
   ExecStart=/usr/bin/python3 /usr/local/bin/host-camera-capture.py --interval 2.0
   ```

### Images Created But Poor Quality

**Diagnosis:**

```bash
# Check recent image sizes
ls -la /mnt/storage/camera_capture/live/ | tail -5

# Expected size: ~1.4MB for 4056x3040 JPEG at quality 95
# If much smaller, quality issue

# Check image properties
identify /mnt/storage/camera_capture/live/$(ls -t /mnt/storage/camera_capture/live/*.jpg | head -1)
```

**Solutions:**

```bash
# Test different quality settings
rpicam-still -o /tmp/q95.jpg --quality 95 --immediate
rpicam-still -o /tmp/q85.jpg --quality 85 --immediate
rpicam-still -o /tmp/q75.jpg --quality 75 --immediate

# Compare sizes and visual quality
ls -la /tmp/q*.jpg
```

## Container Access Issues

### Container Cannot See Shared Volume

**Symptoms:**

- Container services report "No images found"
- `docker exec` shows empty `/app/data/camera_capture/live/` directory

**Diagnosis:**

```bash
# Check volume mount in container
docker inspect traffic-monitoring-edge | grep -A 10 "Mounts"

# Verify mount point exists in container
docker exec traffic-monitoring-edge ls -la /app/data/

# Check if mount point is empty
docker exec traffic-monitoring-edge ls -la /app/data/camera_capture/
```

**Solutions:**

1. **Restart Container with Proper Mounts**

   ```bash
   # Stop container
   docker-compose down
   
   # Verify docker-compose.yml has correct mount
   grep -A 5 "volumes:" docker-compose.yml
   
   # Should include:
   # - /mnt/storage/camera_capture:/app/data/camera_capture:rw
   
   # Restart with updated configuration
   docker-compose up -d
   ```

2. **Fix Volume Permissions**

   ```bash
   # Check host permissions
   ls -la /mnt/storage/camera_capture/
   
   # Fix if needed
   sudo chown -R pi:pi /mnt/storage/camera_capture
   sudo chmod -R 755 /mnt/storage/camera_capture
   ```

### Container Sees Old Images

**Symptoms:**

- Container can access shared volume but images are stale
- Processing services report "Image too old" errors

**Diagnosis:**

```bash
# Compare timestamps between host and container
echo "Host view:"
ls -la /mnt/storage/camera_capture/live/ | tail -3

echo "Container view:"
docker exec traffic-monitoring-edge ls -la /app/data/camera_capture/live/ | tail -3

# Check if clocks are synchronized
docker exec traffic-monitoring-edge date
date
```

**Solutions:**

1. **Restart Host Capture Service**

   ```bash
   sudo systemctl restart host-camera-capture
   
   # Wait for new image
   sleep 5
   
   # Verify new images
   ls -la /mnt/storage/camera_capture/live/ | tail -3
   ```

2. **Increase Maximum Age Tolerance**

   ```python
   # In container services, temporarily increase tolerance
   success, image, metadata = provider.get_latest_image(max_age_seconds=10.0)
   ```

## Performance Problems

### Slow Image Access

**Symptoms:**

- Long delays between image requests and responses
- High CPU usage in container

**Diagnosis:**

```bash
# Run performance test
python3 test_host_capture_architecture.py --mode performance

# Check container resource usage
docker stats traffic-monitoring-edge --no-stream

# Check I/O wait times
iostat -x 1 5
```

**Solutions:**

1. **Optimize Cache Settings**

   ```python
   # Increase cache size in provider
   provider = SharedVolumeImageProvider(
       cache_size=20,  # Increase from default 10
       monitor_interval=0.05  # Reduce from default 0.1
   )
   ```

2. **Reduce Image Size**

   ```bash
   # Temporarily reduce capture resolution
   sudo systemctl edit host-camera-capture
   # Add: --width 2028 --height 1520
   ```

### High Memory Usage

**Symptoms:**

- Container memory usage continuously growing
- System running out of RAM

**Diagnosis:**

```bash
# Check memory usage
free -h
docker stats traffic-monitoring-edge

# Check for memory leaks in provider
# Look for growing cache size without cleanup
```

**Solutions:**

1. **Reduce Cache Size**

   ```python
   # In container services
   provider = SharedVolumeImageProvider(cache_size=5)  # Reduce from 10
   ```

2. **Force Garbage Collection**

   ```python
   # In long-running services
   import gc
   gc.collect()  # Periodically
   ```

## Storage and Cleanup Issues

### Disk Space Running Low

**Symptoms:**

- "No space left on device" errors
- Capture service fails intermittently

**Diagnosis:**

```bash
# Check disk usage
df -h /mnt/storage/
du -sh /mnt/storage/camera_capture/*

# Count files in each directory
echo "Live images: $(find /mnt/storage/camera_capture/live/ -name "*.jpg" | wc -l)"
echo "Metadata files: $(find /mnt/storage/camera_capture/metadata/ -name "*.json" | wc -l)"
echo "Processed images: $(find /mnt/storage/camera_capture/processed/ -name "*.jpg" | wc -l)"
```

**Solutions:**

1. **Emergency Cleanup**

   ```bash
   # Remove images older than 1 hour
   find /mnt/storage/camera_capture/live/ -name "*.jpg" -mtime +0.04 -delete
   find /mnt/storage/camera_capture/metadata/ -name "*.json" -mtime +0.04 -delete
   
   # Remove processed images older than 1 day
   find /mnt/storage/camera_capture/processed/ -name "*.jpg" -mtime +1 -delete
   ```

2. **Automatic Cleanup Configuration**

   ```bash
   # Configure more aggressive cleanup
   sudo systemctl edit host-camera-capture
   # Add: --max-images 50  # Reduce from default 100
   ```

### Cleanup Not Working

**Symptoms:**

- Old images accumulating despite cleanup configuration
- Sync manager not removing old files

**Diagnosis:**

```bash
# Check sync manager status
python3 scripts/image-sync-manager.py --status

# Check file ages
find /mnt/storage/camera_capture/live/ -name "*.jpg" -printf "%T@ %p\n" | sort -n | head -5
```

**Solutions:**

```bash
# Force manual cleanup
python3 scripts/image-sync-manager.py --force-cleanup

# Restart sync manager
sudo systemctl restart image-sync-manager
```

## Advanced Diagnostics

### Performance Profiling

```bash
# Detailed timing analysis
python3 -c "
import time
import numpy as np
from shared_volume_image_provider import SharedVolumeImageProvider

provider = SharedVolumeImageProvider()
times = []

for i in range(10):
    start = time.time()
    success, image, metadata = provider.get_latest_image()
    end = time.time()
    times.append(end - start)
    print(f'Request {i+1}: {end-start:.3f}s, Success: {success}')

print(f'Average: {np.mean(times):.3f}s')
print(f'Min: {np.min(times):.3f}s, Max: {np.max(times):.3f}s')
"
```

### Network Diagnostics

```bash
# Check if networking issues affect container
docker exec traffic-monitoring-edge ping -c 3 google.com

# Check container DNS resolution
docker exec traffic-monitoring-edge nslookup google.com

# Check container to host connectivity
docker exec traffic-monitoring-edge ping -c 3 host.docker.internal
```

### System Resource Analysis

```bash
# Comprehensive resource check
echo "=== CPU Usage ===" 
top -b -n 1 | head -20

echo "=== Memory Usage ==="
free -h
cat /proc/meminfo | grep -E "(MemAvailable|Buffers|Cached)"

echo "=== Disk I/O ==="
iostat -x 1 3

echo "=== Network ==="
netstat -i

echo "=== Process Tree ==="
pstree -p | grep -E "(python|docker|camera)"
```

## Recovery Procedures

### Complete System Recovery

When multiple components are failing:

```bash
#!/bin/bash
# Complete system recovery script

echo "=== Starting Host-Capture Architecture Recovery ==="

# Step 1: Stop all services
echo "Stopping services..."
sudo systemctl stop host-camera-capture image-sync-manager
docker-compose down

# Step 2: Clean up old data
echo "Cleaning up old data..."
sudo rm -rf /mnt/storage/camera_capture/live/*
sudo rm -rf /mnt/storage/camera_capture/metadata/*
sudo rm -rf /mnt/storage/camera_capture/processed/*

# Step 3: Verify directory structure
echo "Verifying directory structure..."
sudo mkdir -p /mnt/storage/camera_capture/{live,metadata,snapshots,processed}
sudo chown -R pi:pi /mnt/storage/camera_capture
sudo chmod -R 755 /mnt/storage/camera_capture

# Step 4: Test camera hardware
echo "Testing camera hardware..."
if rpicam-still -o /tmp/recovery_test.jpg --immediate; then
    echo "Camera hardware OK"
    rm /tmp/recovery_test.jpg
else
    echo "Camera hardware issue - check connections"
    exit 1
fi

# Step 5: Restart services
echo "Restarting services..."
sudo systemctl daemon-reload
sudo systemctl start host-camera-capture
sleep 5
docker-compose up -d
sleep 5

# Step 6: Verify operation
echo "Verifying operation..."
sleep 10  # Wait for first image

if [ -n "$(ls -A /mnt/storage/camera_capture/live/ 2>/dev/null)" ]; then
    echo "SUCCESS: Images being created"
    ls -la /mnt/storage/camera_capture/live/ | tail -3
else
    echo "FAILURE: No images created"
    exit 1
fi

if docker exec traffic-monitoring-edge ls /app/data/camera_capture/live/ >/dev/null 2>&1; then
    echo "SUCCESS: Container can access images"
else
    echo "FAILURE: Container cannot access images"
    exit 1
fi

echo "=== Recovery Complete ==="
```

### Service-Specific Recovery

#### Host Capture Service Only

```bash
# Reset host capture service
sudo systemctl stop host-camera-capture
sudo systemctl reset-failed host-camera-capture
sudo systemctl daemon-reload
sudo systemctl start host-camera-capture

# Verify
sudo systemctl status host-camera-capture
sudo journalctl -u host-camera-capture -n 20
```

#### Container Only

```bash
# Reset container without affecting host
docker-compose stop traffic-monitor
docker-compose rm -f traffic-monitor
docker-compose up -d traffic-monitor

# Verify
docker-compose ps
docker logs traffic-monitoring-edge
```

This troubleshooting guide provides systematic approaches to identify and resolve issues in the host-capture architecture.
