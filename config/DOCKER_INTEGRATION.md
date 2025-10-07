# Docker Configuration Guide

## Overview

The centralized configuration system is **fully compatible** with Docker containers running on **Raspberry Pi 5**. This guide explains how configuration works in containerized environments and how to manage it.

## Raspberry Pi 5 Deployment

This system is designed to run on **Raspberry Pi 5** with Docker containers managing all services:

- ✅ **ARM64 architecture** - Built with `python:3.11-slim-bookworm` base image
- ✅ **Hardware access** - GPIO, I2C, UART passthrough to containers
- ✅ **Host-Container hybrid** - IMX500 camera runs on host, containers process data
- ✅ **Configuration validated** - All paths, GPIO pins, and hardware checked on startup

## How It Works in Docker

### 1. Configuration Module in Container

The `config/` directory is copied into the Docker image during build:

```dockerfile
# From Dockerfile
WORKDIR /app
COPY --chown=merk:merk . /app/
ENV PYTHONPATH=/app
```

This means:
- ✅ `config` module is available at `/app/config/`
- ✅ `from config import get_config` works everywhere
- ✅ Configuration loads from container environment variables

### 2. Environment Variables via Docker Compose

Docker Compose passes environment variables to containers:

```yaml
services:
  traffic-monitor:
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - DATABASE_PATH=/app/data/traffic_data.db
      - LOG_LEVEL=INFO
```

The config system reads these with `os.getenv()` and validates them automatically.

### 3. Backward Compatibility

**During migration**, both methods work simultaneously:

```python
# OLD CODE (still works)
REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')

# NEW CODE (recommended)
from config import get_config
config = get_config()
redis_host = config.redis.host
```

This allows **gradual migration** without breaking existing services.

## Quick Start for Docker

### 1. Build Image on Raspberry Pi 5

```bash
# Build on Pi (native ARM64)
docker build -t traffic-monitor:latest .

# Or pull pre-built image
docker pull gcumerk/cst590-capstone-public:latest
```

**Important**: Build on Pi or use multi-arch images. The config module works on any architecture.

### 2. Run with Environment Variables

**Option A: Using docker-compose.yml**

```yaml
services:
  your-service:
    image: your-image:latest
    environment:
      - ENVIRONMENT=production
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - DATABASE_PATH=/app/data/traffic_data.db
      - LOG_LEVEL=INFO
```

**Option B: Using .env file**

```bash
# Create .env file (not committed)
cp .env.template .env
nano .env

# Docker Compose automatically loads .env
docker-compose up -d
```

**Option C: Command line**

```bash
docker run -e REDIS_HOST=redis -e LOG_LEVEL=INFO your-image:latest
```

### 3. Verify Configuration in Container

```bash
# Test config loading
docker exec traffic-monitor python config/test_docker.py

# Check config interactively
docker exec -it traffic-monitor python -c "
from config import get_config
config = get_config()
print(f'Redis: {config.redis.host}:{config.redis.port}')
print(f'Environment: {config.environment}')
"
```

## Configuration in Different Deployment Modes

### Development (Local Docker)

```yaml
# docker-compose.override.yml
services:
  traffic-monitor:
    environment:
      - ENVIRONMENT=development
      - API_DEBUG=true
      - LOG_LEVEL=DEBUG
      - REDIS_HOST=localhost
```

### Production (Pi + Docker)

```yaml
# docker-compose.yml - Running on Raspberry Pi 5
services:
  traffic-monitor:
    environment:
      - ENVIRONMENT=production
      - API_DEBUG=false
      - LOG_LEVEL=INFO
      - SECRET_KEY=${SECRET_KEY}  # From .env
      - JWT_SECRET=${JWT_SECRET}  # From .env
      
      # Pi-specific hardware paths
      - RADAR_UART_PORT=/dev/ttyAMA0
      - DHT22_GPIO_PIN=4
      
      # Storage on external SSD
      - DATABASE_PATH=/mnt/storage/database/traffic_data.db
      - CAMERA_CAPTURE_DIR=/mnt/storage/camera_capture
```

**Pi-Specific Notes**:
- Hardware devices (`/dev/ttyAMA0`, GPIO pins) must match your Pi configuration
- Use external SSD at `/mnt/storage` for better performance and SD card longevity
- IMX500 camera runs on host, containers process images from shared volume

### Testing (CI/CD)

```yaml
# docker-compose.test.yml
services:
  test-service:
    environment:
      - ENVIRONMENT=testing
      - DATABASE_PATH=:memory:
      - LOG_LEVEL=WARNING
      - REDIS_HOST=redis-test
```

