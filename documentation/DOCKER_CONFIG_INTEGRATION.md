# Docker Configuration Integration Guide
**Version:** 1.0.0  
**Last Updated:** October 8, 2025  
**Status:** ✅ Complete

## 📋 Table of Contents
1. [Overview](#overview)
2. [Configuration Validation](#configuration-validation)
3. [Docker Integration](#docker-integration)
4. [Development Workflow](#development-workflow)
5. [Testing and Validation](#testing-and-validation)
6. [Troubleshooting](#troubleshooting)
7. [Best Practices](#best-practices)

---

## 🎯 Overview

The vehicle detection system now features a **centralized configuration system** fully integrated with Docker. All 7 production services have been migrated from environment variable-based configuration to a type-safe, validated configuration system.

### Key Benefits

✅ **Type Safety**: All configuration uses Python dataclasses with type hints  
✅ **Validation**: Comprehensive validation at build time and runtime  
✅ **Simplicity**: Reduced environment variable duplication in docker-compose.yml  
✅ **Testability**: Easy to inject test configurations without environment variables  
✅ **Documentation**: Self-documenting configuration with clear defaults  
✅ **CI/CD Ready**: Validation script with exit codes for automated pipelines

### System Architecture

```
config/
├── settings.py              # Main configuration (10 dataclass categories)
├── validate_config.py       # Validation CLI tool
├── README.md                # Configuration guide (450+ lines)
└── DOCKER_INTEGRATION.md    # Pi 5 deployment guide (500+ lines)

docker-compose.yml           # Production configuration (simplified)
docker-compose.override.yml.template  # Development overrides
Dockerfile                   # Enhanced with config validation
.env.template                # Environment variable reference (180+ lines)
```

---

## 🔍 Configuration Validation

### Validation Script Features

The `config/validate_config.py` script provides comprehensive configuration validation:

**10 Configuration Categories Validated:**
- Redis (connection, pool, optimization)
- Database (SQLite path, batch, retention)
- API Gateway (host, port, workers, CORS)
- Camera (IMX500 AI, ROI, capture settings)
- Radar (OPS243 UART, baud rate)
- Weather (DHT22, airport weather API)
- Logging (level, file rotation)
- Consolidator (vehicle detection, grouping)
- Maintenance (disk thresholds, file retention)
- Security (JWT, HTTPS, secrets)

### Usage Examples

#### Validate All Configuration
```bash
# Basic validation
python config/validate_config.py

# Verbose output with detailed checks
python config/validate_config.py --verbose

# JSON output for CI/CD
python config/validate_config.py --json
```

#### Validate Specific Category
```bash
# Validate only Redis configuration
python config/validate_config.py --category redis --verbose

# Validate only Camera configuration
python config/validate_config.py --category camera
```

#### Exit Codes
```bash
0  # All validations passed
1  # Configuration validation failed
2  # Missing required environment variables
3  # Invalid configuration values
```

### Example Output

**Successful Validation:**
```
======================================================================
Configuration Validation Summary
======================================================================

✅ Passed: 10
❌ Failed: 0
📊 Total:  10

✅ Passed Categories:
  • api
  • camera
  • consolidator
  • database
  • logging
  • maintenance
  • radar
  • redis
  • security
  • weather

======================================================================
```

**JSON Output:**
```json
{
  "total_checks": 1,
  "passed": 1,
  "failed": 0,
  "results": [
    {
      "category": "redis",
      "passed": true,
      "message": "Redis configuration valid",
      "details": {
        "host": "redis",
        "port": 6379,
        "db": 0,
        "max_connections": 50
      }
    }
  ]
}
```

---

## 🐳 Docker Integration

### Dockerfile Changes

The Dockerfile has been enhanced with configuration validation:

```dockerfile
# Build-time validation
RUN python -c "from config.settings import get_config; \
    print('✅ Config system loaded successfully')" || \
    (echo "❌ Config system validation failed" && exit 1)

# Make validation script executable
RUN chmod +x /app/config/validate_config.py
```

**Benefits:**
- Catches configuration errors during image build
- Ensures config system is properly installed
- Validates Python dependencies are correct
- Fails fast if configuration is broken

### Docker Compose Simplification

The `docker-compose.yml` has been simplified to rely on configuration defaults:

**Before (Redundant Variables):**
```yaml
environment:
  - API_HOST=0.0.0.0
  - API_PORT=5000
  - API_DEBUG=false
  - API_WORKERS=4
  - SWAGGER_ENABLED=true
  - CORS_ENABLED=true
  - RATE_LIMIT_ENABLED=true
  # ... many more
```

**After (Essential Variables Only):**
```yaml
environment:
  # Core system settings
  - REDIS_HOST=redis
  - REDIS_PORT=6379
  - DATABASE_PATH=/app/data/traffic_data.db
  
  # Logging configuration
  - SERVICE_NAME=api_gateway_service
  - LOG_LEVEL=INFO
  - LOG_DIR=/app/logs
  
  # Optional overrides (has defaults in config/settings.py)
  - API_HOST=0.0.0.0
  - API_PORT=5000
  - API_DEBUG=false
```

### Service Environment Variables

**Minimal Required Variables:**
```yaml
# Required for all services
- REDIS_HOST=redis            # Redis connection
- REDIS_PORT=6379             # Redis port
- LOG_LEVEL=INFO              # Logging level
- LOG_DIR=/app/logs           # Log directory
- SERVICE_NAME=service_name   # Service identifier

# Required for database services
- DATABASE_PATH=/app/data/traffic_data.db

# Required for camera service
- CAMERA_CAPTURE_DIR=/mnt/storage/camera_capture
- IMX500_MODEL_PATH=/usr/share/imx500-models/...

# Required for radar service
- RADAR_UART_PORT=/dev/ttyAMA0
- RADAR_BAUD_RATE=19200
```

**All other settings have sensible defaults in `config/settings.py`**

---

## 🛠️ Development Workflow

### Using Docker Compose Override

The `docker-compose.override.yml.template` provides examples for local development:

**1. Copy Template:**
```bash
cp docker-compose.override.yml.template docker-compose.override.yml
```

**2. Enable Config Validation:**
```yaml
services:
  traffic-monitor:
    environment:
      - CONFIG_VALIDATION=strict  # Validate on startup
      - ENVIRONMENT=development
      - API_DEBUG=true
      - LOG_LEVEL=DEBUG
```

**3. Start Services:**
```bash
# Normal start (uses override automatically)
docker-compose up -d

# View combined configuration
docker-compose config
```

### Development Services

**Config Validator Service:**
```bash
# Run standalone config validation
docker-compose --profile testing up config-validator
```

**Interactive Config Shell:**
```bash
# Start interactive Python shell with config loaded
docker-compose --profile development run config-shell

# Then in Python:
>>> from config.settings import get_config
>>> config = get_config()
>>> print(config.redis.host)
redis
>>> print(config.camera.confidence_threshold)
0.5
```

### Live Code Development

Mount local code for live development:

```yaml
services:
  traffic-monitor:
    volumes:
      - ./edge_api:/app/edge_api:ro
      - ./config:/app/config:ro
    environment:
      - ENVIRONMENT=development
      - CONFIG_VALIDATION=strict
```

---

## ✅ Testing and Validation

### Pre-Deployment Checklist

**1. Validate Configuration:**
```bash
# Run comprehensive validation
python config/validate_config.py --verbose

# Expected output: All 10 categories pass
✅ Passed: 10
❌ Failed: 0
```

**2. Validate Docker Compose:**
```bash
# Check docker-compose.yml syntax
docker-compose config --quiet

# View resolved configuration
docker-compose config | head -50
```

**3. Test Build:**
```bash
# Build with config validation
docker build -t vehicle-detection:test .

# Should see during build:
# ✅ Config system loaded successfully
```

**4. Test Services:**
```bash
# Start services
docker-compose up -d

# Check logs for config loading
docker-compose logs traffic-monitor | grep -i config

# Verify health checks pass
docker-compose ps
```

### Validation in CI/CD

**GitHub Actions Example:**
```yaml
name: Validate Configuration
on: [push, pull_request]

jobs:
  validate-config:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements-api.txt
      
      - name: Validate configuration
        run: python config/validate_config.py --verbose
      
      - name: Validate Docker Compose
        run: docker-compose config --quiet
      
      - name: Test Docker build
        run: docker build -t test:latest .
```

### Testing Specific Scenarios

**Test with Invalid Configuration:**
```bash
# Set invalid Redis port
export REDIS_PORT=99999

# Run validation (should fail with exit code 3)
python config/validate_config.py
echo $?  # Should print: 3

# Unset variable
unset REDIS_PORT
```

**Test Missing Required Variables:**
```bash
# Clear all environment variables
env -i python config/validate_config.py

# Should pass (uses defaults from config/settings.py)
```

---

## 🔧 Troubleshooting

### Common Issues

#### Issue 1: Config Validation Fails During Build

**Symptom:**
```
❌ Config system validation failed
ERROR: Service 'traffic-monitor' failed to build
```

**Solution:**
```bash
# Test config locally first
python config/validate_config.py --verbose

# Check for missing dependencies
pip install -r requirements-api.txt

# Verify config module structure
python -c "from config.settings import get_config; print('OK')"
```

#### Issue 2: Service Won't Start Due to Config Error

**Symptom:**
```
service_1  | ValueError: Invalid batch_size: 0
service_1  | exited with code 1
```

**Solution:**
```bash
# Check which variable is invalid
docker-compose config | grep -i batch_size

# Fix in .env or docker-compose.yml
echo "BATCH_SIZE=100" >> .env

# Restart service
docker-compose up -d service_1
```

#### Issue 3: Environment Variables Not Loading

**Symptom:**
```
Using default configuration values instead of environment variables
```

**Solution:**
```bash
# Verify .env file exists
ls -la .env

# Check .env is loaded by docker-compose
docker-compose config | grep -A5 environment

# Verify variable is exported in shell
echo $REDIS_HOST

# Make sure no typos in variable names
python config/validate_config.py --verbose
```

#### Issue 4: Docker Compose Override Not Working

**Symptom:**
```
Configuration not overridden in development
```

**Solution:**
```bash
# Verify override file exists
ls -la docker-compose.override.yml

# Check that docker-compose loads it
docker-compose config | head -20

# View merged configuration
docker-compose config --services

# Force reload
docker-compose down
docker-compose up -d
```

### Debug Commands

```bash
# View full resolved configuration
docker-compose config

# Test validation in container
docker-compose run --rm traffic-monitor \
  python config/validate_config.py --verbose

# Check environment variables in running container
docker-compose exec traffic-monitor env | grep -i redis

# View config loading in real-time
docker-compose logs -f traffic-monitor | grep -i config

# Interactive debugging
docker-compose run --rm traffic-monitor python
>>> from config.settings import get_config
>>> config = get_config()
>>> print(vars(config.redis))
```

---

## 📚 Best Practices

### Configuration Management

**1. Use .env for Secrets**
```bash
# Never commit secrets to git
echo ".env" >> .gitignore

# Store secrets in .env
echo "JWT_SECRET=your-secret-here" >> .env
echo "SECRET_KEY=your-flask-secret" >> .env
```

**2. Document All Variables**
```python
# In config/settings.py, always add docstrings
@dataclass
class RedisConfig:
    """Redis connection and pool configuration"""
    host: str = field(default="redis")  # Hostname or IP
    port: int = field(default=6379)     # Redis port (1-65535)
```

**3. Validate Early and Often**
```bash
# Before committing changes
python config/validate_config.py --verbose

# Before deployment
python config/validate_config.py --json > validation-report.json

# In CI/CD pipeline
python config/validate_config.py || exit 1
```

**4. Use Defaults Wisely**
```python
# Good: Sensible production defaults
database_path: str = field(default="/app/data/traffic_data.db")

# Bad: No default for required value
database_path: str  # Will fail if not provided
```

**5. Override Only When Needed**
```yaml
# Good: Override only what differs from defaults
environment:
  - LOG_LEVEL=DEBUG  # Development override

# Avoid: Repeating defaults unnecessarily
environment:
  - LOG_LEVEL=INFO  # Already the default
```

### Docker Compose Best Practices

**1. Use Environment Variable Files**
```yaml
# Good: Use .env file
services:
  traffic-monitor:
    env_file:
      - .env
```

**2. Keep docker-compose.yml Simple**
```yaml
# Good: Essential variables only
environment:
  - REDIS_HOST=redis
  - LOG_LEVEL=INFO

# Avoid: Duplicating all defaults
environment:
  - REDIS_HOST=redis
  - REDIS_PORT=6379  # Default in config
  - REDIS_DB=0       # Default in config
  - REDIS_MAX_CONNECTIONS=50  # Default in config
```

**3. Use docker-compose.override.yml for Development**
```yaml
# Development-specific overrides
services:
  traffic-monitor:
    environment:
      - ENVIRONMENT=development
      - LOG_LEVEL=DEBUG
    volumes:
      - ./edge_api:/app/edge_api:ro
```

**4. Validate Before Deployment**
```bash
# Always validate before pushing
docker-compose config --quiet || exit 1
python config/validate_config.py || exit 1
```

### Testing Best Practices

**1. Test with Minimal Configuration**
```bash
# Clear environment
env -i python config/validate_config.py

# Should pass with defaults
```

**2. Test with Invalid Values**
```bash
# Set invalid value
export REDIS_PORT=99999

# Expect failure
python config/validate_config.py
# Should fail with exit code 3
```

**3. Test in Container**
```bash
# Build and test
docker build -t test:latest .

# Should pass build-time validation
```

**4. Test All Services**
```bash
# Start all services
docker-compose up -d

# Check all services are healthy
docker-compose ps

# Check logs for config errors
docker-compose logs | grep -i error
```

---

## 📖 Additional Resources

- **Configuration Guide**: `config/README.md` (450+ lines)
- **Pi 5 Deployment**: `config/DOCKER_INTEGRATION.md` (500+ lines)
- **Environment Variables**: `.env.template` (180+ lines)
- **Phase 4 Summary**: `documentation/PHASE_4_TASK_5_COMPLETION_SUMMARY.md` (440 lines)

---

## 🎉 Summary

The Docker configuration integration provides:

✅ **Type-safe configuration** with Python dataclasses  
✅ **Comprehensive validation** at build and runtime  
✅ **Simplified docker-compose.yml** with less duplication  
✅ **Development workflow** with override template  
✅ **CI/CD ready** with exit codes and JSON output  
✅ **Self-documenting** with clear defaults and validation  

**All 7 production services** have been migrated and tested. The system is production-ready with enhanced reliability and maintainability.

---

**Document Version:** 1.0.0  
**Author:** GitHub Copilot  
**Last Updated:** October 8, 2025
