# Deprecated Broken Radar Service Files

This directory contains files that were moved from the main codebase due to being part of a broken radar service implementation.

## Files Moved (September 26, 2025)

### Main Application Files
- `main_edge_app.py` - Complex edge application with vehicle detection
- `main_edge_app_enhanced.py` - Enhanced version of the edge application

### Documentation
- `CAMERA_ISSUE_RESOLUTION.md` - Documentation specific to main_edge_app.py camera issues

### Scripts
- `start-with-maintenance.sh` - Deprecated startup script that used main_edge_app.py

## Why These Files Were Moved

1. **Container Issues**: The `radar-service-new` container using these files was stuck in a restart loop (105+ restarts) due to missing cv2 (OpenCV) dependency
2. **Production System**: The current working production system uses `radar_service.py` directly, not these complex edge applications
3. **Last Modified**: These files hadn't been updated since September 19, 2025, while the working `radar_service.py` was updated on September 26, 2025
4. **Functionality**: The working radar service successfully detects vehicles and is integrated with the production docker-compose setup

## Current Production Status

- **Working Service**: `radar_service.py` (modified Sept 26, 2025 at 1:56 PM)
- **Container**: `radar-service` using `gcumerk/cst590-capstone-public:latest`
- **Status**: Healthy and actively detecting vehicles
- **Command**: `python radar_service.py`

## References Updated

The following files were updated to remove references to the deprecated files:
- `Dockerfile` - Changed CMD from main_edge_app.py to radar_service.py
- `test_suite.py` - Removed EdgeOrchestrator test
- `setup.py` - Updated run instructions
- `prepare_swagger_deployment.py` - Updated validation function
- `docker_entrypoint.py` - Changed default APP_MODULE

## Recovery Instructions

If these files are needed for future development:
1. They are preserved in this directory
2. The missing cv2 dependency would need to be resolved
3. A proper Docker image with OpenCV would need to be built
4. Integration with the current production system would need to be tested

## Working Vehicle Detection

The white truck detection you reported was successfully captured by the production `radar_service.py` system, confirming the current setup is working correctly.