## Service Migration Strategy

### Phase 1: Infrastructure Ready (✅ Complete)
- Configuration module created
- Docker compatibility verified
- Documentation written

### Phase 2: Service Migration (In Progress)
Each service is migrated one at a time:

**Before Migration:**
```python
# radar_service.py
import os
REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
```

**After Migration:**
```python
# radar_service.py
from config import get_config
config = get_config()
redis_host = config.redis.host
redis_port = config.redis.port
```

**Docker Compose (no change needed!):**
```yaml
# Same environment variables work for both old and new code
environment:
  - REDIS_HOST=redis
  - REDIS_PORT=6379
```

### Phase 3: Cleanup
After all services migrated:
- Remove duplicate default values in code
- Remove redundant os.environ.get() calls
- Keep environment variables in docker-compose.yml

## Validation in Containers

### Automatic Validation on Startup

Add validation to your service entrypoint:

```python
#!/usr/bin/env python3
from config import get_config
import sys

# Load and validate configuration
config = get_config()
errors = config.validate()

if errors:
    print("❌ Configuration errors:")
    for error in errors:
        print(f"  - {error}")
    
    if config.environment == "production":
        print("Cannot start in production with configuration errors")
        sys.exit(1)

print(f"✅ Configuration valid: {config.environment} environment")

# Start your service...
```

### Health Check with Config

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s \
    CMD python -c "from config import get_config; get_config()" || exit 1
```

## Common Docker Scenarios

### 1. Override Config for One Service

```yaml
services:
  radar-service:
    environment:
      - RADAR_SPEED_UNITS=kph  # Override just for this service
      - LOG_LEVEL=DEBUG         # Debug only radar
  
  camera-service:
    environment:
      - LOG_LEVEL=INFO          # Normal logging for others
```

### 2. Share Config Across Services

```yaml
# Use YAML anchors for common config
x-common-env: &common-env
  ENVIRONMENT: production
  REDIS_HOST: redis
  REDIS_PORT: 6379
  LOG_LEVEL: INFO

services:
  service1:
    environment:
      <<: *common-env
  
  service2:
    environment:
      <<: *common-env
```

### 3. Mount Custom Config File

```yaml
services:
  traffic-monitor:
    volumes:
      - ./custom-config.py:/app/config/custom_settings.py:ro
```

### 4. Multi-Environment with Same Image

```yaml
# Development
services:
  app:
    image: myapp:v1.0
    environment:
      - ENVIRONMENT=development
      - API_DEBUG=true

# Production (same image!)
services:
  app:
    image: myapp:v1.0
    environment:
      - ENVIRONMENT=production
      - API_DEBUG=false
```

## Raspberry Pi 5 Specific Configuration

### Hardware Device Access

The configuration system validates hardware paths, but Docker must have device access:

```yaml
# docker-compose.yml
services:
  radar-service:
    devices:
      - /dev/ttyAMA0:/dev/ttyAMA0  # UART for radar
    environment:
      - RADAR_UART_PORT=/dev/ttyAMA0
      - RADAR_BAUD_RATE=19200
  
  weather-service:
    devices:
      - /dev/gpiomem:/dev/gpiomem  # GPIO for DHT22
    privileged: false  # gpiomem avoids need for privileged
    environment:
      - DHT22_GPIO_PIN=4
```

### IMX500 Camera Integration

The system uses a **host-container hybrid** architecture:

**On Pi Host:**
```bash
# Host service captures images with full hardware access
sudo systemctl start imx500-ai-capture.service
```

**In Container:**
```python
# Containers process images from shared volume
from config import get_config
config = get_config()

# Images written by host, read by container
capture_dir = config.camera.capture_dir
# Example: /mnt/storage/camera_capture
```

**docker-compose.yml:**
```yaml
services:
  traffic-monitor:
    volumes:
      - ${STORAGE_ROOT}/camera_capture:/app/camera_capture
    environment:
      - CAMERA_CAPTURE_DIR=/app/camera_capture
```

### Storage Configuration for Pi

**Best Practice**: Use external SSD for Docker volumes:

```yaml
# docker-compose.yml
services:
  traffic-monitor:
    volumes:
      - /mnt/storage/camera_capture:/app/camera_capture
      - /mnt/storage/data:/app/data
      - /mnt/storage/logs:/app/logs
    environment:
      - DATABASE_PATH=/app/data/traffic_data.db
      - LOG_DIR=/app/logs
