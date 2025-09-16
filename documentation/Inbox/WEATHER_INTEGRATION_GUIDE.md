# Weather Analysis Integration Guide

## Overview

The Raspberry Pi 5 Edge ML Traffic Monitoring System now includes comprehensive weather analysis capabilities using computer vision to analyze sky conditions. This integration enhances traffic monitoring by correlating weather conditions with traffic patterns and automatically adjusting detection sensitivity.

## Features

### 1. **Sky Condition Analysis**

- **Real-time analysis** of sky conditions using the existing camera feed
- **Condition classification**: Clear, Partly Cloudy, Cloudy
- **Confidence scoring** for each analysis
- **Visibility estimation** based on weather conditions
- **Multiple analysis methods**: Color analysis, brightness analysis, texture analysis

### 2. **Weather-Aware Vehicle Detection**

- **Automatic threshold adjustment** based on weather conditions
- **Improved detection accuracy** in varying visibility conditions
- **Weather context included** in detection results
- **Adaptive sensitivity** for different weather scenarios

### 3. **Data Storage and Correlation**

- **SQLite database** for weather data persistence
- **Historical weather analysis** with configurable retention
- **Traffic-weather correlation** analysis
- **Hourly and daily weather summaries**

### 4. **API Integration**

- **REST endpoints** for weather data access
- **WebSocket support** for real-time weather updates
- **Comprehensive weather history** APIs
- **Correlation analysis** endpoints

## Quick Start

### 1. **Testing Weather Analysis**

Run the standalone test script to verify weather analysis functionality:

```bash
# Test with live camera
python test_sky_analysis.py --mode camera

# Test with a static image
python test_sky_analysis.py --mode image --input path/to/image.jpg

# Generate test images and run batch analysis
python test_sky_analysis.py --mode create-tests
python test_sky_analysis.py --mode batch --input test_sky_images/

# Performance testing
python test_sky_analysis.py --mode performance
```

### 2. **Running with Weather Integration**

Start the main edge application with weather analysis enabled:

```bash
# Full system with weather analysis (default)
python main_edge_app.py

# Disable weather analysis
python main_edge_app.py --no-weather

# Test weather analysis only
python main_edge_app.py --weather-only
```

### 3. **API Access**

Access weather data through the API endpoints:

```bash
# Current weather conditions
curl http://localhost:5000/api/weather

# Weather history (last 24 hours)
curl http://localhost:5000/api/weather/history

# Weather-traffic correlation
curl http://localhost:5000/api/weather/correlation

# Database statistics
curl http://localhost:5000/api/weather/stats

# Current detection sensitivity (weather-influenced)
curl http://localhost:5000/api/detection-sensitivity
```

## API Reference

### Weather Endpoints

#### `GET /api/weather`

Get current weather conditions and sky analysis.

**Response:**

```json
{
  "weather_enabled": true,
  "timestamp": "2025-09-12T10:30:00.123456",
  "sky_condition": {
    "condition": "clear",
    "confidence": 0.85,
    "analysis_methods": {
      "color": {"condition": "clear", "confidence": 0.88},
      "brightness": {"condition": "clear", "confidence": 0.82},
      "texture": {"condition": "clear", "confidence": 0.85}
    }
  },
  "visibility_estimate": "excellent"
}
```

#### `GET /api/weather/history?hours=24&limit=100`

Get weather analysis history.

**Parameters:**

- `hours`: Hours to look back (1-168, default: 24)
- `limit`: Maximum records to return (1-1000, default: 100)

#### `GET /api/weather/correlation?hours=24`

Get weather-traffic correlation analysis.

**Parameters:**

- `hours`: Hours to analyze (1-168, default: 24)

#### `GET /api/weather/stats`

Get weather database statistics.

### WebSocket Events

Subscribe to real-time weather updates:

```javascript
socket.emit('subscribe_weather');

socket.on('weather_update', function(data) {
    console.log('Weather update:', data);
});
```

## Weather-Aware Detection

### How It Works

The system automatically adjusts vehicle detection sensitivity based on current weather conditions:

#### **Clear Conditions (Confidence > 80%)**

- **Detection Threshold**: 0.5 (standard)
- **Save Threshold**: 0.7 (standard)
- **Rationale**: Optimal visibility, use standard thresholds

#### **Partly Cloudy Conditions**

- **Detection Threshold**: 0.45 (-0.05 adjustment)
- **Save Threshold**: 0.65 (-0.05 adjustment)
- **Rationale**: Slightly reduced visibility, minor threshold reduction

#### **Cloudy Conditions (Confidence > 70%)**

- **Detection Threshold**: 0.35 (-0.15 adjustment)
- **Save Threshold**: 0.6 (-0.1 adjustment)
- **Rationale**: Poor visibility, significant threshold reduction to catch more detections

#### **Unknown/Uncertain Conditions**

- **Detection Threshold**: 0.4 (-0.1 adjustment)
- **Save Threshold**: 0.65 (-0.05 adjustment)
- **Rationale**: Conservative adjustment for uncertain conditions

### Manual Threshold Control

You can also manually set detection thresholds:

```python
# In your vehicle detection service
service.set_detection_threshold(0.3)  # Lower threshold for poor conditions
```

## Data Storage

### Database Schema

The weather integration uses SQLite with three main tables:

