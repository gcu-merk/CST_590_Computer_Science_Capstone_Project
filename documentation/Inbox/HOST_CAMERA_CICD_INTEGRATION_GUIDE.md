# Host Camera Capture Service - CI/CD Integration Guide

**Date:** September 13, 2025  
**System:** Raspberry Pi 5 with IMX500 AI Camera  
**Project:** Traffic Monitoring System with Weather Analysis  

## 📋 Overview

The host camera capture service must run directly on the Raspberry Pi host (not in Docker) to access the IMX500 camera hardware. This document outlines the complete CI/CD integration strategy for deploying and managing this service alongside the existing Docker-based traffic monitoring system.

## 🏗️ Current Architecture

### Existing Components:
- **Docker Containers:** 
  - `traffic-monitoring-edge` (main processing)
  - `traffic-maintenance` (data cleanup)
- **GitHub Actions Runner:** Self-hosted at `/home/merk/actions-runner`
- **Deployment Location:** `/home/merk/traffic-monitor-deploy`
- **Service Management:** docker-compose.yml

### New Component:
- **Host Camera Service:** `host-camera-capture.py` (Python script running on host)

## 🔧 Service Configuration

### 1. Systemd Service File

**Location:** `/etc/systemd/system/host-camera-capture.service`

The service file is located at `deployment/host-camera-capture.service` and includes:

- **User/Group:** `merk:merk` (deployment user)
- **Working Directory:** `/home/merk/traffic-monitor-deploy`
- **Dependencies:** Requires Docker service to be running
- **Restart Policy:** Always restart on failure with 10-second delay
- **Security:** Limited privileges while maintaining camera access
- **Environment:** Proper Python paths and camera configuration

### 2. Service Parameters

**Recommended Configuration:**
- **Capture Interval:** 60 seconds (configurable)
- **Max Images:** 100 (automatic cleanup)
- **Image Quality:** 95% JPEG, 4056x3040 resolution
- **Storage Location:** `/mnt/storage/camera_capture/live/`
- **Metadata:** JSON files in `/mnt/storage/camera_capture/metadata/`

## 🚀 CI/CD Integration Strategy

### 1. Enhanced Deployment Script

**Location:** `deployment/deploy.sh`

The deployment script includes:

1. **Pre-deployment Validation:**
   - Camera hardware detection using `rpicam-still --list-cameras`
   - Storage mount verification at `/mnt/storage`
   - Backup creation with timestamp

2. **Service Deployment:**
   - Host camera script deployment and permission setting
   - Camera functionality testing with `--test-only` flag
   - Systemd service installation and configuration

3. **Docker Integration:**
   - Graceful container shutdown
   - Image updates and container restart
   - Shared volume integration verification

4. **Post-deployment Verification:**
   - Service status validation
   - Image capture pipeline testing
   - API health checks

### 2. GitHub Actions Workflow Integration

**Enhanced `.github/workflows/deploy-to-pi.yml`:**

The workflow now includes:

1. **Enhanced File Download:**
   - Downloads all deployment files in single step
   - Includes host camera service files and deployment scripts
   - Sets proper permissions for execution

2. **Host Camera Service Deployment:**
   - Executes the enhanced deployment script
   - Handles both Docker and host service deployment
   - Includes comprehensive error handling

3. **Integrated Verification:**
   - Verifies both host and Docker services
   - Tests image capture pipeline
   - Validates API endpoints
   - Checks storage and resource usage

## 📁 Project Structure

### Current Directory Layout:

```
traffic-monitor-deploy/
├── docker-compose.yml                      # Docker services configuration
├── host-camera-capture.py                  # Main host service script
├── deployment/
│   ├── host-camera-capture.service         # Systemd service file
│   ├── deploy.sh                          # Main deployment script
│   ├── verify-deployment.sh               # Post-deployment checks
│   └── health-check.sh                    # System health monitoring
├── data/                                   # Docker persistent data
├── logs/                                   # Application logs
└── README.md
```

### Storage Structure:

```
/mnt/storage/
├── camera_capture/
│   ├── live/                              # Current captures (host service)
│   ├── metadata/                          # Image metadata JSON files
│   └── processed/                         # Processed by containers
├── periodic_snapshots/                    # Legacy snapshots
├── ai_camera_images/                      # AI processing results
├── processed_data/                        # Analysis outputs
├── backups/                               # System backups
└── logs/                                  # Centralized logging
```

## 🔄 Service Management Commands

### Manual Operations:

```bash
# Host camera service management
sudo systemctl start host-camera-capture
sudo systemctl stop host-camera-capture
sudo systemctl restart host-camera-capture
sudo systemctl status host-camera-capture

# View service logs
sudo journalctl -u host-camera-capture -f

# Docker services management
cd /home/merk/traffic-monitor-deploy
docker-compose up -d
docker-compose down
docker-compose logs -f

# Test camera functionality
python3 host-camera-capture.py --test-only

# Manual capture test
python3 host-camera-capture.py --interval 60 --max-images 5 --no-snapshots
```

### Service Startup Order:

1. **System Boot** → systemd starts `host-camera-capture.service`
2. **Host Service** → Creates images in shared volume
3. **Docker Services** → docker-compose starts containers
4. **Container Services** → Read images from shared volume

## 📊 Monitoring and Verification

### Automated Health Checks:

The deployment includes two verification scripts:

1. **`verify-deployment.sh`** - Comprehensive post-deployment validation
   - Service status verification
   - Docker container health
   - Image capture pipeline testing
   - Storage and API checks