```

**Why?**
- SD card has limited write cycles
- SSD provides better performance
- Database writes won't wear out SD card

### Verifying Pi Configuration

**Test on Raspberry Pi 5:**

```bash
# 1. Verify Docker is running
docker info | grep "Operating System"
# Should show: Raspbian GNU/Linux 12 (bookworm)

# 2. Test config in container
docker-compose run --rm traffic-monitor python config/test_docker.py

# 3. Check hardware device access
docker-compose run --rm radar-service ls -l /dev/ttyAMA0
docker-compose run --rm weather-service ls -l /dev/gpiomem

# 4. Verify storage mounts
docker-compose run --rm traffic-monitor df -h /app/data
```

### Pi Performance Tuning

Adjust configuration for Pi 5 performance:

```bash
# .env file for Pi 5
# Optimize for 8GB RAM, quad-core ARM Cortex-A76

# API Gateway
API_WORKERS=2  # Fewer workers than x86

# Database
BATCH_SIZE=50  # Smaller batches for limited memory
COMMIT_INTERVAL_SEC=60  # Less frequent commits

# Maintenance
MAINTENANCE_IMAGE_MAX_AGE_HOURS=12  # More aggressive cleanup
MAINTENANCE_MAX_LIVE_IMAGES=200  # Lower limit for storage

# Camera
MAX_STORED_IMAGES=50  # Fewer cached images
CAPTURE_INTERVAL=2.0  # Slower capture rate if needed
```

## Troubleshooting in Docker

### Problem: "Module config not found"

**Check:**
```bash
# Is PYTHONPATH set?
docker exec traffic-monitor env | grep PYTHONPATH

# Does /app/config exist?
docker exec traffic-monitor ls -la /app/config/

# Can Python find it?
docker exec traffic-monitor python -c "import sys; print(sys.path)"
```

**Solution:**
```dockerfile
# Add to Dockerfile if missing
ENV PYTHONPATH=/app
```

### Problem: "Configuration validation failed"

**Check:**
```bash
# What environment variables are set?
docker exec traffic-monitor python config/test_docker.py

# What's the actual config?
docker exec traffic-monitor python -c "
from config import get_config
import os
print('REDIS_HOST env:', os.getenv('REDIS_HOST'))
config = get_config()
print('REDIS_HOST config:', config.redis.host)
"
```

**Solution:**
- Check `docker-compose.yml` has correct environment variables
- Check `.env` file exists and is valid
- Run `docker-compose config` to see interpolated values

### Problem: "Environment variable not being used"

**Check:**
```bash
# Is the variable in docker-compose.yml?
docker-compose config | grep REDIS_HOST

# Is it reaching the container?
docker exec traffic-monitor env | grep REDIS_HOST

# Is config reading it?
docker exec traffic-monitor python -c "
from config import get_config
config = get_config()
print(config.redis.host)
"
```

**Solution:**
```yaml
# Add to docker-compose.yml
environment:
  - REDIS_HOST=redis  # Must be explicitly listed
```

### Problem: "Hardware device not accessible" (Pi-specific)

**Check:**
```bash
# Does device exist on host?
ls -l /dev/ttyAMA0
ls -l /dev/gpiomem

# Is it passed to container?
docker-compose config | grep devices -A 5

# Container can see it?
docker exec radar-service ls -l /dev/ttyAMA0
```

**Solution:**
```yaml
# docker-compose.yml
services:
  radar-service:
    devices:
      - /dev/ttyAMA0:/dev/ttyAMA0
  
  weather-service:
    devices:
      - /dev/gpiomem:/dev/gpiomem
```

### Problem: "Permission denied on GPIO/UART"

**Solution 1: Use device groups**
```yaml
services:
  weather-service:
    devices:
      - /dev/gpiomem:/dev/gpiomem
    group_add:
      - gpio
      - i2c
```

**Solution 2: Verify host permissions**
```bash
# On Pi host
sudo usermod -a -G gpio,i2c,dialout merk
ls -l /dev/gpiomem  # Should show group 'gpio'
ls -l /dev/ttyAMA0  # Should show group 'dialout'
```

### Problem: "SD card filling up"

**Check:**
```bash
# Check disk usage
df -h /
docker system df

# Check container logs size
docker logs traffic-monitor 2>&1 | wc -l
```

**Solution:**
```yaml
# docker-compose.yml - Use external SSD
services:
  traffic-monitor:
    volumes:
      - /mnt/storage/data:/app/data  # SSD, not SD
    environment:
      - DATABASE_PATH=/app/data/traffic_data.db
      - LOG_DIR=/mnt/storage/logs
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### Problem: "Container OOM (Out of Memory)" (Pi-specific)

