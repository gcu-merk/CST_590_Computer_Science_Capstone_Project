# DHT22 Service Architecture Evolution & Solution

## Overview
This document explains the evolution of the DHT22 weather service from local Docker builds to standardized remote images with runtime GPIO library installation.

## Problem Summary
The DHT22 service stopped working after migrating from local Docker builds to standardized remote images because GPIO libraries (lgpio, gpiozero) were missing from the containerized environment.

## Architecture Evolution

### Previous Approach (Local Build - 3 days ago)
```yaml
dht22-weather:
  build:                    # ❌ Local build per Pi
    context: .
    dockerfile: Dockerfile
  command: ["python", "-m", "edge_processing.dht_22_weather_service_enhanced"]
```

**Issues with Previous Approach:**
- Each Pi had to build its own Docker image
- GPIO libraries baked into image (bloat)
- No standardization across deployment environments
- Slower CI/CD pipeline due to build requirements

### Current Approach (Standardized Image + Runtime Installation)
```yaml
dht22-weather:
  image: gcumerk/cst590-capstone-public:latest  # ✅ Standardized image
  entrypoint: ["python", "docker_entrypoint.py"]
  environment:
    - SERVICE_TYPE=dht22      # ✅ Triggers GPIO library installation
```

## Solution Architecture

### 1. Hardware Detection Logic
The `docker_entrypoint.py` automatically detects Pi hardware:
```python
def is_raspberry_pi():
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read().lower()
        return any(keyword in cpuinfo for keyword in ['raspberry', 'bcm'])
    except:
        return False
```

### 2. Runtime GPIO Library Installation
When Pi hardware is detected:
```bash
pip install lgpio>=0.2.2.0 gpiozero>=1.6.2
```

### 3. Service Routing
Based on `SERVICE_TYPE=dht22`, the entrypoint executes:
```bash
python -m edge_processing.dht_22_weather_service_enhanced
```

## Benefits of New Approach

### ✅ Advantages
1. **Standardized Images**: One image works across all services and environments
2. **Lightweight Base**: No unnecessary GPIO libraries in base image
3. **Runtime Adaptation**: Only installs GPIO libraries when actually on Pi hardware
4. **Faster CI/CD**: No per-Pi builds required
5. **Better Architecture**: Clear separation of concerns
6. **Maintainability**: Centralized entrypoint logic for all services

### 🔄 Maintained Features
- Identical GPIO device mappings and permissions
- Same module execution pattern
- Equivalent hardware access capabilities
- Same healthcheck and monitoring

## Container Configuration Comparison

| Aspect | Previous (Local Build) | Current (Standardized) |
|--------|----------------------|----------------------|
| Image Source | Local build per Pi | Remote standardized image |
| GPIO Libraries | Built-in during image build | Installed at runtime on Pi |
| Hardware Detection | Not needed | Automatic via /proc/cpuinfo |
| Deployment Speed | Slow (build required) | Fast (image pull only) |
| Resource Usage | Higher (bloated images) | Lower (lean base image) |
| Cross-Platform | Pi-only builds | Works everywhere |

## Verification Steps

### On Pi (SSH Access Required)
```bash
# 1. Check service status
docker ps | grep dht22-weather

# 2. Verify entrypoint logs
docker logs dht22-weather 2>&1 | grep -i gpio

# 3. Check Redis data
docker exec redis redis-cli HGETALL weather:dht22

# 4. Test API endpoint
curl http://localhost:5000/weather/current
```

### Remote Verification
```powershell
# Run the status check script
.\check_dht22_status.ps1 -PiAddress 192.168.1.100

# Test entrypoint logic
python test_dht22_entrypoint_logic.py
```

## Expected Log Output

### Successful Startup
```
Detecting hardware platform...
Raspberry Pi detected in /proc/cpuinfo
Installing GPIO libraries for Pi hardware...
GPIO libraries installed successfully: lgpio==0.2.2.0, gpiozero==1.6.2
Service type: dht22
Executing: python -m edge_processing.dht_22_weather_service_enhanced
DHT22 Weather Service starting...
```

## Rollback Plan (If Needed)

If issues arise, revert to local builds:
```yaml
dht22-weather:
  build:
    context: .
    dockerfile: Dockerfile
  command: ["python", "-m", "edge_processing.dht_22_weather_service_enhanced"]
  # Remove entrypoint and SERVICE_TYPE
```

## Future Enhancements

1. **Library Caching**: Cache installed GPIO libraries across container restarts
2. **Version Pinning**: Pin specific GPIO library versions for consistency
3. **Health Monitoring**: Enhanced monitoring of GPIO library installation success
4. **Multi-Architecture**: Support for different Pi models and architectures

## Conclusion

The new entrypoint-based approach successfully maintains all DHT22 functionality while providing better architecture, faster deployments, and standardized images. The solution automatically adapts to Pi hardware and installs required GPIO libraries at runtime, ensuring compatibility across all deployment environments.