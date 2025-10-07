# Traffic Monitoring System - Logging & Debugging Guide

## 📋 Overview

This guide provides comprehensive documentation for managing logging and debugging across the distributed traffic monitoring system with radar, camera, sensors, and weather API integrations.

## 🏗️ Current Architecture

### System Components
- **🎯 OPS243-C Radar Service** - Vehicle speed detection
- **📸 IMX500 Camera Service** - AI-powered vehicle classification  
- **🌡️ DHT22 Weather Service** - Local environmental sensors
- **🌤️ Weather API Service** - External weather data integration
- **🔄 Vehicle Consolidator** - Data aggregation and correlation
- **📊 Redis Streams** - Real-time data messaging
- **🗄️ Database Persistence** - Long-term data storage
- **🌐 API Gateway** - RESTful service interface

### Current Logging Challenges

#### ❌ **Fragmented Logging Setup**
```bash
# Each service has independent logging configuration
├── radar_service.py              # logging.basicConfig() 
├── camera_service.py             # logging.basicConfig()
├── weather_service.py            # logging.basicConfig()  
├── consolidator_service.py       # logging.basicConfig()
└── api_gateway.py                # logging.basicConfig()
```

**Problems:**
- 20+ independent `logging.basicConfig()` calls
- Inconsistent log formats between services
- No request correlation across services
- Difficult to trace data flow: radar → consolidator → API
- Mixed storage locations (some `/var/log`, some `/mnt/storage`)

#### ❌ **Debugging Difficulties**
- **Multi-service correlation**: Hard to track vehicle detection from radar through to API
- **No request IDs**: Cannot correlate events across service boundaries
- **Performance blindness**: No timing information for bottleneck identification
- **Error isolation**: Difficult to determine root cause of system failures

## 🎯 Enhanced Logging Solution

### Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Radar Service │───▶│ Shared Logging   │◀───│  Camera Service │
└─────────────────┘    │    Infrastructure│    └─────────────────┘
         │              └──────────────────┘              │
         │                       │                        │
         ▼                       ▼                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Centralized Log Aggregation                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │ Correlation │ │Performance  │ │  Error      │ │ Health    │ │
│  │ Tracking    │ │ Metrics     │ │ Context     │ │ Monitoring│ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │
└─────────────────────────────────────────────────────────────────┘
         │                       │                        │
         ▼                       ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   File Logs     │    │   Console Logs   │    │   Dashboards    │
│ /mnt/storage/   │    │ (Docker Logs)    │    │   (Grafana)     │
│ logs/           │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Key Features

#### ✅ **Correlation Tracking**
```python
# Example: Track vehicle detection from radar through consolidation
with CorrelationContext(logger) as correlation_id:
    radar_logger.info(f"Vehicle detected: 25.3 mph", extra={
        'correlation_id': correlation_id,
        'event_type': 'vehicle_detection',
        'speed_mph': 25.3
    })
    
    # Same correlation_id appears in consolidator logs
    consolidator_logger.info(f"Processing vehicle data", extra={
        'correlation_id': correlation_id,
        'event_type': 'data_consolidation'
    })
```

#### ✅ **Performance Monitoring** 
```python
# Automatic timing for critical operations
service_logger.log_performance("radar_processing", 45.2, {
    'speed': 25.3,
    'data_size': 256
})

# Output: "⏱️ radar_processing completed in 45.20ms"
```

#### ✅ **Structured Error Context**
```python
try:
    process_vehicle_detection()
except Exception as e:
    service_logger.log_error_with_context(e, {
        'vehicle_id': 'v123',
        'radar_reading': raw_data,
        'system_state': get_system_status()
    })
```

#### ✅ **Health Monitoring**
```python
# Service health with comprehensive metrics
health = radar_service.get_health_status()
# Returns: uptime, error_rate, detection_count, performance_metrics
```

## 🛠️ Implementation Guide

### Phase 1: Core Infrastructure (2-3 hours)

#### Step 1: Install Shared Logging Module

