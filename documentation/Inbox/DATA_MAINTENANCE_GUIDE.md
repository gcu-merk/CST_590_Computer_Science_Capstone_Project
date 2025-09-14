# Data File Maintenance System

## Overview

The Data File Maintenance System provides comprehensive automated cleanup, monitoring, and maintenance for the traffic monitoring camera system. It handles image files, logs, database maintenance, and disk space management across both SD card and SSD storage.

## Components

### 🔧 **Core Components**

1. **`data-maintenance-manager.py`** - Main maintenance daemon and command-line tool
2. **`setup-maintenance-scheduler.sh`** - Installation and configuration script  
3. **`disk-space-monitor.sh`** - Real-time disk monitoring and alerting
4. **`maintenance.conf`** - Configuration file for all maintenance settings

### 📋 **Convenience Scripts**

- **`maintenance-monitor.sh`** - Status dashboard
- **`quick-cleanup.sh`** - Manual cleanup trigger
- **`emergency-cleanup.sh`** - Aggressive space recovery
- **`storage-analysis.sh`** - Storage distribution analysis

## Installation & Setup

### 1. **Install Maintenance System**

```bash
# Install and configure all maintenance components
sudo bash scripts/setup-maintenance-scheduler.sh
```

This will:
- Create systemd service for maintenance daemon
- Set up cron jobs for scheduled tasks  
- Configure log rotation
- Create monitoring scripts
- Enable automatic startup

### 2. **Start Services**

```bash
# Start maintenance daemon
sudo systemctl start data-maintenance

# Check status
sudo systemctl status data-maintenance

# View logs
sudo journalctl -u data-maintenance -f
```

### 3. **Verify Installation**

```bash
# Check overall status
bash scripts/maintenance-monitor.sh

# Test disk monitoring
bash scripts/disk-space-monitor.sh

# Run manual cleanup test
bash scripts/quick-cleanup.sh
```

## Configuration

### **Main Configuration File: `config/maintenance.conf`**

```json
{
  "image_max_age_hours": 24.0,          // Keep images for 24 hours
  "snapshot_max_age_hours": 168.0,      // Keep snapshots for 1 week
  "processed_max_age_hours": 48.0,      // Keep processed images for 2 days
  "emergency_cleanup_threshold_percent": 10.0,  // Emergency at 90% usage
  
  "log_max_age_days": 30,               // Keep logs for 30 days
  "log_max_size_mb": 100,               // Rotate logs > 100MB
  
  "db_backup_max_age_days": 14,         // Keep backups for 2 weeks
  "db_vacuum_frequency_hours": 168,     // Vacuum weekly
  
  "cleanup_frequency_hours": 1.0,       // Run cleanup every hour
  "monitoring_frequency_minutes": 5,    // Monitor every 5 minutes
  "storage_warning_threshold_percent": 20.0,    // Warning at 80% usage
  "storage_critical_threshold_percent": 10.0    // Critical at 90% usage
}
```

### **Customizing Settings**

```bash
# Edit configuration
nano config/maintenance.conf

# Apply changes (restart daemon)
sudo systemctl restart data-maintenance
```

## Automated Maintenance Schedule

### **Continuous Operations**
- **Every 5 minutes**: Disk space monitoring and health checks
- **Every 15 minutes**: Emergency cleanup trigger check
- **Every hour**: Regular image and log cleanup

### **Daily Operations** 
- **1:00 AM**: Full cleanup cycle
- **2:00 AM**: Database backup
- **3:00 AM**: Log rotation

### **Weekly Operations**
- **Sunday 3:00 AM**: Database vacuum and optimization

### **Monthly Operations**
- **1st of month, 4:00 AM**: Deep cleanup and maintenance

## Manual Operations

### **Status and Monitoring**

```bash
# Comprehensive status dashboard
bash scripts/maintenance-monitor.sh

# Disk space monitoring only
bash scripts/disk-space-monitor.sh

# Storage analysis (SD vs SSD usage)
bash scripts/storage-analysis.sh

# Quick status check
python3 scripts/data-maintenance-manager.py --status
```

### **Cleanup Operations**

