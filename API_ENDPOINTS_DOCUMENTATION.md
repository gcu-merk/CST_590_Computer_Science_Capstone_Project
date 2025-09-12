# API Endpoints Documentation

## New `/api/endpoints` Endpoint

### Overview
Added a comprehensive API documentation endpoint at `http://100.121.231.16:5000/api/endpoints` that provides a complete listing of all available API endpoints grouped by category.

### Endpoint Details
- **URL**: `http://100.121.231.16:5000/api/endpoints`
- **Method**: `GET`
- **Content-Type**: `application/json`
- **Description**: Returns structured documentation of all available API endpoints

### Response Structure

```json
{
  "api_info": {
    "title": "Traffic Monitoring Edge API",
    "version": "1.0.0", 
    "description": "Real-time traffic monitoring with vehicle detection, speed analysis, and weather integration",
    "base_url": "http://100.121.231.16:5000",
    "timestamp": "2025-09-12T18:45:00.123456"
  },
  "endpoints": {
    "system": {
      "description": "System health and status endpoints",
      "endpoints": [...]
    },
    "vehicle_detection": {
      "description": "Vehicle detection and tracking endpoints", 
      "endpoints": [...]
    },
    "speed_analysis": {
      "description": "Speed measurement and analysis endpoints",
      "endpoints": [...]
    },
    "analytics": {
      "description": "Traffic analytics and insights endpoints",
      "endpoints": [...]
    },
    "weather": {
      "description": "Weather analysis and sky condition endpoints",
      "endpoints": [...]
    },
    "camera": {
      "description": "Camera and image endpoints",
      "endpoints": [...]
    }
  },
  "websocket": {
    "description": "Real-time WebSocket endpoints for live data streaming",
    "url": "http://100.121.231.16:5000",
    "events": [...]
  },
  "usage_examples": {
    "curl_examples": [...]
  }
}
```

### Endpoint Categories

#### 1. System Endpoints
- `/api/health` - System health check
- `/hello` - Connectivity test
- `/api/endpoints` - This documentation endpoint

#### 2. Vehicle Detection Endpoints  
- `/api/detections` - Recent vehicle detections
- `/api/tracks` - Active vehicle tracks
- `/api/detection-sensitivity` - Detection parameters

#### 3. Speed Analysis Endpoints
- `/api/speeds` - Recent speed measurements

#### 4. Analytics Endpoints
- `/api/analytics` - Traffic analytics and insights

#### 5. Weather Endpoints
- `/api/weather` - Current weather conditions
- `/api/weather/history` - Historical weather data
- `/api/weather/correlation` - Weather-traffic correlation
- `/api/weather/stats` - Weather database statistics

#### 6. Camera Endpoints
- `/api/camera/snapshot/<filename>` - Camera snapshot images

### WebSocket Events
The API also provides real-time WebSocket connectivity with events for:
- Vehicle detection updates
- Speed analysis updates  
- Tracking updates
- Weather updates
- Analytics updates

### Usage Examples

#### cURL Examples
```bash
# Get API documentation
curl http://100.121.231.16:5000/api/endpoints

# System health check
curl http://100.121.231.16:5000/api/health

# Recent vehicle detections (last 30 seconds)  
curl http://100.121.231.16:5000/api/detections?seconds=30

# Current weather conditions
curl http://100.121.231.16:5000/api/weather

# Weather history (last 6 hours, max 50 records)
curl http://100.121.231.16:5000/api/weather/history?hours=6&limit=50

# Traffic analytics
curl http://100.121.231.16:5000/api/analytics
```

#### Python Example
```python
import requests

# Get all endpoints
response = requests.get("http://100.121.231.16:5000/api/endpoints")
endpoints_data = response.json()

# Print all available endpoints
for category, info in endpoints_data['endpoints'].items():
    print(f"\n{category.upper()}:")
    for endpoint in info['endpoints']:
        print(f"  {endpoint['method']} {endpoint['path']} - {endpoint['description']}")
```

#### JavaScript Example
```javascript
// Fetch all endpoints
fetch('http://100.121.231.16:5000/api/endpoints')
  .then(response => response.json())
  .then(data => {
    console.log('API Info:', data.api_info);
    console.log('Available Endpoints:', data.endpoints);
    console.log('Usage Examples:', data.usage_examples);
  });
```

### Features

1. **Auto-Generated URLs**: All endpoint URLs are automatically generated based on the request's base URL
2. **Categorized Organization**: Endpoints are logically grouped by functionality
3. **Parameter Documentation**: Optional parameters are documented for each endpoint
4. **Usage Examples**: Practical curl examples for common use cases
5. **WebSocket Documentation**: Information about real-time event subscriptions
6. **Comprehensive Metadata**: API version, description, and timestamp information

### Integration Benefits

- **Developer-Friendly**: Easy discovery of all available endpoints
- **Self-Documenting**: Automatically stays up-to-date with code changes
- **Testing Support**: Provides ready-to-use curl commands for testing
- **API Exploration**: Enables quick understanding of system capabilities

This endpoint serves as a comprehensive API reference that developers can use to understand and interact with the traffic monitoring system's REST API and WebSocket interfaces.