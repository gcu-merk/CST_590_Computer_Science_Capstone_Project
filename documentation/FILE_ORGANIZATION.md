# File Organization Guide

## Overview
This document clarifies which files are actively used in production vs deprecated/development versions.

## Production Files (Used by docker-compose.yml)

### Core Services

1. **radar_service.py** (ROOT)
   - Status: ✅ PRODUCTION
   - Version: 2.1.2
   - Referenced by: docker-compose.yml (`command: ["python", "radar_service.py"]`)
   - Features: ServiceLogger, CorrelationContext, Redis integration, UART communication
   - **IMPORTANT**: Do not move this file - docker-compose depends on root location
   - History: Restored from scripts/deprecated/ in 2025 to fix docker-compose reference

2. **edge_api/edge_api_gateway_enhanced.py**
   - Status: ✅ PRODUCTION
   - Port: 5000
   - Service: API Gateway with enhanced error handling and logging

3. **edge_processing/data_maintenance_service_enhanced.py**
   - Status: ✅ PRODUCTION
   - Service: Disk cleanup, database optimization, and monitoring

4. **edge_processing/airport_weather_service_enhanced.py**
   - Status: ✅ PRODUCTION
   - Service: Weather data collection from airport APIs

5. **edge_processing/data_persistence/database_persistence_service_simplified.py**
   - Status: ✅ PRODUCTION
   - Service: SQLite persistence layer (simplified from enhanced version)

6. **edge_processing/data_persistence/redis_optimization_service_enhanced.py**
   - Status: ✅ PRODUCTION
   - Service: Redis data optimization and cleanup

7. **imx500_ai_host_capture_enhanced.py**
   - Status: ✅ PRODUCTION (systemd service on host)
   - Service: IMX500 camera capture with AI object detection

8. **realtime_events_broadcaster.py**
   - Status: ✅ PRODUCTION
   - Port: 5001
   - Service: WebSocket event streaming

9. **edge_processing/vehicle_detection/vehicle_consolidator_service.py**
   - Status: ✅ PRODUCTION
   - Service: Vehicle detection fusion (radar + camera)

## Deprecated Files (Not Used)

### API Gateway
- ❌ `edge_api/edge_api_gateway_original.py` - Superseded by enhanced version
- ❌ `edge_api/edge_api_gateway.py` - Superseded by enhanced version

### Data Persistence
- ❌ `edge_processing/data_persistence/database_persistence_service.py` - Superseded by simplified version
- ❌ `edge_processing/data_persistence/database_persistence_service_enhanced.py` - Superseded by simplified version
- ❌ `edge_processing/data_persistence/redis_optimization_service.py` - Superseded by enhanced version

### Weather Services
- ❌ `edge_processing/airport_weather_service.py` - Superseded by enhanced version
- ❌ `edge_processing/dht_22_weather_service.py` - Superseded by enhanced version

### Radar Services
- ⚠️ `edge_processing/ops243_radar_service.py` - Status unclear, investigate usage
- ⚠️ `scripts/deprecated/radar_service.py` - Backup of production version (DO NOT DELETE)

## Development/Test Variants

Located in `scripts/development/`:
- `radar_service_enhanced.py` - Enhanced logging testing
- `radar_service_fixed.py` - Bug fix testing
- `radar_service_debug.py` - Debug version
- `radar_service_deployed.py` - Deployment testing
- `radar_service_corrected.py` - Corrections testing
- Various `test_enhanced_*.py` files

**Purpose**: These are development/testing variants. Keep for reference but not used in production.

## Cleanup Recommendations

### Phase 1: Move Deprecated Files
```bash
# Create backup directory if not exists
mkdir -p backup/deprecated_api
mkdir -p backup/deprecated_persistence
mkdir -p backup/deprecated_weather

# Move deprecated files
git mv edge_api/edge_api_gateway_original.py backup/deprecated_api/
git mv edge_api/edge_api_gateway.py backup/deprecated_api/
git mv edge_processing/data_persistence/database_persistence_service.py backup/deprecated_persistence/
git mv edge_processing/data_persistence/database_persistence_service_enhanced.py backup/deprecated_persistence/
git mv edge_processing/data_persistence/redis_optimization_service.py backup/deprecated_persistence/
git mv edge_processing/airport_weather_service.py backup/deprecated_weather/
git mv edge_processing/dht_22_weather_service.py backup/deprecated_weather/
```

### Phase 2: Investigate Unclear Status
- Review `edge_processing/ops243_radar_service.py` usage
- Determine if it's used by any scripts or services
- Move to backup/ or mark as production

### Phase 3: Consolidate Development Variants
- Keep only the most recent/complete versions in scripts/development/
- Move older variants to documentation/archive/

## File Naming Convention

Moving forward, use this convention:
- **Production files**: No suffix (e.g., `radar_service.py`)
- **Development versions**: `_dev` suffix (e.g., `radar_service_dev.py`)
- **Test versions**: `test_` prefix (e.g., `test_radar_service.py`)
- **Deprecated files**: Move to `backup/deprecated_<category>/`

## Docker Dependencies

Critical files referenced in `docker-compose.yml`:
1. `radar_service.py` ← **MUST remain in root**
2. `edge_api/edge_api_gateway_enhanced.py`
3. `edge_processing/data_maintenance_service_enhanced.py`
4. `edge_processing/airport_weather_service_enhanced.py`
5. `edge_processing/data_persistence/database_persistence_service_simplified.py`
6. `edge_processing/data_persistence/redis_optimization_service_enhanced.py`
7. `realtime_events_broadcaster.py`
8. `edge_processing/vehicle_detection/vehicle_consolidator_service.py`

**Warning**: Moving any of these files will break docker-compose.yml

## Systemd Dependencies (Pi 5 Host)

Critical file referenced in `imx500-ai-capture.service`:
- `imx500_ai_host_capture_enhanced.py` ← **MUST remain in root**

## History Notes

### radar_service.py Restoration (2025)
- **Commit 91310ae**: Moved radar_service.py → scripts/deprecated/radar_service.py during "Phase 1 & 2: Security hardening and repository cleanup"
- **Issue**: docker-compose.yml still referenced root location, causing potential build failures
- **Fix**: Restored scripts/deprecated/radar_service.py → radar_service.py (root)
- **Reason**: Maintain backward compatibility with docker-compose.yml without requiring configuration changes
- **Backup**: Original remains in scripts/deprecated/ for reference

## Migration to Centralized Configuration

Phase 4 Task 5 will migrate all production services to use `config/settings.py`:

**Priority Order**:
1. Redis clients (redis_optimization_service_enhanced.py)
2. Database services (database_persistence_service_simplified.py)
3. API gateways (edge_api_gateway_enhanced.py)
4. Camera service (imx500_ai_host_capture_enhanced.py)
5. Radar service (radar_service.py) ← Start here for example
6. Weather services (airport_weather_service_enhanced.py)
7. Maintenance (data_maintenance_service_enhanced.py)

**Migration Pattern**:
```python
# Before (old pattern)
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.environ.get('REDIS_PORT', '6379'))

# After (centralized config)
from config.settings import get_config
config = get_config()
REDIS_HOST = config.redis.host
REDIS_PORT = config.redis.port
```

## Questions?

See also:
- `config/README.md` - Configuration system documentation
- `config/DOCKER_INTEGRATION.md` - Pi 5 Docker deployment guide
- `docker-compose.yml` - Service definitions and file references