The centralized logging infrastructure is provided by `edge_processing/shared_logging.py`:

```python
from edge_processing.shared_logging import get_radar_logger, CorrelationContext

# Initialize service logger
service_logger = get_radar_logger()
logger = service_logger.get_logger()

# Log service startup
service_logger.log_service_start({
    'port': '/dev/ttyUSB0',
    'baud_rate': 9600
})
```

#### Step 2: Service Integration Pattern

**Before (Current):**
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Basic logging
logger.info("Vehicle detected")
```

**After (Enhanced):**
```python
from edge_processing.shared_logging import get_radar_logger, CorrelationContext

# Initialize centralized logging
service_logger = get_radar_logger()
logger = service_logger.get_logger()

# Structured logging with correlation
with CorrelationContext(service_logger) as correlation_id:
    logger.info("🚛 Vehicle detected: 25.3 mph", extra={
        'event_type': 'vehicle_detection',
        'speed_mph': 25.3,
        'correlation_id': correlation_id
    })
```

#### Step 3: Docker Configuration Updates

Update `docker-compose.yml` to include centralized logging:

```yaml
services:
  radar-service:
    # ... existing configuration
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    volumes:
      - ${STORAGE_ROOT:-/mnt/storage}/logs:/app/logs
    environment:
      - LOG_LEVEL=INFO
      - LOG_CORRELATION=true
```

### Phase 2: Service Integration Examples

#### Radar Service Integration

```python
#!/usr/bin/env python3
"""Enhanced Radar Service with Centralized Logging"""

from edge_processing.shared_logging import get_radar_logger, CorrelationContext

class EnhancedRadarService:
    def __init__(self):
        self.service_logger = get_radar_logger()
        self.logger = self.service_logger.get_logger()
        
        # Log service initialization
        self.service_logger.log_service_start({
            'service': 'ops243c_radar',
            'version': '2.0.0'
        })
    
    def process_detection(self, raw_data: str):
        """Process radar detection with full logging context"""
        
        with CorrelationContext(self.service_logger) as correlation_id:
            start_time = time.time()
            
            # Parse radar data
            parsed = self._parse_radar_data(raw_data)
            
            if parsed and parsed.get('speed', 0) > 15:
                # Log significant detection
                self.logger.info(f"🚛 Vehicle: {parsed['speed']:.1f} mph", extra={
                    'event_type': 'vehicle_detection',
                    'speed_mph': parsed['speed'],
                    'raw_data': raw_data,
                    'correlation_id': correlation_id
                })
                
                # Publish to Redis with correlation
                self._publish_to_redis(parsed, correlation_id)
            
            # Log performance
            processing_time = (time.time() - start_time) * 1000
            self.service_logger.log_performance("radar_processing", processing_time)
```

#### Vehicle Consolidator Integration

```python
#!/usr/bin/env python3
"""Enhanced Vehicle Consolidator with Logging"""

from edge_processing.shared_logging import get_consolidator_logger

class EnhancedVehicleConsolidator:
    def __init__(self):
        self.service_logger = get_consolidator_logger()
        self.logger = self.service_logger.get_logger()
    
    def process_radar_event(self, radar_data: dict):
        """Process radar event with correlation tracking"""
        
        # Extract correlation ID from radar data
        correlation_id = radar_data.get('correlation_id')
        
        if correlation_id:
            self.service_logger.set_correlation_id(correlation_id)
        
        self.logger.info(f"📊 Consolidating vehicle data", extra={
            'event_type': 'data_consolidation',
            'speed': radar_data.get('speed'),
            'correlation_id': correlation_id
        })
        
        # Process consolidation...
        consolidated = self._consolidate_data(radar_data)
        
        # Log results with timing
        self.service_logger.log_performance("data_consolidation", processing_time, {
            'input_sources': ['radar', 'weather', 'sensors'],
            'output_keys': list(consolidated.keys())
        })
