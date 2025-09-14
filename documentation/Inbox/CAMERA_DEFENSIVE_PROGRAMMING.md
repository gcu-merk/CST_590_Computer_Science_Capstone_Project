# Camera Pipeline Defensive Programming Implementation

## Overview

This document outlines the defensive programming improvements made to the camera pipeline system to prevent and handle the "shared_volume_failed" errors and other common issues.

## Changes Made

### 1. Test Script (`test_complete_camera_pipeline.sh`)

**Changed from**: Attempting to fix issues during testing
**Changed to**: Purely diagnostic testing with recommendations

- ✅ **Directory Structure Test**: Checks if all required directories exist
- ✅ **Permission Test**: Verifies read/write access without modifying permissions
- ✅ **Image Capture Test**: Tests camera functionality and shared volume access
- ✅ **Container Status Test**: Checks Docker containers without auto-starting
- ✅ **Recommendations**: Provides clear next steps when issues are found

### 2. Host Camera Capture Script (`scripts/host-camera-capture.py`)

**Added**: Comprehensive directory initialization with error handling

#### New `_initialize_directories()` method

- ✅ **Base Mount Check**: Warns if `/mnt/storage` doesn't exist
- ✅ **Directory Creation**: Creates all required subdirectories with error handling
- ✅ **Permission Testing**: Tests write permissions for each directory
- ✅ **Graceful Degradation**: Continues even if some operations fail
- ✅ **Detailed Logging**: Reports exactly what succeeded and what failed

#### Enhanced directory structure

```text
/mnt/storage/camera_capture/
├── live/                    # Real-time image capture
├── metadata/               # Image metadata files
├── periodic_snapshots/     # Long-term snapshots
├── processed/              # Processed images
├── backups/               # Backup storage
└── logs/                  # Capture logs
```

### 3. Shared Volume Image Provider (`edge_processing/shared_volume_image_provider.py`)

**Enhanced**: Error handling and directory management

#### New `_verify_and_create_directories()` method

- ✅ **Directory Existence**: Checks all required directories
- ✅ **Auto-Creation**: Attempts to create missing directories
- ✅ **Access Testing**: Tests read/write permissions
- ✅ **Graceful Degradation**: Continues with limited functionality if needed

#### Enhanced `_load_latest_image_from_disk()` method

- ✅ **Directory Validation**: Checks if directories exist and are accessible
- ✅ **Permission Handling**: Proper error messages for permission issues
- ✅ **File Access Errors**: Handles file stat and glob errors
- ✅ **Detailed Error Metadata**: Returns specific error information for debugging

### 4. Camera Infrastructure Initialization (`scripts/camera-init.sh`)

**New**: Comprehensive setup script for initial system configuration

#### Features

- ✅ **Root Privilege Check**: Ensures script runs with proper permissions
- ✅ **User Validation**: Verifies pi user and group exist
- ✅ **Storage Mount Check**: Validates /mnt/storage mount point
- ✅ **Directory Creation**: Creates complete directory structure
- ✅ **Permission Setting**: Sets optimal permissions for Docker compatibility
- ✅ **Access Testing**: Tests directory access as both root and pi user
- ✅ **Systemd Service**: Creates and enables camera capture service
- ✅ **Dependency Installation**: Installs required Python packages
- ✅ **Summary Report**: Provides clear status and next steps

## Error Handling Improvements

### Before (Issues)

- ❌ Directories might not exist
- ❌ Permission errors not handled
- ❌ Generic "shared_volume_failed" errors
- ❌ No recovery mechanisms
- ❌ Test script tried to fix issues

### After (Solutions)

- ✅ **Defensive Directory Creation**: All components check and create needed directories
- ✅ **Granular Error Reporting**: Specific error codes and reasons
- ✅ **Permission Validation**: Tests and reports permission issues clearly
- ✅ **Graceful Degradation**: Systems continue with reduced functionality when possible
- ✅ **Separation of Concerns**: Tests diagnose, initialization scripts fix
- ✅ **Comprehensive Logging**: Detailed logs for troubleshooting

## Usage Instructions

### Initial Setup (Run Once)

```bash
# Run the initialization script to set up infrastructure
sudo bash scripts/camera-init.sh
```

### Testing (Run Anytime)

```bash
# Run diagnostic tests to check system status
bash test_complete_camera_pipeline.sh
```

### Service Management

```bash
# Start camera capture service
sudo systemctl start host-camera-capture

# Check service status
sudo systemctl status host-camera-capture

# View service logs
journalctl -u host-camera-capture -f
```

### Docker Operations

```bash
# Start containers
docker-compose up -d

# Check container logs
docker logs $(docker ps --format "{{.Names}}" | head -1)

# Test weather API
curl http://localhost:5000/api/weather
```

## Directory Permissions

### Recommended Structure

```text
/mnt/storage/camera_capture/    # 755 (rwxr-xr-x)
├── live/                       # 777 (rwxrwxrwx) - Docker compatibility
├── metadata/                   # 777 (rwxrwxrwx) - Docker compatibility  
├── periodic_snapshots/         # 777 (rwxrwxrwx) - Docker compatibility
├── processed/                  # 777 (rwxrwxrwx) - Docker compatibility
├── backups/                    # 777 (rwxrwxrwx) - Docker compatibility
└── logs/                       # 777 (rwxrwxrwx) - Docker compatibility

Owner: pi:pi
```

## Error Code Reference

### SharedVolumeImageProvider Error Codes

- `shared_volume_failed` - General shared volume access issue
  - `live_directory_missing` - /live directory doesn't exist
  - `live_path_not_directory` - Path exists but isn't a directory
  - `permission_denied` - No read access to directory
  - `directory_access_error` - Other directory access error
  - `no_images_found` - Directory exists but contains no images
  - `file_stat_error` - Cannot get file statistics
- `image_too_old` - Image exists but exceeds max_age_seconds
- `image_load_failed` - Image file exists but cannot be loaded
  - `opencv_load_failed` - OpenCV couldn't read the image
  - `exception` - Other loading exception

## Monitoring and Troubleshooting

### Key Log Files

- `/var/log/host-camera-capture.log` - Camera capture service
- `/var/log/camera-init.log` - Initialization script
- `journalctl -u host-camera-capture` - Systemd service logs
- `docker logs <container>` - Container logs

### Health Checks

```bash
# Check if directories exist and are writable
ls -la /mnt/storage/camera_capture/

# Check recent images
ls -lt /mnt/storage/camera_capture/live/ | head -5

# Test camera manually
rpicam-still -o /tmp/test.jpg --immediate

# Check container access
docker exec <container> ls -la /app/data/camera_capture/live/
```

This defensive programming approach ensures the camera pipeline is robust, self-healing, and provides clear diagnostic information when issues occur.