```bash
# Regular cleanup cycle
bash scripts/quick-cleanup.sh

# Emergency cleanup (aggressive)
bash scripts/emergency-cleanup.sh

# Specific operations
python3 scripts/data-maintenance-manager.py --cleanup      # Full cycle
python3 scripts/data-maintenance-manager.py --backup-db    # Database backup
python3 scripts/data-maintenance-manager.py --vacuum-db    # Database vacuum
```

### **Service Management**

```bash
# Service control
sudo systemctl start|stop|restart data-maintenance
sudo systemctl enable|disable data-maintenance

# View logs
sudo journalctl -u data-maintenance -f         # Follow logs
sudo journalctl -u data-maintenance --since "1 hour ago"  # Recent logs

# Check configuration
python3 scripts/data-maintenance-manager.py --status | jq .config
```

## Maintenance Targets

### **Image Files**
- **Live Images** (`/mnt/storage/camera_capture/live/`)
  - Default retention: 24 hours
  - Emergency: Keep only 25 newest files
  - Moved to processed folder before deletion

- **Processed Images** (`/mnt/storage/camera_capture/processed/`)
  - Default retention: 48 hours  
  - Emergency: All removed
  
- **Snapshots** (`/mnt/storage/periodic_snapshots/`)
  - Default retention: 1 week
  - Emergency: Keep only 5 newest
  
- **AI Camera Images** (`/mnt/storage/ai_camera_images/`)
  - Default retention: 24 hours
  - Processed same as live images

### **Log Files**
- **Application Logs** (`/mnt/storage/logs/`)
  - Rotation: 30 days or 100MB per file
  - Automatic compression of old logs
  - Cleanup of rotated logs older than retention period

- **Docker Container Logs**
  - Size limit: 10MB per container, 3 files
  - System cleanup via `docker system prune`

### **Database Maintenance**
- **Daily Backups**
  - Full PostgreSQL dump at 2:00 AM
  - Retention: 14 days
  - Stored in `/mnt/storage/backups/`

- **Weekly Vacuum**
  - `VACUUM ANALYZE` every Sunday
  - Optimizes database performance
  - Reclaims disk space

### **Metadata Files**
- **Orphaned Metadata** (`/mnt/storage/camera_capture/metadata/`)
  - JSON files without corresponding images
  - Cleaned up during regular cycles
  - Prevents metadata accumulation

## Alert System

### **Alert Types**

1. **Disk Space Alerts**
   - Warning: 80% SD card, 85% SSD usage
   - Critical: 90% SD card, 95% SSD usage
   - Automatic emergency cleanup triggered

2. **Service Health Alerts**
   - Maintenance daemon down
   - Docker service status
   - Camera capture service status

3. **File Count Alerts**
   - High image counts (>1000 live images)
   - Orphaned metadata detection
   - Large log files (>50MB)

### **Alert Destinations**

- **System Log**: All alerts logged via `logger`
- **File Log**: `/mnt/storage/logs/maintenance/disk-alerts.log`
- **JSON Alerts**: `/mnt/storage/alerts/` (for web dashboard)
- **Email**: Optional email alerts (if `mail` command available)

### **Alert Cooldown**
- 6-hour cooldown prevents alert spam
- Different cooldown timers per alert type
- Emergency alerts bypass cooldown

## Troubleshooting

### **Common Issues**

#### Maintenance Daemon Not Starting
```bash
# Check service status
sudo systemctl status data-maintenance

# Check logs for errors
sudo journalctl -u data-maintenance --no-pager

# Verify script permissions
ls -la scripts/data-maintenance-manager.py

# Test script manually
python3 scripts/data-maintenance-manager.py --status
```

#### High Disk Usage Not Cleaned
```bash
# Force emergency cleanup
bash scripts/emergency-cleanup.sh

# Check what's using space
bash scripts/storage-analysis.sh

# Manual cleanup specific directories
find /mnt/storage/camera_capture/live -name "*.jpg" -mtime +1 -delete
```

#### Database Backup Failing
```bash
# Check Docker container status
docker ps | grep postgres

# Test database connection
docker exec postgres psql -U postgres -c "SELECT version();"

# Manual backup
docker exec postgres pg_dumpall -U postgres > manual_backup.sql
```

