# Configuration Management System

## Overview

The Vehicle Detection System uses a centralized configuration management system that provides:

- **Type Safety**: All configuration values are validated with proper types
- **Environment-Based**: Support for development, production, and testing environments
- **Centralized**: Single source of truth for all system settings
- **Well-Documented**: Clear descriptions and sensible defaults
- **Secure**: Secrets loaded from environment, never hardcoded

## Quick Start

### 1. Create Environment File

```bash
# Copy template
cp .env.template .env

# Generate secrets
python config/generate_secrets.py >> .env

# Edit with your specific values
nano .env  # or your preferred editor
```

### 2. Use in Code

```python
from config import get_config

# Get configuration instance
config = get_config()

# Access settings by category
redis_host = config.redis.host
redis_port = config.redis.port

db_path = config.database.path
api_port = config.api.port

# ROI coordinates for camera
roi_x = (config.camera.roi_x_start, config.camera.roi_x_end)
roi_y = (config.camera.roi_y_start, config.camera.roi_y_end)
```

## Configuration Structure

### System Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `production` | Environment: development, production, or testing |
| `LOCATION_ID` | `default_location` | Unique identifier for multi-site deployments |
| `TIMEZONE` | `America/Phoenix` | Timezone for all timestamps |

### Redis Configuration (`config.redis`)

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_HOST` | `redis` | Redis server hostname |
| `REDIS_PORT` | `6379` | Redis server port |
| `REDIS_DB` | `0` | Redis database index (0-15) |
| `REDIS_PASSWORD` | `None` | Redis authentication password (optional) |
| `REDIS_MAX_CONNECTIONS` | `50` | Maximum connection pool size |
| `DHT22_REDIS_KEY` | `weather:dht22` | Redis key for weather data |

**Validation**:
- Port must be 1-65535
- DB index must be 0-15

### Database Configuration (`config.database`)

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_PATH` | `/app/data/traffic_data.db` | SQLite database file path |
| `BATCH_SIZE` | `100` | Records per batch write |
| `COMMIT_INTERVAL_SEC` | `30` | Seconds between commits |
| `RETENTION_DAYS` | `90` | Days to keep historical data |

**Validation**:
- Batch size ≥ 1
- Commit interval ≥ 1 second
- Retention ≥ 1 day

### API Configuration (`config.api`)

| Variable | Default | Description |
|----------|---------|-------------|
| `API_HOST` | `0.0.0.0` | API server bind address |
| `API_PORT` | `5000` | API server port |
| `API_DEBUG` | `false` | Enable Flask debug mode |
| `API_WORKERS` | `4` | Number of worker processes |
| `SWAGGER_ENABLED` | `true` | Enable Swagger documentation |

**Validation**:
- Port must be 1-65535
- Workers ≥ 1

**Security Warning**: Never use `API_DEBUG=true` in production!

### Camera Configuration (`config.camera`)

| Variable | Default | Description |
|----------|---------|-------------|
| `CAMERA_CAPTURE_DIR` | `/mnt/storage/camera_capture` | Image storage directory |
| `IMX500_MODEL_PATH` | `/usr/share/imx500-models/...` | AI model file path |
| `CAPTURE_INTERVAL` | `1.0` | Seconds between captures |
| `AI_CONFIDENCE_THRESHOLD` | `0.5` | Minimum detection confidence (0.0-1.0) |
| `MAX_STORED_IMAGES` | `100` | Maximum images to retain |

**Region of Interest (ROI)**:

| Variable | Default | Description |
|----------|---------|-------------|
| `STREET_ROI_X_START` | `0.15` | Left edge (15% from left) |
| `STREET_ROI_X_END` | `0.85` | Right edge (85% from left) |
| `STREET_ROI_Y_START` | `0.5` | Top edge (50% from top) |
| `STREET_ROI_Y_END` | `0.9` | Bottom edge (90% from top) |

**Validation**:
- Confidence threshold 0.0-1.0
- Capture interval ≥ 0.1 seconds
- ROI coordinates 0.0-1.0, start < end

**Tuning ROI**: Adjust coordinates based on camera angle and target area. Use coordinate visualization tools to find optimal values.

### Radar Configuration (`config.radar`)

| Variable | Default | Description |
|----------|---------|-------------|
| `RADAR_UART_PORT` | `/dev/ttyAMA0` | Serial port device |
| `RADAR_BAUD_RATE` | `19200` | Serial baud rate |
| `RADAR_SPEED_UNITS` | `mph` | Speed units (mph, kph, mps) |

