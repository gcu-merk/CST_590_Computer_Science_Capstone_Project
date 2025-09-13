# SD Card vs SSD Storage Configuration

## Current Storage Analysis

### ❌ **Files Currently on SD Card (Need Moving)**

#### **Application Logs** (Currently `/var/log/` - SD Card)
- `host-camera-capture.log` - Camera service logs (~1-5MB daily)
- `camera-init.log` - Setup script logs  
- `image-sync-manager.log` - Image sync service logs
- All systemd service logs (journalctl) - Can be 100MB+

#### **Docker Data** (Currently `/var/lib/docker/` - SD Card)  
- Container images and layers (~500MB - 2GB)
- Container logs (can grow large over time)
- Container runtime data
- Docker volumes metadata

#### **System Logs** (Currently `/var/log/` - SD Card)
- `syslog`, `daemon.log`, `kern.log` etc. (10-50MB daily)
- All systemd journal logs (can be 100MB+)

### ✅ **Files Correctly on SSD**
- Camera images: `/mnt/storage/camera_capture/` ✓
- Periodic snapshots: `/mnt/storage/periodic_snapshots/` ✓  
- AI camera images: `/mnt/storage/ai_camera_images/` ✓
- All image processing data ✓

## Storage Impact Analysis

### **SD Card Wear Concerns:**
- **High**: Frequent log writes (every second for camera logs)
- **High**: Docker layer changes during updates  
- **Medium**: System log rotation
- **Critical**: Database writes (if enabled)

### **Performance Impact:**
- SD card I/O is slower than SSD
- Log writes can interfere with system performance
- Docker operations slower on SD card

## Migration Solutions

### **Option 1: Quick Fix (Recommended)**
Run the automated migration script:
```bash
# Analyze current storage
bash scripts/storage-analysis.sh

# Migrate to SSD (if issues found)
sudo bash scripts/storage-migration.sh
```

### **Option 2: Manual Configuration**

#### Move Application Logs:
```bash
# Create SSD log directories
sudo mkdir -p /mnt/storage/logs/applications
sudo chown pi:pi /mnt/storage/logs/applications

# Move existing logs
sudo mv /var/log/host-camera-capture.log /mnt/storage/logs/applications/
sudo ln -sf /mnt/storage/logs/applications/host-camera-capture.log /var/log/host-camera-capture.log

# Repeat for other application logs
```

#### Move Docker Data:
```bash
# Stop Docker
sudo systemctl stop docker

# Create SSD Docker directory  
sudo mkdir -p /mnt/storage/docker

# Move Docker data
sudo mv /var/lib/docker/* /mnt/storage/docker/
sudo rmdir /var/lib/docker
sudo ln -sf /mnt/storage/docker /var/lib/docker

# Configure Docker daemon
sudo tee /etc/docker/daemon.json << EOF
{
    "data-root": "/mnt/storage/docker",
    "log-driver": "json-file", 
    "log-opts": {
        "max-size": "10m",
        "max-file": "3"
    }
}
EOF

# Start Docker
sudo systemctl start docker
```

## Updated File Locations After Migration

### **SSD Storage (`/mnt/storage/`)**
```
/mnt/storage/
├── camera_capture/           # Camera images ✓
├── periodic_snapshots/       # Snapshots ✓  
├── ai_camera_images/         # AI processing ✓
├── logs/                     # All application logs ✓
│   ├── applications/         # App-specific logs
│   ├── system/              # System monitoring
│   ├── docker/              # Container logs  
│   └── services/            # Service output logs
├── docker/                   # Docker data ✓
├── processed_data/           # Processed results ✓
├── backups/                  # Data backups ✓
└── postgres_data/           # Database data ✓
```

### **SD Card (Minimal - OS Only)**
```
/
├── boot/                    # Boot partition
├── bin/, sbin/, usr/        # System binaries  
├── etc/                     # Configuration files
├── lib/                     # System libraries
└── var/log/                 # Symbolic links to SSD only
```

## Configuration Updates Made

### **Scripts Updated:**
- `host-camera-capture.py` - Now uses SSD logs by default
- `camera-init.sh` - Creates log structure on SSD  
- `storage-migration.sh` - Automated migration script
- `storage-analysis.sh` - Storage verification script

### **Docker Configuration:**
- `docker-compose.yml` - Updated volume mounts for SSD
- Container logging configured with size limits
- All persistent volumes point to SSD paths

### **Service Configuration:**
- Systemd services updated for SSD log paths
- Log rotation configured for SSD locations
- Monitoring scripts created

## Verification Commands

### **Check Current Configuration:**
```bash
# Run storage analysis
bash scripts/storage-analysis.sh

# Check specific locations
ls -la /var/log/host-camera-capture.log  # Should be symlink to SSD
ls -la /var/lib/docker                   # Should be symlink to SSD
df -h                                    # Check disk usage

# Check camera images (should be on SSD)
ls -la /mnt/storage/camera_capture/live/ | head -5
```

### **Monitor Storage Usage:**
```bash
# Real-time monitoring
/mnt/storage/storage-monitor.sh

# Manual checks
du -sh /mnt/storage/*                    # SSD usage by directory
du -sh /var/log/*                       # Remaining SD card logs
docker system df                        # Docker storage usage
```

## Expected Results After Migration

### **SD Card Usage:**
- **Before**: 60-80% (with logs and Docker)
- **After**: 20-40% (OS only)
- **Writes**: Minimal (mostly read-only)

### **SSD Usage:**  
- **All application data**: Camera images, logs, Docker
- **High performance**: Fast I/O for image processing
- **No wear concerns**: SSD designed for frequent writes

### **Performance Improvements:**
- Faster Docker operations
- Reduced SD card wear
- Better system responsiveness
- Faster log access and analysis

This configuration ensures maximum SSD utilization and minimal SD card wear for optimal Raspberry Pi performance.