#### Alerts Not Working
```bash
# Test alert system
bash scripts/disk-space-monitor.sh test

# Check alert log
tail -f /mnt/storage/logs/maintenance/disk-alerts.log

# Verify mail system (optional)
echo "Test" | mail -s "Test" root
```

### **Emergency Procedures**

#### Critical Disk Space (>95% usage)
```bash
# Immediate emergency cleanup
bash scripts/emergency-cleanup.sh

# Free additional space manually
sudo docker system prune -af --volumes  # Remove all unused Docker data
sudo apt autoremove --purge             # Remove old packages
sudo journalctl --vacuum-time=2d         # Clean old journal logs
```

#### System Performance Issues
```bash
# Check system resources
top
iostat -x 1 5
df -h

# Reduce maintenance frequency temporarily
# Edit config/maintenance.conf:
# "monitoring_frequency_minutes": 60  # Reduce from 5 to 60 minutes
sudo systemctl restart data-maintenance
```

#### Complete System Reset
```bash
# Stop all services
sudo systemctl stop data-maintenance host-camera-capture

# Nuclear cleanup (DANGER: REMOVES ALL DATA)
sudo rm -rf /mnt/storage/camera_capture/live/*
sudo rm -rf /mnt/storage/camera_capture/processed/*
sudo rm -rf /mnt/storage/periodic_snapshots/*
sudo docker system prune -af --volumes

# Restart services
sudo systemctl start data-maintenance host-camera-capture
```

## Performance Impact

### **Resource Usage**
- **CPU**: < 5% during cleanup cycles, < 1% during monitoring
- **Memory**: ~50MB for maintenance daemon
- **I/O**: Cleanup operations are throttled to prevent system impact

### **Optimization Settings**
- Maintenance runs during low-activity hours (1-4 AM)
- Monitoring uses minimal resources (5-minute intervals)
- Emergency cleanup only triggered when critically needed
- Database vacuum scheduled for low-traffic periods

## Integration

### **With Camera System**
- Monitors image capture directories
- Coordinates with image processing pipeline
- Respects container processing locks

### **With Docker Services**
- Manages container logs
- Monitors Docker daemon health
- Cleans up unused container resources

### **With System Services**
- Integrates with systemd for service management
- Uses system logging infrastructure
- Respects system resource limits

## Development & Customization

### **Adding New Cleanup Rules**

Edit `scripts/data-maintenance-manager.py`:

```python
def cleanup_custom_data(self):
    """Add custom cleanup logic"""
    # Your custom cleanup code here
    pass
```

### **Custom Alert Types**

Edit `scripts/disk-space-monitor.sh`:

```bash
send_custom_alert() {
    local message="$1"
    send_alert "WARNING" "Custom Alert" "$message" "custom"
}
```

### **Additional Monitoring**

Create new monitoring scripts following the pattern of existing tools.

## Security Considerations

- Maintenance scripts run with minimal privileges
- File operations are restricted to designated directories
- Database access is container-isolated
- System service integration follows security best practices

---

## Quick Reference

### **Daily Commands**
```bash
bash scripts/maintenance-monitor.sh     # Check status
bash scripts/quick-cleanup.sh          # Manual cleanup
```

### **Weekly Commands**  
```bash
bash scripts/storage-analysis.sh       # Storage review
sudo journalctl -u data-maintenance --since "1 week ago"  # Review logs
```

### **Emergency Commands**
```bash
bash scripts/emergency-cleanup.sh      # Aggressive cleanup
bash scripts/disk-space-monitor.sh     # Immediate disk check
```

### **Configuration Files**
- `config/maintenance.conf` - Main configuration
- `/etc/systemd/system/data-maintenance.service` - Service definition
- `/etc/cron.d/data-maintenance` - Scheduled tasks
- `/etc/logrotate.d/data-maintenance` - Log rotation

### **Log Locations**
- `/mnt/storage/logs/maintenance/data-maintenance.log` - Main log
- `/mnt/storage/logs/maintenance/disk-alerts.log` - Alert log
- `sudo journalctl -u data-maintenance` - System service logs