**Check:**
```bash
# Container memory usage
docker stats --no-stream

# Pi total memory
free -h
```

**Solution:**
```yaml
# docker-compose.yml - Set memory limits
services:
  traffic-monitor:
    mem_limit: 512m
    environment:
      - BATCH_SIZE=25  # Reduce batch size
      - MAX_STORED_IMAGES=25  # Lower limits
```

### Problem: "Secrets not loading"

**Security:** Never put secrets directly in docker-compose.yml!

**Solution 1: Use .env file**
```bash
# .env (not committed)
SECRET_KEY=your-secure-secret-here
JWT_SECRET=your-jwt-secret-here

# docker-compose.yml
environment:
  - SECRET_KEY=${SECRET_KEY}
  - JWT_SECRET=${JWT_SECRET}
```

**Solution 2: Use Docker secrets** (Swarm mode)
```yaml
secrets:
  secret_key:
    external: true

services:
  app:
    secrets:
      - secret_key
```

## Testing Configuration Changes

### 1. Test Locally

```bash
# Set test environment variables
export REDIS_HOST=localhost
export LOG_LEVEL=DEBUG

# Test config loads
python -c "from config import get_config; print(get_config().redis.host)"
```

### 2. Test in Container

```bash
# Rebuild with new config
docker-compose build

# Test config loading
docker-compose run --rm traffic-monitor python config/test_docker.py

# Check specific values
docker-compose run --rm traffic-monitor python -c "
from config import get_config
config = get_config()
print(f'Environment: {config.environment}')
print(f'Redis: {config.redis.host}')
print(f'Log Level: {config.logging.level}')
"
```

### 3. Test with Different Environments

```bash
# Development
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Testing
docker-compose -f docker-compose.test.yml run --rm test-suite
```

## Best Practices

### ✅ Do:

1. **Use .env for local secrets** (not committed)
2. **Set ENVIRONMENT explicitly** in docker-compose.yml
3. **Use same variable names** in docker-compose.yml as .env.template
4. **Test config loading** before deploying
5. **Use docker-compose.override.yml** for local development overrides

### ❌ Don't:

1. **Commit .env files** with secrets
2. **Hardcode secrets** in docker-compose.yml
3. **Mix old and new config** in same file (migrate completely)
4. **Skip validation** in production containers
5. **Assume defaults** - always set critical values explicitly

## Migration Checklist

When migrating a service to use centralized config:

- [ ] Service code imports `from config import get_config`
- [ ] All `os.environ.get()` replaced with `config.category.setting`
- [ ] docker-compose.yml has required environment variables
- [ ] .env.template documents the variables used
- [ ] Service starts without errors: `docker-compose up service-name`
- [ ] Config validation passes: `docker exec service python config/test_docker.py`
- [ ] Health check still works
- [ ] Logs show correct configuration values

## Example: Complete Service Migration

**Before:**
```python
# radar_service.py
import os
import redis

REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
UART_PORT = os.environ.get('RADAR_UART_PORT', '/dev/ttyAMA0')

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
```

**After:**
```python
# radar_service.py
from config import get_config
import redis

# Load configuration
config = get_config()

# Use validated, typed configuration
redis_client = redis.Redis(
    host=config.redis.host,
    port=config.redis.port,
    db=config.redis.db,
    socket_timeout=config.redis.socket_timeout
)

# Radar config
uart_port = config.radar.uart_port
baud_rate = config.radar.baud_rate
```

**docker-compose.yml (no change!):**
```yaml
services:
  radar-service:
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - RADAR_UART_PORT=/dev/ttyAMA0
      - RADAR_BAUD_RATE=19200
```

## Next Steps

1. **Test the config system on Pi**: Run `docker-compose run --rm traffic-monitor python config/test_docker.py`
2. **Verify hardware access**: Check GPIO, UART devices are accessible
3. **Migrate one service**: Start with a simple service like radar or weather
4. **Test on Pi hardware**: Verify actual hardware (radar, DHT22) works with config
5. **Migrate remaining services**: One at a time, testing each on Pi
6. **Update documentation**: Keep track of what's been migrated

## Raspberry Pi 5 Deployment Checklist

Before deploying to Pi with new configuration system:

### Pre-Deployment
- [ ] **Build or pull Docker image** on Pi
- [ ] **Create .env file**: `cp .env.template .env`
- [ ] **Generate secrets**: `python config/generate_secrets.py >> .env`
- [ ] **Edit .env**: Set Pi-specific paths and hardware pins
- [ ] **Verify storage**: External SSD mounted at `/mnt/storage`
- [ ] **Set permissions**: User `merk` has access to GPIO, UART

### Configuration Validation
- [ ] **Test config loading**: `docker-compose run --rm traffic-monitor python config/test_docker.py`
- [ ] **Verify hardware paths**: GPIO pin 4, UART `/dev/ttyAMA0` exist
- [ ] **Check storage paths**: `/mnt/storage` writable by containers
- [ ] **Validate secrets**: SECRET_KEY and JWT_SECRET set in .env

### Service Testing
- [ ] **Start Redis**: `docker-compose up -d redis`
- [ ] **Test API Gateway**: `docker-compose up -d traffic-monitor`
- [ ] **Test Radar Service**: Verify UART connection
- [ ] **Test Weather Service**: Verify GPIO/DHT22 readings
- [ ] **Test Camera Integration**: Host captures, container processes
- [ ] **Check logs**: All services logging correctly

### Production Readiness
- [ ] **Environment set**: `ENVIRONMENT=production` in .env
- [ ] **Debug disabled**: `API_DEBUG=false`
- [ ] **Secrets validated**: No default/placeholder values
- [ ] **Monitoring enabled**: Health checks passing
- [ ] **Backup configured**: Database backup schedule set
- [ ] **Storage monitored**: Disk usage alerts configured

### Post-Deployment
- [ ] **Monitor for 24h**: Check logs, CPU, memory, disk
- [ ] **Verify data collection**: Database receiving records
- [ ] **Test API endpoints**: All endpoints responding
- [ ] **Check maintenance**: Cleanup running, disk not filling
- [ ] **Document issues**: Note any Pi-specific quirks

## Pi-Specific Configuration Tips

### Optimizing for Pi 5

```bash
# .env optimized for Raspberry Pi 5 (8GB model)

# System
ENVIRONMENT=production
TIMEZONE=America/Phoenix

# API - Conservative for ARM
API_WORKERS=2
API_PORT=5000
API_DEBUG=false

# Database - Smaller batches for Pi
DATABASE_PATH=/mnt/storage/database/traffic_data.db
BATCH_SIZE=50
COMMIT_INTERVAL_SEC=60
RETENTION_DAYS=30

# Redis - Standard settings work well
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# Camera - Moderate capture rate
CAMERA_CAPTURE_DIR=/mnt/storage/camera_capture
CAPTURE_INTERVAL=1.5
AI_CONFIDENCE_THRESHOLD=0.5
MAX_STORED_IMAGES=50

# Radar - Pi GPIO/UART
RADAR_UART_PORT=/dev/ttyAMA0
RADAR_BAUD_RATE=19200
RADAR_SPEED_UNITS=mph

# Weather - Pi GPIO
DHT22_GPIO_PIN=4
DHT22_UPDATE_INTERVAL=600

# Maintenance - Aggressive for limited storage
MAINTENANCE_IMAGE_MAX_AGE_HOURS=12
MAINTENANCE_SNAPSHOT_MAX_AGE_HOURS=72
MAINTENANCE_MAX_LIVE_IMAGES=200
MAINTENANCE_WARNING_THRESHOLD=75.0
MAINTENANCE_EMERGENCY_THRESHOLD=85.0

# Logging
LOG_LEVEL=INFO
LOG_DIR=/mnt/storage/logs
```

### Hardware Compatibility

| Component | Configuration | Notes |
|-----------|--------------|-------|
| **IMX500 Camera** | Host service | Runs outside Docker with `rpicam-still` |
| **OPS243 Radar** | Container | UART via `/dev/ttyAMA0` device passthrough |
| **DHT22 Weather** | Container | GPIO via `/dev/gpiomem` (no privileged mode) |
| **Database** | Container | SQLite on external SSD (`/mnt/storage`) |
| **Redis** | Container | In-memory cache with persistence |
| **API Gateway** | Container | Port 5000 (internal), 443 via nginx |

## See Also

- [Configuration System README](README.md) - Complete configuration guide
- [Environment Template](.env.template) - All available variables
- [Migration Strategy](../documentation/DEPLOYMENT_NOTES.md) - Deployment notes
- [Docker Best Practices](../DOCKER_BEST_PRACTICES.md) - Docker guidelines
