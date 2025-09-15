# Host-Capture Weather Analysis Implementation

## Overview

Modified the weather analysis system to use the **host-capture/container-process architecture** where:

1. **Photos are taken outside the Docker container** (on the Raspberry Pi host)
2. **Analysis is performed inside the Docker container** (using shared volume)

This resolves the camera access issues within Docker containers while maintaining full weather analysis capabilities.

## Problem Solved

**Previous Issue**: Weather API was failing with:

```json
{
  "camera_available": false,
  "error": "No camera data available for weather analysis", 
  "weather_enabled": true
}
```

**Root Cause**: The weather API was trying to get camera frames directly from the vehicle detection service inside the Docker container, but camera access is not available in the containerized environment.

## Solution Implementation

### Architecture Changes

#### Before (Direct Camera Access)

```text
┌─────────────────────────────────────┐
│         Docker Container            │
│  ┌─────────────┐  ┌──────────────┐  │
│  │   Camera    │──│   Weather    │  │
│  │   Access    │  │   Analysis   │  │
│  └─────────────┘  └──────────────┘  │
│         ❌ FAILS                     │
└─────────────────────────────────────┘
```

#### After (Host-Capture Architecture)

```text
┌─────────────────────────────────────┐
│        Raspberry Pi Host            │
│  ┌─────────────┐  ┌──────────────┐  │
│  │   Camera    │──│  Shared      │  │
│  │   Capture   │  │  Volume      │  │
│  └─────────────┘  └──────────────┘  │
└─────────────────────────┼───────────┘
                          │
┌─────────────────────────▼───────────┐
│         Docker Container            │
│  ┌──────────────┐  ┌──────────────┐ │
│  │  Shared      │──│   Weather    │ │
│  │  Volume      │  │   Analysis   │ │
│  └──────────────┘  └──────────────┘ │
│         ✅ WORKS                     │
└─────────────────────────────────────┘
```

### Code Changes

#### Modified Weather API Endpoint (`/api/weather`)

**Before**:

```python
# Get current frame from vehicle detection service
current_frame = self.vehicle_detection_service.get_current_frame()
if current_frame is None:
    return error_response()

# Analyze using direct frame
sky_result = self.sky_analyzer.analyze_sky_condition(current_frame)
```

**After**:

```python
# Use host-capture architecture - analyze from shared volume
max_age = request.args.get('max_age_seconds', 10.0, type=float) 
sky_result = self.sky_analyzer.analyze_current_sky(max_age_seconds=max_age)

# Handle both success and failure cases gracefully
if 'error' in sky_result:
    # Still return useful data even if no recent images
    return partial_response_with_system_metrics()
else:
    return full_weather_analysis()
```

#### Key Improvements

1. **Uses `analyze_current_sky()` method**: This method automatically uses the shared volume image provider to get recent images captured on the host
2. **Configurable image age**: API accepts `max_age_seconds` parameter to control how recent images must be
3. **Graceful degradation**: If no recent images are available, still returns system metrics and partial weather data
4. **Better error reporting**: Includes image source, age, and availability information

### API Usage

#### New Parameters

- `max_age_seconds` (optional): Maximum age of image to use for analysis (default: 10.0 seconds)

#### Example Requests

```bash
# Standard weather analysis (images up to 10 seconds old)
curl http://100.121.231.16:5000/api/weather

# Accept older images (up to 30 seconds)
curl http://100.121.231.16:5000/api/weather?max_age_seconds=30.0

# Require very recent images (up to 5 seconds)
curl http://100.121.231.16:5000/api/weather?max_age_seconds=5.0
```

#### Success Response

```json
{
  "weather_enabled": true,
  "timestamp": "2025-09-12T19:15:00.123456",
  "sky_condition": {
    "condition": "clear",
    "confidence": 0.85,
    "analysis_methods": {
      "color": {"condition": "clear", "confidence": 0.88},
      "brightness": {"condition": "clear", "confidence": 0.82},
      "texture": {"condition": "clear", "confidence": 0.85}
    },
    "image_source": "shared_volume",
    "image_age_seconds": 3.2
  },
  "visibility_estimate": "excellent",
  "camera_available": true,
  "image_source": "shared_volume",
  "max_age_seconds": 10.0
}
```

#### No Recent Images Response

```json
{
  "weather_enabled": true,
  "timestamp": "2025-09-12T19:15:00.123456", 
  "sky_condition": {
    "error": "No recent image available from shared volume",
    "condition": "unknown",
    "confidence": 0.0
  },
  "visibility_estimate": "variable",
  "camera_available": false,
  "image_source": "shared_volume_failed",
  "max_age_seconds": 10.0
}
```

## Host-Capture Setup Requirements

### 1. Host Camera Capture Service

Must be running on the Raspberry Pi host:

```bash
# Check if host capture service is running
sudo systemctl status host-camera-capture

# Start if not running
sudo systemctl start host-camera-capture
```

### 2. Shared Volume Mount

Docker container must have access to shared volume:

```yaml
# docker-compose.yml
volumes:
  - /mnt/storage/camera_capture:/mnt/storage/camera_capture
```

### 3. Recent Images Available

Host capture service should be creating recent images:

```bash
# Check for recent images
ls -la /mnt/storage/camera_capture/live/

# Should see files like:
# capture_20250912_191500_123.jpg
# capture_20250912_191505_456.jpg
```

## Testing

### Test Host-Capture Weather Analysis

```bash
# Run the test script
python test_host_capture_weather.py

# Test API endpoint directly
curl http://100.121.231.16:5000/api/weather?max_age_seconds=30
```

### Troubleshooting

#### No Recent Images

- Check host camera capture service: `sudo systemctl status host-camera-capture`
- Verify shared volume mount: `docker exec container ls -la /mnt/storage/camera_capture/live/`
- Check disk space: `df -h /mnt/storage/`

#### Analysis Errors  

- Check SkyAnalyzer logs for image processing errors
- Verify image file integrity: `file /mnt/storage/camera_capture/live/*.jpg`
- Test with longer `max_age_seconds` parameter

## Benefits

1. **Camera Compatibility**: Works with any camera setup on the host
2. **Container Isolation**: No need for camera device access in containers
3. **Reliability**: Host capture service handles camera reliability
4. **Flexibility**: Can adjust image age requirements per request
5. **Graceful Degradation**: Provides useful data even when images unavailable

This implementation enables robust weather analysis in containerized environments while leveraging the proven host-capture architecture.
