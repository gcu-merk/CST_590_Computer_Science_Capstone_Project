# Host-Capture Architecture Deployment Issues & Fixes

## Overview

This document captures specific deployment issues encountered during the initial rollout of the Host-Capture Architecture and their resolutions. These fixes are critical for successful deployment on Raspberry Pi systems.

## Issue #1: Docker Container Device Mapping Failures

### Problem Description

**Date Encountered**: Initial deployment  
**Severity**: Critical - Container fails to start  
**Error Message**:

```text
error gathering device information while adding custom device "/dev/ttyACM0": no such file or directory
```

### Root Cause Analysis

The docker-compose.yml configuration was attempting to map hardware devices that were not available on all Raspberry Pi systems:

1. **Missing Radar Sensor Device**: `/dev/ttyACM0` was not present (radar sensor not connected or not detected)
2. **Incorrect GPIO Device Path**: `/dev/gpiomem` did not exist, but `/dev/gpiomem0` through `/dev/gpiomem4` were available

### Device Availability Investigation

```bash
# Commands used to investigate available devices
ls -la /dev/ttyACM*     # Result: No such file or directory
ls -la /dev/gpio*       # Result: Found gpiomem0, gpiomem1, gpiomem2, gpiomem3, gpiomem4
ls -la /dev/gpiomem*    # Result: Found /dev/gpiomem0
```

### Solution Applied

#### 1. Updated docker-compose.yml Device Mapping

**Before (Problematic Configuration)**:

```yaml
devices:
  - /dev/ttyACM0:/dev/ttyACM0  # Radar sensor access
  - /dev/gpiomem:/dev/gpiomem  # GPIO access
```

**After (Fixed Configuration)**:

```yaml
devices:
  # - /dev/ttyACM0:/dev/ttyACM0  # Radar sensor access (commented out - device not available)
  - /dev/gpiomem0:/dev/gpiomem  # GPIO access (using gpiomem0)
```

#### 2. Container Cleanup and Recreation

```bash
# Remove container with old configuration
docker rm traffic-monitoring-edge

# Recreate container with updated configuration
cd /home/merk/traffic-monitor-deploy
docker-compose up -d
```

### Verification Steps

After applying the fix:

```bash
# Check container status
docker-compose ps
# Result: Container "Up and running" with health check starting

# Verify port mapping
docker port traffic-monitoring-edge
# Result: 5000/tcp -> 0.0.0.0:5000

# Check container logs
docker logs traffic-monitoring-edge
# Result: No device mapping errors, container starts successfully
```

### Final Status

✅ **Container Status**: Up and running  
✅ **Port Access**: 5000 properly mapped for API access  
✅ **Volume Mounts**: All preserved for data persistence  
✅ **GPIO Access**: Maintained through /dev/gpiomem0  
✅ **Essential Functionality**: Maintained without missing device dependencies

## Prevention Guidelines

### Pre-Deployment Device Check

Before deploying the host-capture architecture, always run this device availability check:

```bash
#!/bin/bash
# Device availability check script

echo "=== Device Availability Check ==="
echo

echo "1. Checking GPIO devices:"
if ls /dev/gpiomem* >/dev/null 2>&1; then
    echo "✅ GPIO devices found:"
    ls -la /dev/gpiomem*
    GPIOMEM_DEVICE=$(ls /dev/gpiomem* | head -1)
    echo "   Recommended device mapping: ${GPIOMEM_DEVICE}:/dev/gpiomem"
else
    echo "❌ No GPIO devices found"
fi
echo

echo "2. Checking radar sensor device:"
if ls /dev/ttyACM* >/dev/null 2>&1; then
    echo "✅ Radar sensor devices found:"
    ls -la /dev/ttyACM*
    echo "   Enable device mapping: /dev/ttyACM0:/dev/ttyACM0"
else
    echo "❌ No radar sensor device found"
    echo "   Comment out device mapping: # - /dev/ttyACM0:/dev/ttyACM0"
fi
echo

echo "3. Checking camera devices (should be absent for host-capture architecture):"
if ls /dev/video* >/dev/null 2>&1; then
    echo "ℹ️ Camera devices found (will be ignored in host-capture mode):"
    ls -la /dev/video*
else
    echo "✅ No camera devices found (expected for host-capture)"
fi
echo

echo "=== Check Complete ==="
```

### Updated Deployment Procedure

1. **Run Device Check**: Execute the device availability check script
2. **Update docker-compose.yml**: Modify device mappings based on check results
3. **Clean Previous Containers**: Remove any existing containers with old configurations
4. **Deploy**: Use `docker-compose up -d` to create container with correct mappings
5. **Verify**: Check container status and logs for successful startup

### docker-compose.yml Template

Use this template as a starting point, commenting/uncommenting device mappings based on your system:

```yaml
services:
  traffic-monitor:
    # ... other configuration ...
    
    devices:
      # Radar sensor - uncomment if /dev/ttyACM0 exists
      # - /dev/ttyACM0:/dev/ttyACM0
      
      # GPIO access - use available gpiomem device
      - /dev/gpiomem0:/dev/gpiomem  # Most common
      # - /dev/gpiomem1:/dev/gpiomem  # Alternative if gpiomem0 not available
      
      # Camera devices - SHOULD BE COMMENTED OUT for host-capture architecture
      # - /dev/video0:/dev/video0    # Not used in host-capture
      # - /dev/video1:/dev/video1    # Not used in host-capture
```

## Related Documentation Updates

This issue and its resolution have been incorporated into:

- **HOST_CAPTURE_DEPLOYMENT.md**: Updated deployment steps include device checking
- **HOST_CAPTURE_TROUBLESHOOTING.md**: Added Docker container startup troubleshooting section
- **docker-compose.yml**: Updated with correct device mappings and comments

## Lessons Learned

1. **Always Verify Hardware Availability**: Device mappings should be verified before deployment
2. **Graceful Degradation**: System should function without optional hardware (radar sensor)
3. **Clear Documentation**: Device mapping requirements must be clearly documented
4. **Pre-Deployment Validation**: Include device checks in deployment procedures

This fix ensures reliable container deployment across different Raspberry Pi configurations while maintaining essential functionality.
