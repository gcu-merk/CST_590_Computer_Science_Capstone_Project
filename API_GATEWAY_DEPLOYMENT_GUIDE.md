# Enhanced API Gateway Service - Deployment and Operations Guide

## Overview

The Enhanced API Gateway Service provides a comprehensive REST API with Swagger documentation, WebSocket communication, and full centralized logging integration for the traffic monitoring system.

### Key Features

- **Centralized Logging**: Full integration with ServiceLogger and CorrelationContext
- **Request/Response Correlation**: Track requests across all services with correlation IDs
- **Performance Monitoring**: Automatic timing and performance metrics for all endpoints
- **Swagger Documentation**: Interactive API documentation with real-time testing
- **WebSocket Support**: Real-time communication with correlation tracking
- **Health Monitoring**: System health endpoints with detailed diagnostics
- **Error Handling**: Comprehensive error tracking and reporting

## Architecture

```
HTTP Requests → Enhanced API Gateway → ServiceLogger → Redis/Database → Centralized Logging
     ↓                  ↓                   ↓
WebSocket Clients  Correlation IDs    Business Events
```

## Deployment Options

### 1. Docker Deployment (Recommended)

The enhanced API gateway runs as the `traffic-monitor` service in Docker Compose.

#### Configuration

```yaml
# docker-compose.yml
traffic-monitor:
  image: ${DOCKER_IMAGE:-gcumerk/cst590-capstone-public:latest}
  container_name: traffic-monitor
  command: ["python", "edge_api/edge_api_gateway_enhanced.py"]
  ports:
    - "5000:5000"
  environment:
    # API Configuration
    - API_HOST=0.0.0.0
    - API_PORT=5000
    - API_DEBUG=false
    
    # Centralized Logging
    - SERVICE_NAME=api_gateway_service
    - LOG_LEVEL=INFO
    - LOG_DIR=/app/logs
    - CORRELATION_HEADER=X-Correlation-ID
    
    # Redis Configuration
    - REDIS_HOST=redis
    - REDIS_PORT=6379
    
    # Database Configuration
    - POSTGRES_HOST=postgres
    - POSTGRES_DB=traffic_monitoring
    - POSTGRES_USER=traffic_user
    - POSTGRES_PASSWORD=traffic_password
```

#### Deployment Commands

```bash
# Start the enhanced API gateway
docker-compose up traffic-monitor

# View logs with correlation tracking
docker-compose logs -f traffic-monitor

# Check service status
docker-compose ps traffic-monitor
```

### 2. Standalone Deployment

For development or testing without Docker:

```bash
# Install dependencies
cd edge_api
pip install -r requirements.txt

# Set environment variables
export SERVICE_NAME=api_gateway_service
export LOG_LEVEL=INFO
export LOG_DIR=./logs
export REDIS_HOST=localhost
export REDIS_PORT=6379

# Run enhanced API gateway
python edge_api_gateway_enhanced.py
```

## API Endpoints

### Health and Monitoring

- **GET /api/health/system**: Comprehensive system health status
- **GET /api/health/stats**: API gateway performance statistics

### Vehicle Detection

- **GET /api/vehicles/detections**: Recent vehicle detection data
- **GET /api/vehicles/tracks**: Vehicle tracking information
- **GET /api/vehicles/speeds**: Speed analysis data

### Weather Information

- **GET /api/weather/current**: Current weather from all sources
- **GET /api/weather/history**: Historical weather data

### Analytics

- **GET /api/analytics/traffic**: Traffic flow analytics
- **GET /api/analytics/performance**: System performance metrics

### Documentation

