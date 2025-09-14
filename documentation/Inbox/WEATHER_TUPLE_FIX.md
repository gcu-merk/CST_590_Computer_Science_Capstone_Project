# Weather Analysis Tuple Fix

## Problem Identified

The weather analysis was failing with the error:

```text
"'tuple' object has no attribute 'shape'"
```

This occurred because the `get_current_frame()` method in `VehicleDetectionService` was returning a tuple `(success, frame)` instead of just the frame numpy array, but the weather analysis code expected a numpy array.

## Root Cause

In `edge_processing/vehicle_detection/vehicle_detection_service.py`, the `get_current_frame()` method was incorrectly returning the result of `capture_frame()` directly:

```python
def get_current_frame(self):
    try:
        return self.capture_frame()  # Returns (success, frame) tuple
    except Exception as e:
        return None
```

However, the weather API code in `edge_api/edge_api_gateway.py` expected just the frame:

```python
current_frame = self.vehicle_detection_service.get_current_frame()
sky_result = self.sky_analyzer.analyze_sky_condition(current_frame)  # Expects numpy array
```

## Solution Applied

Modified the `get_current_frame()` method to properly extract the frame from the tuple:

```python
def get_current_frame(self):
    """
    Get the current camera frame for weather analysis
    
    Returns:
        Current frame as numpy array or None if not available
    """
    try:
        success, frame = self.capture_frame()
        if success and frame is not None:
            return frame
        else:
            return None
    except Exception as e:
        logger.warning(f"Could not get current frame for weather analysis: {e}")
        return None
```

## Impact

This fix resolves the weather analysis errors and allows proper sky condition analysis. The weather API endpoints should now return valid results instead of errors.

## Files Modified

- `edge_processing/vehicle_detection/vehicle_detection_service.py`: Fixed `get_current_frame()` method

## Testing

Created `test_weather_fix.py` to verify the fix works correctly by testing:

1. Direct SkyAnalyzer functionality
2. PiSystemStatus weather metrics
3. VehicleDetectionService get_current_frame method

The weather API endpoints should now work properly:

- `/api/weather` - Current weather conditions
- `/api/weather/history` - Historical weather data
- `/api/weather/stats` - Database statistics
- `/api/weather/correlation` - Weather-traffic correlation

## Expected Results

After this fix, weather API responses should look like:

```json
{
  "weather_enabled": true,
  "timestamp": "2025-09-12T18:37:12.938512",
  "sky_condition": {
    "condition": "clear",
    "confidence": 0.85,
    "analysis_methods": {
      "color": {"condition": "clear", "confidence": 0.88},
      "brightness": {"condition": "clear", "confidence": 0.82},
      "texture": {"condition": "clear", "confidence": 0.85}
    }
  },
  "visibility_estimate": "excellent",
  "camera_available": true
}
```