2. **`health-check.sh`** - Ongoing system monitoring
   - Real-time status display
   - Resource usage monitoring
   - Log analysis
   - Storage utilization

### Usage:

```bash
# Post-deployment verification
cd /home/merk/traffic-monitor-deploy
./deployment/verify-deployment.sh

# Ongoing health monitoring
./deployment/health-check.sh

# Quick status check
sudo systemctl status host-camera-capture --no-pager
docker-compose ps
ls -la /mnt/storage/camera_capture/live/ | tail -5
```

### Log Locations:

- **Host Service Logs:** `sudo journalctl -u host-camera-capture`
- **Docker Logs:** `docker-compose logs`
- **Camera Images:** `/mnt/storage/camera_capture/live/`
- **Metadata:** `/mnt/storage/camera_capture/metadata/`

## ⚡ Performance Configuration

### Optimized Settings:

**Production Configuration (in systemd service):**
```bash
ExecStart=/usr/bin/python3 /home/merk/traffic-monitor-deploy/host-camera-capture.py \
  --interval 60 \
  --max-images 100 \
  --quality 95 \
  --width 4056 \
  --height 3040 \
  --no-snapshots
```

**Development/Testing Configuration:**
```bash
ExecStart=/usr/bin/python3 /home/merk/traffic-monitor-deploy/host-camera-capture.py \
  --interval 30 \
  --max-images 20 \
  --quality 85 \
  --width 2028 \
  --height 1520
```

### Resource Management:

- **CPU Usage:** ~1-2% during capture
- **Memory Usage:** ~15-20MB
- **Disk Usage:** ~2MB per image, auto-cleanup at 100 images
- **Network:** No network usage (local file system only)

## 🔧 Troubleshooting

### Common Issues:

1. **Camera not detected:**
   ```bash
   # Check camera hardware
   rpicam-still --list-cameras
   
   # Check permissions
   groups merk | grep video
   ```

2. **Service fails to start:**
   ```bash
   # Check service logs
   sudo journalctl -u host-camera-capture -n 50
   
   # Test script manually
   cd /home/merk/traffic-monitor-deploy
   python3 host-camera-capture.py --test-only
   ```

3. **No images captured:**
   ```bash
   # Check directory permissions
   ls -la /mnt/storage/camera_capture/
   
   # Check disk space
   df -h /mnt/storage
   ```

4. **Weather API not working:**
   ```bash
   # Check if containers can see images
   docker exec traffic-monitoring-edge ls -la /mnt/storage/camera_capture/live/
   
   # Test weather endpoint
   curl http://localhost:5000/api/weather
   ```

5. **GitHub Actions deployment failure:**
   ```bash
   # Check runner status
   cd /home/merk/actions-runner
   ./run.sh --check
   
   # Verify permissions
   ls -la /home/merk/traffic-monitor-deploy/
   
   # Manual deployment test
   cd /home/merk/traffic-monitor-deploy
   ./deployment/deploy.sh
   ```

## 🎯 Future Enhancements

### Planned Improvements:

1. **Vehicle-Triggered Weather Analysis:**
   - Modify weather monitoring to trigger only when vehicles are detected
   - Implement event-based capture instead of continuous
   
2. **Advanced Monitoring:**
   - Prometheus metrics export
   - Grafana dashboard integration
   - Alert system for service failures

3. **Cloud Integration:**
   - Automated backup of critical images
   - Remote monitoring capabilities
   - Edge-to-cloud synchronization

## 📝 Deployment Checklist

### Pre-Deployment:
- [ ] Verify camera hardware is connected and detected
- [ ] Ensure storage mount at `/mnt/storage` is available
- [ ] Confirm Docker service is running
- [ ] Check GitHub Actions runner status

### Deployment Process:
- [ ] GitHub Actions workflow triggers automatically on main branch
- [ ] Downloads all required deployment files
- [ ] Executes enhanced deployment script
- [ ] Verifies both host and Docker services

### Post-Deployment:
- [ ] Run verification script: `./deployment/verify-deployment.sh`
- [ ] Check service status: `sudo systemctl status host-camera-capture`
- [ ] Verify image capture: Check `/mnt/storage/camera_capture/live/`
- [ ] Test API endpoints: `curl http://localhost:5000/api/health`

## 📞 Support Information

**Generated:** September 13, 2025  
**System:** Raspberry Pi 5 Model B Rev 1.1  
**Camera:** IMX500 AI Camera  
**OS:** Raspberry Pi OS  
**Docker:** 20.10.24+dfsg1  

### Key Files and Locations:

- **Service File:** `/etc/systemd/system/host-camera-capture.service`
- **Deployment Directory:** `/home/merk/traffic-monitor-deploy`
- **Scripts:** `deployment/` subdirectory
- **Storage:** `/mnt/storage/camera_capture/`
- **Logs:** `sudo journalctl -u host-camera-capture`

### Quick Commands:

```bash
# Service management
sudo systemctl {start|stop|restart|status} host-camera-capture

# Deployment
cd /home/merk/traffic-monitor-deploy && ./deployment/deploy.sh

# Health check
./deployment/health-check.sh

# Manual testing
python3 host-camera-capture.py --test-only
```

**Contact:** For deployment issues, check logs first, then review this guide.

---

## 🔄 Change Log

**v1.0 - September 13, 2025:**
- Initial CI/CD integration implementation
- Enhanced deployment script with pre/post validation
- GitHub Actions workflow integration
- Comprehensive verification and health check scripts
- Complete documentation and troubleshooting guide