**Validation**:
- Baud rate must be standard value (9600, 19200, 38400, 57600, 115200)

### Weather Configuration (`config.weather`)

| Variable | Default | Description |
|----------|---------|-------------|
| `DHT22_GPIO_PIN` | `4` | GPIO pin number (BCM) |
| `DHT22_UPDATE_INTERVAL` | `600` | Seconds between readings (10 min) |

**Validation**:
- GPIO pin 1-27 (valid BCM pins)
- Update interval ≥ 60 seconds

### Logging Configuration (`config.logging`)

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `LOG_DIR` | `/var/log/vehicle-detection` | Log file directory |
| `ENABLE_LOG_SHIPPING` | `false` | Enable centralized logging |
| `CENTRAL_LOG_URL` | `None` | Centralized logging endpoint |

**Log Levels**:
- `DEBUG`: Detailed diagnostic information
- `INFO`: General informational messages (recommended for production)
- `WARNING`: Warning messages
- `ERROR`: Error messages
- `CRITICAL`: Critical errors

### Maintenance Configuration (`config.maintenance`)

| Variable | Default | Description |
|----------|---------|-------------|
| `MAINTENANCE_WARNING_THRESHOLD` | `80.0` | Disk usage warning (%) |
| `MAINTENANCE_EMERGENCY_THRESHOLD` | `90.0` | Disk usage emergency (%) |
| `MAINTENANCE_IMAGE_MAX_AGE_HOURS` | `24.0` | Max age for live images |
| `MAINTENANCE_SNAPSHOT_MAX_AGE_HOURS` | `168.0` | Max age for snapshots (1 week) |
| `MAINTENANCE_MAX_LIVE_IMAGES` | `500` | Maximum live image count |

**Validation**:
- 0 < warning < emergency ≤ 100%

### Security Configuration (`config.security`)

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | **Yes** (production) | Flask secret key |
| `JWT_SECRET` | **Yes** (production) | JWT signing secret |
| `HTTPS_ENABLED` | No | Enable HTTPS |
| `HTTPS_CERT_PATH` | No | Certificate file path |
| `HTTPS_KEY_PATH` | No | Private key file path |

**Generating Secrets**:
```bash
python config/generate_secrets.py >> .env
```

**Security Best Practices**:
1. Never commit `.env` to version control
2. Use strong, randomly generated secrets
3. Rotate secrets periodically
4. Use different secrets for development and production
5. Enable HTTPS in production

## Environment-Specific Configuration

### Development Environment

```bash
ENVIRONMENT=development
API_DEBUG=true
LOG_LEVEL=DEBUG
REDIS_HOST=localhost
DATABASE_PATH=./data/dev_traffic_data.db
```

**Features**:
- Debug mode enabled
- Verbose logging
- Local services
- Relaxed validation

### Production Environment

```bash
ENVIRONMENT=production
API_DEBUG=false
LOG_LEVEL=INFO
SECRET_KEY=<strong-random-secret>
JWT_SECRET=<strong-random-secret>
```

**Features**:
- Debug mode disabled
- Informational logging only
- Required secrets validation
- Strict security

### Testing Environment

```bash
ENVIRONMENT=testing
LOG_LEVEL=WARNING
DATABASE_PATH=:memory:
```

**Features**:
- In-memory database
- Minimal logging
- Mock external services

## Migration Guide

### From Legacy Configuration

**Before** (scattered `os.environ.get()` calls):
```python
import os

REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
DATABASE_PATH = os.environ.get('DATABASE_PATH', '/app/data/traffic_data.db')
```

**After** (centralized configuration):
```python
from config import get_config

config = get_config()
redis_host = config.redis.host
redis_port = config.redis.port
database_path = config.database.path
```

### Migration Steps

1. **Import new config**:
   ```python
   from config import get_config
   ```

2. **Replace environment reads**:
   ```python
   # OLD
   redis_host = os.environ.get('REDIS_HOST', 'redis')
   
   # NEW
   config = get_config()
   redis_host = config.redis.host
   ```

3. **Remove redundant code**:
   - Delete individual `os.environ.get()` calls
   - Remove duplicate default values
   - Remove manual type conversions

4. **Test**:
   ```bash
   python config/settings.py  # Validate configuration loads
   ```

## Configuration Validation

### Automatic Validation

All configuration is validated on load:

```python
config = get_config()
errors = config.validate()

if errors:
    for error in errors:
        print(f"Configuration error: {error}")
```

