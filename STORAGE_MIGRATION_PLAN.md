# SD Card vs SSD Storage Analysis & Migration Plan

## Current Storage Issues Found:

### ❌ **Files Currently on SD Card (Need to Move to SSD):**

1. **Application Logs** (Currently on SD Card):
   - `/var/log/host-camera-capture.log` - Camera capture service logs
   - `/var/log/camera-init.log` - Infrastructure setup logs
   - `/var/log/image-sync-manager.log` - Image sync service logs
   - Docker container logs (stored in `/var/lib/docker/containers/`)

2. **Docker Data** (Currently on SD Card):
   - Container logs and metadata
   - Container filesystem layers
   - Docker volumes (postgres_data)

3. **System Logs** (Currently on SD Card):
   - All systemd service logs
   - System journal logs

### ✅ **Files Correctly on SSD:**
- Camera images: `/mnt/storage/camera_capture/`
- Periodic snapshots: `/mnt/storage/periodic_snapshots/`
- AI camera images: `/mnt/storage/ai_camera_images/`

## Storage Configuration Target:

### **SD Card (Minimal - OS Only):**
- Raspberry Pi OS system files
- Boot partition
- Essential system binaries
- Temporary files only

### **SSD (/mnt/storage):**
- All application data
- All application logs
- All camera images and metadata
- Docker volumes and persistent data
- Service logs

## Migration Actions Required:

### 1. **Move Application Logs to SSD**
Create log directory structure on SSD and update log paths.

### 2. **Configure Docker to Use SSD Storage**
Move Docker data directory to SSD for better performance.

### 3. **Update Log Rotation**
Configure logrotate to prevent log files from growing too large.

### 4. **Create Symbolic Links**
Link SD card log locations to SSD locations for compatibility.

## Implementation Plan:

1. **Create SSD log directory structure**
2. **Update application log paths**
3. **Configure Docker data directory**
4. **Set up log rotation**
5. **Create migration script**
6. **Update documentation**

This ensures maximum SSD utilization and minimal SD card wear.