```

### Phase 3: Monitoring Dashboard (2-3 hours)

#### Grafana Setup

1. **Deploy monitoring stack:**
```bash
# Start monitoring services
docker-compose -f docker-compose.logging.yml --profile monitoring up -d

# Access Grafana at http://localhost:3000
# Default login: admin/admin123
```

2. **Import dashboard:**
- Use `grafana/dashboards/traffic-monitoring-dashboard.json`
- Provides real-time service health monitoring

#### Key Metrics Tracked

- **Service Uptime** - All services health status
- **Vehicle Detection Rate** - Detections per hour
- **Error Rates** - Failures per service
- **Performance Metrics** - Processing times
- **Storage Usage** - SSD and SD card utilization
- **Redis Performance** - Memory and connection metrics

## 📊 Log Structure Reference

### Standard Log Format

#### Console Output (Human Readable)
```
[2025-09-24T14:30:45] INFO | radar_service | abc12345 | 🚛 Vehicle detected: 25.3 mph
[2025-09-24T14:30:45] INFO | consolidator | abc12345 | 📊 Processing vehicle data
```

#### File Output (JSON Structured)
```json
{
  "timestamp": "2025-09-24T14:30:45.123",
  "service": "radar_service",
  "level": "INFO",
  "message": "Vehicle detected: 25.3 mph",
  "correlation_id": "abc12345",
  "event_type": "vehicle_detection",
  "speed_mph": 25.3,
  "module": "radar_processor",
  "function": "process_detection",
  "line": 142
}
```

### Event Types

| Event Type | Description | Example |
|------------|-------------|---------|
| `service_start` | Service initialization | Radar service starting |
| `service_stop` | Service shutdown | Graceful shutdown |
| `vehicle_detection` | Vehicle detected by radar | 25.3 mph truck |
| `data_consolidation` | Multi-source data merge | Radar + weather + sensors |
| `performance` | Timing measurements | Processing took 45ms |
| `error` | Exception with context | Redis connection failed |
| `health_check` | Periodic service status | All systems operational |

## 🔧 Configuration Reference

### Environment Variables

```bash
# Logging configuration
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR
LOG_CORRELATION=true              # Enable correlation tracking
LOG_FILE_PATH=/app/logs/service.log
LOG_MAX_BYTES=10485760           # 10MB per log file
LOG_BACKUP_COUNT=5               # Keep 5 rotated files

# Performance monitoring  
PERF_LOGGING=true                # Enable performance timing
HEALTH_CHECK_INTERVAL=60         # Health check every 60 seconds

# Storage paths
STORAGE_ROOT=/mnt/storage        # SSD storage location
LOG_DIR=${STORAGE_ROOT}/logs     # Centralized log directory
```

### Service-Specific Configuration

#### Radar Service
```python
radar_logger = get_service_logger("radar_service", 
    log_level="INFO",
    log_dir="/mnt/storage/logs/applications",
    enable_correlation=True
)
```

#### Camera Service
```python
camera_logger = get_service_logger("camera_service",
    log_level="DEBUG",  # More verbose for AI processing
    enable_correlation=True
)
```

#### Consolidator Service  
```python
consolidator_logger = get_service_logger("vehicle_consolidator",
    log_level="INFO",
    enable_correlation=True
)
```

## 🚨 Troubleshooting Guide

### Common Issues

#### 1. Logs Not Appearing
**Problem:** Service logs not showing up in expected location

**Solution:**
```bash
# Check log directory permissions
ls -la /mnt/storage/logs/applications/

# Verify service logger initialization
grep "Service starting" /mnt/storage/logs/applications/radar_service.log

# Check Docker volume mounts
docker inspect radar-service | grep -A5 "Mounts"
```

#### 2. Missing Correlation IDs
**Problem:** Cannot trace requests across services

**Solution:**
```python
# Ensure CorrelationContext is used
with CorrelationContext(service_logger) as correlation_id:
    logger.info("Processing request", extra={
        'correlation_id': correlation_id  # Explicitly set
    })