### Common Validation Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `SECRET_KEY is required in production` | Missing secret | Generate with `generate_secrets.py` |
| `Invalid Redis port` | Port out of range | Use 1-65535 |
| `Invalid ROI X coordinates` | Start >= End | Ensure start < end, both 0.0-1.0 |
| `Cannot create log directory` | Permission denied | Check directory permissions |

## Testing Configuration

### Unit Tests

```python
from config import Config, RedisConfig

def test_redis_config():
    redis_config = RedisConfig(host="localhost", port=6379)
    assert redis_config.host == "localhost"
    assert redis_config.port == 6379

def test_invalid_port():
    try:
        RedisConfig(port=99999)  # Invalid port
        assert False, "Should raise ValueError"
    except ValueError as e:
        assert "Invalid Redis port" in str(e)
```

### Environment Testing

```bash
# Test configuration loading
python -c "from config import get_config; config = get_config(); print(f'✅ Config loaded: {config.environment}')"

# Test with custom environment
export ENVIRONMENT=development
export LOG_LEVEL=DEBUG
python -c "from config import get_config; config = get_config(); print(f'Environment: {config.environment}, Log Level: {config.logging.level}')"
```

## Advanced Usage

### Custom Configuration

```python
from config import Config, RedisConfig, get_config

# Override specific values
config = get_config()
config.redis.host = "custom-redis-server"

# Create custom config for testing
test_config = Config(
    environment="testing",
    redis=RedisConfig(host="localhost", port=6380),
    database=DatabaseConfig(path=":memory:")
)
```

### Configuration Reload

```python
from config import reload_config

# Force reload from environment (useful for testing)
config = reload_config()
```

### Accessing Nested Configuration

```python
config = get_config()

# Get entire subsystem
redis_cfg = config.redis

# Get specific values
host = config.redis.host
port = config.redis.port

# ROI as tuple
roi_x = (config.camera.roi_x_start, config.camera.roi_x_end)
roi_y = (config.camera.roi_y_start, config.camera.roi_y_end)
```

## Troubleshooting

### Configuration Not Loading

**Problem**: `config = get_config()` fails

**Solutions**:
1. Check `.env` file exists
2. Verify `.env` syntax (no spaces around `=`)
3. Check for required secrets in production
4. Review validation errors in stderr

### Wrong Values Used

**Problem**: Configuration uses default instead of `.env` value

**Solutions**:
1. Verify variable name matches exactly (case-sensitive)
2. Check for typos in `.env`
3. Ensure no spaces around `=` in `.env`
4. Use `config.logging.level = "DEBUG"` to see what's loaded

### Type Conversion Errors

**Problem**: `ValueError` when loading config

**Solutions**:
1. Check numeric values are valid (e.g., `PORT=5000`, not `PORT=abc`)
2. Check boolean values use `true`/`false`, not `True`/`False`
3. Verify port numbers are 1-65535
4. Check float values use decimal notation

## Best Practices

### 1. Never Hardcode Secrets
❌ **Bad**:
```python
SECRET_KEY = "my-secret-123"
```

✅ **Good**:
```python
config = get_config()
secret_key = config.security.secret_key
```

### 2. Use Environment-Specific Configs
❌ **Bad**:
```python
if os.environ.get('ENV') == 'dev':
    DEBUG = True
else:
    DEBUG = False
```

✅ **Good**:
```python
config = get_config()
debug = config.api.debug  # Automatically set based on ENVIRONMENT
```

### 3. Validate Early
✅ **Good**:
```python
config = get_config()
errors = config.validate()
if errors and config.environment == "production":
    sys.exit(1)  # Fail fast in production
```

### 4. Document Custom Values
✅ **Good** (in `.env`):
```bash
# Custom ROI for 45-degree camera angle
STREET_ROI_X_START=0.2  # Adjusted for angle
STREET_ROI_X_END=0.8    # Adjusted for angle
```

### 5. Use Type Hints
✅ **Good**:
```python
def process_data(config: Config) -> None:
    redis_host: str = config.redis.host
    redis_port: int = config.redis.port
```

## See Also

- [Environment Configuration Template](.env.template) - Complete configuration options
- [Secret Generation](generate_secrets.py) - Generate secure secrets
- [Docker Configuration Guide](../documentation/CONTAINERIZATION_GUIDE.md) - Docker environment setup
- [Deployment Guide](../documentation/DEPLOYMENT_NOTES.md) - Production deployment

## Support

For configuration issues:
1. Check validation errors with `config.validate()`
2. Review this documentation
3. Check example configurations in `.env.template`
4. Enable debug logging: `LOG_LEVEL=DEBUG`