#### **weather_analysis**

- `id`: Primary key
- `timestamp`: Analysis timestamp
- `condition`: Sky condition (clear/partly_cloudy/cloudy)
- `confidence`: Analysis confidence (0.0-1.0)
- `visibility_estimate`: Visibility assessment
- `analysis_methods`: JSON blob with detailed analysis
- `system_temperature`: System temperature (°C)
- `frame_info`: JSON blob with frame metadata

#### **traffic_events**

- `id`: Primary key
- `timestamp`: Event timestamp
- `event_type`: Type of event (detection/speed/track)
- `event_data`: JSON blob with event data
- `weather_id`: Foreign key to weather_analysis

#### **weather_summaries**

- `id`: Primary key
- `period_start/end`: Time period covered
- `period_type`: 'hourly' or 'daily'
- `condition_counts`: Counts for each condition type
- `avg_confidence`: Average confidence for the period

### Data Retention

- **Default**: 10,000 weather records
- **Automatic cleanup**: Removes oldest records when limit exceeded

## Configuration

### Weather Analysis Settings

Customize weather analysis in `sky_analyzer.py`:

```python
# Sky region ratio (top portion of image to analyze)
sky_region_ratio = 0.3  # Top 30% of image

# Confidence threshold for condition classification
confidence_threshold = 0.7

# Analysis method weights
weights = {'color': 0.5, 'brightness': 0.3, 'texture': 0.2}
```

### Detection Sensitivity Settings

Customize weather-aware detection in `vehicle_detection_service.py`:

```python
# Weather adjustment ranges
weather_adjustments = {
    'clear': {'threshold': 0.0, 'save': 0.0},
    'partly_cloudy': {'threshold': -0.05, 'save': -0.05},
    'cloudy': {'threshold': -0.15, 'save': -0.1}
}
```

## Troubleshooting

### Common Issues

#### **Weather Analysis Not Available**

- **Symptom**: API returns "Weather analysis not available"
- **Solutions**:
  - Check that OpenCV is installed: `pip install opencv-python`
  - Verify camera access
  - Check logs for import errors

#### **No Camera Data for Weather Analysis**

- **Symptom**: API returns "No camera data available"
- **Solutions**:
  - Ensure vehicle detection service is running
  - Check camera initialization
  - Verify camera permissions

#### **Database Errors**

- **Symptom**: Weather storage failures
- **Solutions**:
  - Check disk space in data directory
  - Verify write permissions
  - Check SQLite installation

### Debug Mode

Enable debug logging for weather analysis:

```python
import logging
logging.getLogger('edge_processing.weather_analysis').setLevel(logging.DEBUG)
```

### Test Commands

Verify individual components:

```bash
# Test sky analyzer only
python -c "
from edge_processing.weather_analysis.sky_analyzer import SkyAnalyzer
analyzer = SkyAnalyzer()
print('Sky analyzer initialized successfully')
"

# Test weather storage
python -c "
print('Weather storage initialized successfully')
print(storage.get_database_stats())
"
```

## Performance Considerations

### Resource Usage

- **CPU Impact**: ~5-10% additional CPU usage for weather analysis
- **Memory**: ~50-100MB additional memory for analysis buffers
- **Storage**: ~1KB per weather record, ~1MB per 1000 records
- **Network**: Minimal additional API traffic

### Optimization Tips

1. **Adjust Analysis Frequency**: Reduce weather update frequency in monitoring loop
2. **Limit History**: Reduce `max_records` for weather storage
3. **Disable If Not Needed**: Use `--no-weather` flag if weather analysis not required
4. **Use Selective Analysis**: Analyze only during certain conditions or times

## Integration Examples

### Custom Weather Logic

```python
from edge_processing.weather_analysis.sky_analyzer import SkyAnalyzer

analyzer = SkyAnalyzer()

# Custom analysis with your own logic
def custom_weather_analysis(image):
    result = analyzer.analyze_sky_condition(image)
    
    # Add your custom logic
    if result['condition'] == 'cloudy' and result['confidence'] > 0.8:
        # Heavy cloud cover detected
        return 'storm_approaching'
    
    return result['condition']
```

### Weather-Based Alerting

```python
def check_weather_alerts(weather_data):
    condition = weather_data['sky_condition']['condition']
    confidence = weather_data['sky_condition']['confidence']
    
    if condition == 'cloudy' and confidence > 0.85:
        # Send alert for poor visibility conditions
        send_alert("Poor visibility conditions detected")
        
    return True
```

## Future Enhancements

Planned improvements for weather integration:

1. **Hardware Weather Sensors**: Integration with BME280/BME680 sensors
2. **Weather API Correlation**: Compare sky analysis with external weather APIs
3. **Precipitation Detection**: Enhanced analysis for rain/snow detection
4. **Time-based Analysis**: Day/night mode switching
5. **Machine Learning**: Improved classification with trained models
6. **Weather Prediction**: Short-term weather forecasting based on trends

## Support

For questions or issues related to weather integration:

1. Check the troubleshooting section above
2. Review system logs for detailed error messages
3. Test individual components using the provided test commands
4. Use the standalone test script to isolate issues

The weather integration is designed to enhance your traffic monitoring system while maintaining reliability and performance of the core vehicle detection functionality.