- **GET /**: Swagger UI interactive documentation
- **GET /swagger.json**: OpenAPI specification

## Correlation Tracking

The enhanced API gateway implements comprehensive request correlation tracking:

### Client Usage

```python
import requests

# Generate correlation ID
correlation_id = "req_12345678"

# Send request with correlation header
headers = {"X-Correlation-ID": correlation_id}
response = requests.get(
    "http://localhost:5000/api/health/system", 
    headers=headers
)

# Correlation ID is returned in response
response_correlation = response.headers.get("X-Correlation-ID")
assert response_correlation == correlation_id
```

### Log Correlation

All API requests generate structured logs with correlation IDs:

```json
{
  "timestamp": "2024-01-15T10:30:45.123456Z",
  "service": "api_gateway_service",
  "level": "INFO",
  "correlation_id": "req_12345678",
  "business_event": "api_request_start",
  "endpoint": "/api/health/system",
  "method": "GET",
  "client_ip": "192.168.1.100"
}
```

## WebSocket Communication

Real-time communication with correlation tracking:

```javascript
// Connect to WebSocket
const socket = io('http://localhost:5000');

// Handle connection with correlation ID
socket.on('connected', (data) => {
    console.log('Connected with correlation:', data.correlation_id);
});

// Send messages with correlation
socket.emit('vehicle_detection', {
    correlation_id: 'ws_87654321',
    vehicle_id: 'VH001',
    timestamp: new Date().toISOString()
});
```

## Performance Monitoring

The enhanced gateway provides comprehensive performance monitoring:

### Automatic Metrics

- Request duration timing
- Response size tracking
- Error rate monitoring
- Correlation success rate

### Performance Decorators

```python
@logger.monitor_performance("api_endpoint")
def get_data():
    # Function execution is automatically timed
    return {"data": "example"}
```

### Business Event Logging

```python
logger.info("Vehicle detection processed", extra={
    "business_event": "vehicle_detected",
    "correlation_id": correlation_id,
    "vehicle_count": 5,
    "processing_duration_ms": 150
})
```

## Health Monitoring

### System Health Endpoint

```bash
curl http://localhost:5000/api/health/system
```

Response includes:
- CPU and memory usage
- Disk space information
- Redis connection status
- API gateway statistics
- System information

### API Statistics

```bash
curl http://localhost:5000/api/health/stats
```

Provides:
- Total request count
- Success/failure rates
- Average response times
- Active WebSocket connections
- Uptime information

## Validation and Testing

### Automated Validation

Run the comprehensive validation script:

```bash
python test_enhanced_api_gateway.py
```

Tests include:
- All API endpoints functionality
- Correlation tracking accuracy
- WebSocket connectivity
- Swagger documentation
- Error handling
- Performance metrics

### Manual Testing

1. **Swagger UI**: Visit http://localhost:5000 for interactive testing
2. **Health Check**: `curl http://localhost:5000/api/health/system`
3. **Correlation Test**: Send requests with `X-Correlation-ID` header
4. **WebSocket Test**: Use browser developer tools or WebSocket client

## Logging Configuration

### Log Levels

- **DEBUG**: Detailed diagnostic information
- **INFO**: General operational information
- **WARNING**: Warning conditions
- **ERROR**: Error conditions
- **CRITICAL**: Critical conditions requiring immediate attention

### Log Destinations

- **Console**: Real-time log output
- **Files**: Persistent log storage in `/app/logs/`
- **Redis**: Optional log streaming for real-time monitoring

### Log Format

```json
{
  "timestamp": "2024-01-15T10:30:45.123456Z",
  "service": "api_gateway_service",
  "level": "INFO",
  "correlation_id": "req_12345678",
  "message": "API request completed successfully",
  "business_event": "api_request_success",
  "endpoint": "/api/health/system",
  "method": "GET",
  "duration_ms": 45.67,
  "client_ip": "192.168.1.100"
}
```

## Troubleshooting

### Common Issues

1. **Service Won't Start**
   ```bash
   # Check logs
   docker-compose logs traffic-monitor
   
   # Verify dependencies
   docker-compose ps redis postgres
   ```

2. **Correlation IDs Not Working**
   - Verify `CORRELATION_HEADER` environment variable
   - Check client sends correct header name
   - Validate logging configuration

3. **WebSocket Connection Issues**
   - Check firewall settings
   - Verify SocketIO client compatibility
   - Test with simple WebSocket client

4. **Performance Issues**
   - Monitor system resources in health endpoint
   - Check Redis connection performance
   - Review database query timing

### Debug Mode

Enable debug mode for detailed logging:

```bash
# Docker deployment
docker-compose up traffic-monitor -e API_DEBUG=true

# Standalone deployment
API_DEBUG=true python edge_api_gateway_enhanced.py
```

### Log Analysis

Search logs for specific correlation IDs:

```bash
# Docker logs
docker-compose logs traffic-monitor | grep "req_12345678"

# File logs
grep "req_12345678" /app/logs/api_gateway_service.log
```

## Security Considerations

1. **CORS Configuration**: Review allowed origins for production
2. **Rate Limiting**: Consider implementing rate limiting for production
3. **Authentication**: Add authentication middleware as needed
4. **Input Validation**: Validate all API inputs
5. **Log Sanitization**: Ensure sensitive data isn't logged

## Performance Optimization

1. **Redis Connection Pooling**: Use connection pooling for high load
2. **Response Caching**: Cache frequent API responses
3. **Request Compression**: Enable gzip compression
4. **Database Query Optimization**: Optimize data retrieval queries
5. **WebSocket Scaling**: Use Redis adapter for WebSocket scaling

## Integration with Other Services

The enhanced API gateway integrates with all other enhanced services:

- **Radar Service**: Receives vehicle detection events
- **Vehicle Consolidator**: Provides processed vehicle data
- **Weather Services**: Aggregates weather information
- **Camera Service**: Handles image data and AI results
- **Database Services**: Queries historical data

All integrations maintain correlation tracking for end-to-end observability.

## Monitoring and Alerting

Set up monitoring for:

1. **API Response Times**: Alert if average > 1000ms
2. **Error Rates**: Alert if error rate > 5%
3. **System Resources**: Alert if CPU > 80% or Memory > 85%
4. **Service Dependencies**: Alert if Redis or database unavailable
5. **Correlation Success**: Alert if correlation tracking < 90%

## Backup and Recovery

1. **Configuration Backup**: Version control all configuration files
2. **Log Retention**: Implement log rotation and archival
3. **Health Data**: Monitor and backup system health trends
4. **Service Recovery**: Implement automatic service restart policies

This enhanced API gateway provides the foundation for comprehensive traffic monitoring system observability and API access.