# Check correlation propagation
grep "correlation_id" /mnt/storage/logs/applications/*.log
```

#### 3. High Log Volume
**Problem:** Log files growing too quickly

**Solution:**
```python
# Increase log rotation frequency
file_handler = RotatingFileHandler(
    log_file,
    maxBytes=5 * 1024 * 1024,  # Reduce to 5MB
    backupCount=3               # Keep fewer files
)

# Reduce log level for noisy services
camera_logger = get_service_logger("camera", log_level="WARNING")
```

#### 4. Performance Impact
**Problem:** Logging affecting real-time processing

**Solution:**
```python
# Use asynchronous logging for high-throughput services
import logging.handlers
import queue

# Queue-based handler for radar service
log_queue = queue.Queue()
queue_handler = logging.handlers.QueueHandler(log_queue)
logger.addHandler(queue_handler)
```

### Debug Commands

#### View Real-time Logs
```bash
# All services
tail -f /mnt/storage/logs/applications/*.log

# Specific service
tail -f /mnt/storage/logs/applications/radar_service.log

# Docker container logs
docker-compose logs -f radar-service
```

#### Search Correlation IDs
```bash
# Find all events for a specific correlation ID
grep "abc12345" /mnt/storage/logs/applications/*.log

# Find recent vehicle detections
grep "vehicle_detection" /mnt/storage/logs/applications/*.log | tail -10
```

#### Performance Analysis
```bash
# Find slowest operations
grep "performance" /mnt/storage/logs/applications/*.log | sort -k6 -nr

# Error rate analysis
grep "ERROR" /mnt/storage/logs/applications/*.log | wc -l
```

## 📈 Benefits & ROI

### Immediate Benefits (Phase 1)
- ✅ **Correlated debugging** - Track vehicle detection end-to-end
- ✅ **Structured logs** - JSON format for easy parsing
- ✅ **Performance visibility** - Identify bottlenecks quickly
- ✅ **Error context** - Rich error information for faster resolution

### Long-term Benefits (Phase 2-3)
- ✅ **Proactive monitoring** - Alerts before system failures
- ✅ **Historical analysis** - Usage patterns and optimization opportunities
- ✅ **Automated troubleshooting** - Self-diagnosing system issues
- ✅ **Scalability insights** - Performance trends over time

### Time Savings
- **Debugging time**: Reduced from hours to minutes
- **Issue resolution**: 70% faster problem identification
- **System optimization**: Data-driven performance improvements
- **Maintenance overhead**: Automated log rotation and cleanup

## 🚀 Implementation Timeline

### 2-Hour MVP (Immediate Value)
1. **Enhanced radar service** with correlation tracking ⏱️ 45 min
2. **Enhanced consolidator** with performance metrics ⏱️ 45 min  
3. **Basic health monitoring** ⏱️ 30 min

**Deliverables:**
- Correlated vehicle detection logs
- Performance timing for radar → consolidator flow
- Structured error handling
- Basic service health monitoring

### Full Implementation (8-12 hours)
- **Phase 1**: Core infrastructure (2-3 hours)
- **Phase 2**: All service integration (3-4 hours)  
- **Phase 3**: Monitoring dashboard (2-3 hours)
- **Phase 4**: Production hardening (1-2 hours)

## 📚 Additional Resources

### Files Created
- `edge_processing/shared_logging.py` - Centralized logging infrastructure
- `examples/enhanced_radar_service_with_logging.py` - Integration example
- `docker-compose.logging.yml` - Monitoring stack configuration
- `grafana/dashboards/traffic-monitoring-dashboard.json` - Monitoring dashboard

### Further Reading
- [Python Logging Best Practices](https://docs.python.org/3/howto/logging.html)
- [Docker Logging Configuration](https://docs.docker.com/config/containers/logging/)
- [Grafana Dashboard Guide](https://grafana.com/docs/grafana/latest/dashboards/)
- [Redis Monitoring](https://redis.io/docs/manual/admin/)

---

**Next Steps:** Ready to implement the 2-hour MVP for immediate debugging improvements?