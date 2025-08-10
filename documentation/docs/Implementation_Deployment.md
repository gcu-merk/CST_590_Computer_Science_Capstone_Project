# Implementation & Deployment Guide

**Document Version:** 1.0  
**Last Updated:** August 7, 2025  
**Project:** Raspberry Pi 5 Edge ML Traffic Monitoring System  
**Authors:** Implementation Team  

## Table of Contents
1. [Prerequisites](#1-prerequisites)
2. [Installation Steps](#2-installation-steps)
3. [Integration & Configuration](#3-integration--configuration)
4. [Troubleshooting & Maintenance](#4-troubleshooting--maintenance)

**See also:**
- [Technical Design Document](./Technical_Design.md)
- [User Guide](./User_Guide.md)
- [Project Management Summary](./Project_Management.md)
- [References & Appendices](./References_Appendices.md)

## 1. Prerequisites

### Hardware Requirements
- Raspberry Pi 5 (16GB RAM recommended)
- Raspberry Pi AI Camera (Sony IMX500)
- OmniPreSense OPS243-C Radar Sensor
- Samsung T7 SSD (or similar), 256GB MicroSD card
- Power supply (PoE or USB-C)
- Ethernet or WiFi network access

### Software Requirements
- Raspberry Pi OS (64-bit, latest)
- Python 3.10+
- Docker (recommended for deployment)
- PostgreSQL (local or remote)
- Required Python packages: TensorFlow, OpenCV, Flask, Flask-SocketIO, NumPy, SQLAlchemy, etc.

### Network & Power Setup
- Ensure stable power and network connectivity at the deployment site
- (Optional) Configure PoE or cellular backup for remote locations

---

## 2. Installation Steps

### 2.1. Raspberry Pi & OS Setup
1. **Flash Raspberry Pi OS (64-bit) to the MicroSD card**
   ```bash
   # Using Raspberry Pi Imager or manual dd command
   sudo dd if=raspios-lite-arm64.img of=/dev/sdX bs=4M status=progress
   ```

2. **Boot the Pi and complete initial OS setup**
   ```bash
   # Enable SSH before first boot (optional)
   sudo touch /boot/ssh
   
   # Configure WiFi before first boot (optional)
   sudo nano /boot/wpa_supplicant.conf
   ```

3. **Update system packages**
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install -y git python3-pip python3-venv postgresql postgresql-contrib
   ```

4. **Enable required interfaces**
   ```bash
   # Enable Camera, SPI, I2C, and UART
   sudo raspi-config nonint do_camera 0
   sudo raspi-config nonint do_spi 0
   sudo raspi-config nonint do_i2c 0
   sudo raspi-config nonint do_serial 1
   
   # Edit boot config for UART
   echo "enable_uart=1" | sudo tee -a /boot/firmware/config.txt
   echo "dtparam=spi=on" | sudo tee -a /boot/firmware/config.txt
   
   # Reboot to apply changes
   sudo reboot
   ```

### 2.2. Hardware Assembly
1. **Connect the AI Camera to the Pi camera port**
   - Use the CSI-2 ribbon cable (included with camera)
   - Ensure proper orientation (blue side toward Ethernet port)

2. **Wire the OPS243-C radar sensor to the Pi GPIO header**
   ```
   OPS243-C Pin 9 (5V)    → Pi Pin 2 (5V)
   OPS243-C Pin 10 (GND)  → Pi Pin 6 (GND)
   OPS243-C Pin 6 (RxD)   → Pi Pin 8 (TXD/GPIO14)
   OPS243-C Pin 7 (TxD)   → Pi Pin 10 (RXD/GPIO15)
   ```

3. **Connect SSD for local storage**
   ```bash
   # Format and mount external SSD
   sudo fdisk /dev/sda  # Create partition
   sudo mkfs.ext4 /dev/sda1
   sudo mkdir /mnt/storage
   sudo mount /dev/sda1 /mnt/storage
   
   # Add to fstab for automatic mounting
   echo "/dev/sda1 /mnt/storage ext4 defaults 0 2" | sudo tee -a /etc/fstab
   ```

4. **Verify hardware connections**
   ```bash
   # Test camera
   libcamera-hello --preview=none --timeout=5000
   
   # Test UART (should show radar sensor data)
   sudo cat /dev/serial0
   
   # Check USB devices
   lsusb
   ```

### 2.3. Python Environment & Dependencies
1. **Create virtual environment**
   ```bash
   python3 -m venv /opt/traffic-monitor
   source /opt/traffic-monitor/bin/activate
   ```

2. **Install required packages**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   
   # Core dependencies
   pip install tensorflow opencv-python flask flask-socketio
   pip install psycopg2-binary sqlalchemy numpy pandas
   pip install pyserial RPi.GPIO picamera2
   ```

3. **PostgreSQL Database Setup**
   ```bash
   # Create database user and database
   sudo -u postgres createuser --interactive traffic_user
   sudo -u postgres createdb traffic_monitor
   
   # Set password for database user
   sudo -u postgres psql -c "ALTER USER traffic_user PASSWORD 'your_secure_password';"
   
   # Grant privileges
   sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE traffic_monitor TO traffic_user;"
   ```

### 2.4. Configuration Templates

#### Database Configuration (`config/database.conf`)
```ini
[database]
host = localhost
port = 5432
database = traffic_monitor
username = traffic_user
password = your_secure_password
pool_size = 10

```

## 5. Future Work & Clarifications

### Future Work
- **Automated Deployment Scripts:** Expand and refine scripts for one-click setup, including cloud and edge deployments.
- **Containerization Enhancements:** Improve Docker Compose and multi-architecture support for easier deployment on various edge devices.
- **Remote Update Mechanisms:** Add secure, over-the-air update capabilities for field devices.
- **Monitoring & Logging:** Integrate advanced monitoring, alerting, and log aggregation tools.
- **Configuration UI:** Develop a user-friendly web interface for system configuration and diagnostics.

### Contradictions & Clarifications
- The GitHub repository may reference additional deployment automation or CI/CD features not fully implemented in the current scripts. Document and clarify any differences in future updates.
- Some troubleshooting and maintenance steps are described as manual; automation is a future goal.

### Repository Reference
- For deployment scripts, Dockerfiles, and configuration templates, see: [CST_590_Computer_Science_Capstone_Project GitHub](https://github.com/gcu-merk/CST_590_Computer_Science_Capstone_Project)

#### API Configuration (`config/api.conf`)
```ini
[api]
host = 0.0.0.0
port = 5000
debug = false
secret_key = your_secret_key_here
jwt_secret = your_jwt_secret_here

[security]
api_rate_limit = 100
enable_cors = true
allowed_origins = http://localhost:3000,https://yourdomain.com
```

#### Radar Sensor Configuration (`config/radar.conf`)
```ini
[radar]
port = /dev/serial0
baudrate = 9600
timeout = 1.0
buffer_size = 1024

[detection]
min_speed_threshold = 5.0
max_speed_threshold = 100.0
range_filter_min = 1.0
range_filter_max = 200.0
```

### 2.5. Application Deployment
1. **Clone project repository**
   ```bash
   cd /opt
   git clone https://github.com/your-org/traffic-monitor.git
   cd traffic-monitor
   ```

2. **Configure systemd services**
   ```bash
   # Copy service files
   sudo cp scripts/traffic-monitor-api.service /etc/systemd/system/
   sudo cp scripts/traffic-monitor-processor.service /etc/systemd/system/
   
   # Enable and start services
   sudo systemctl daemon-reload
   sudo systemctl enable traffic-monitor-api
   sudo systemctl enable traffic-monitor-processor
   sudo systemctl start traffic-monitor-api
   sudo systemctl start traffic-monitor-processor
   ```

3. **Verify deployment**
   ```bash
   # Check service status
   sudo systemctl status traffic-monitor-api
   sudo systemctl status traffic-monitor-processor
   
   # Test API endpoint
   curl http://localhost:5000/api/health
   
   # View logs
   sudo journalctl -u traffic-monitor-api -f
   ```
1. Install Python 3.10+ if not already present
2. Create and activate a virtual environment:
   ```bash
   python3 -m venv ~/traffic-monitor/venv
   source ~/traffic-monitor/venv/bin/activate
   ```
3. Install required Python packages:
   ```bash
   pip install tensorflow opencv-python flask flask-socketio numpy sqlalchemy psycopg2-binary
   ```

### 2.4. Database Setup
1. Install PostgreSQL (if local):
   ```bash
   sudo apt install postgresql postgresql-contrib
   ```
2. Create database and user:
   ```sql
   CREATE DATABASE traffic_monitor;
   CREATE USER tm_user WITH PASSWORD 'yourpassword';
   GRANT ALL PRIVILEGES ON DATABASE traffic_monitor TO tm_user;
   ```
3. Update backend configuration with database credentials

### 2.5. Application Deployment
1. Clone or copy the project code to the Pi
2. (Recommended) Build and run services using Docker Compose
3. Alternatively, run backend and dashboard manually from the virtual environment
4. Start the Flask API and dashboard services

---


## 3. Integration

### 3.1. Hardware-Software Integration
- Ensure all hardware is connected as per the GPIO pin mapping in the Technical Design Document.
- Enable UART on the Raspberry Pi (see radar sensor setup instructions).
- Verify camera functionality using `libcamera` or `picamera2` test commands.

### 3.2. Database & API Configuration
- Update backend configuration files with correct PostgreSQL credentials and host.
- Run database migration scripts (if provided) to create tables.
- Test database connectivity from the backend using a simple script or API call.

### 3.3. Service Startup & Verification
- Start backend services (Flask API, WebSocket server, ML pipeline).
- Access the Edge UI dashboard in a browser (default: http://<pi-ip>:5000 or similar).
- Confirm real-time data is displayed and events are logged in the database.

---

## 4. Troubleshooting & Maintenance

### 4.1. Common Issues & Solutions

#### Camera Issues
- **No camera detected:**
  ```bash
  # Check camera detection
  libcamera-hello --list-cameras
  
  # Verify ribbon cable connection and enable camera
  sudo raspi-config nonint do_camera 0
  
  # Check boot config
  grep camera /boot/firmware/config.txt
  ```

- **Poor image quality:**
  ```bash
  # Test different camera settings
  libcamera-still -o test.jpg --width 1920 --height 1080
  
  # Check lens focus and clean lens
  # Verify adequate lighting conditions
  ```

#### Radar Sensor Issues
- **No radar data:**
  ```bash
  # Verify UART is enabled
  sudo raspi-config nonint do_serial 1
  
  # Check UART communication
  sudo cat /dev/serial0
  
  # Test with minicom
  sudo apt install minicom
  sudo minicom -D /dev/serial0 -b 9600
  
  # Check power and connections
  gpio readall  # Verify GPIO states
  ```

#### Database Issues
- **Database connection errors:**
  ```bash
  # Check PostgreSQL status
  sudo systemctl status postgresql
  
  # Test connection
  psql -h localhost -U traffic_user -d traffic_monitor
  
  # Check logs
  sudo tail -f /var/log/postgresql/postgresql-*.log
  ```

- **Database performance issues:**
  ```sql
  -- Check database size and table statistics
  SELECT schemaname,tablename,attname,n_distinct,correlation 
  FROM pg_stats WHERE tablename = 'vehicleevent';
  
  -- Vacuum and analyze tables
  VACUUM ANALYZE vehicleevent;
  VACUUM ANALYZE radarreading;
  ```

#### Network and API Issues
- **API not responding:**
  ```bash
  # Check service status
  sudo systemctl status traffic-monitor-api
  
  # Check port binding
  sudo netstat -tlnp | grep :5000
  
  # Test local connectivity
  curl -v http://localhost:5000/api/health
  ```

- **Dashboard not loading:**
  ```bash
  # Check firewall rules
  sudo ufw status
  
  # Verify CORS settings
  grep cors config/api.conf
  
  # Check browser console for JavaScript errors
  ```

### 4.2. Backup & Recovery Procedures

#### Database Backup
```bash
#!/bin/bash
# Create automated backup script: /opt/scripts/backup_database.sh

BACKUP_DIR="/mnt/storage/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="traffic_monitor_backup_${DATE}.sql"

# Create backup directory
mkdir -p $BACKUP_DIR

# Perform database backup
pg_dump -h localhost -U traffic_user traffic_monitor > $BACKUP_DIR/$BACKUP_FILE

# Compress backup
gzip $BACKUP_DIR/$BACKUP_FILE

# Remove backups older than 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE.gz"
```

#### System Configuration Backup
```bash
#!/bin/bash
# System backup script: /opt/scripts/backup_system.sh

BACKUP_DIR="/mnt/storage/backups"
DATE=$(date +%Y%m%d_%H%M%S)
CONFIG_BACKUP="system_config_${DATE}.tar.gz"

# Backup important configuration files
tar -czf $BACKUP_DIR/$CONFIG_BACKUP \
    /opt/traffic-monitor/config/ \
    /etc/systemd/system/traffic-monitor*.service \
    /boot/firmware/config.txt \
    /etc/fstab

echo "Configuration backup completed: $CONFIG_BACKUP"
```

#### Recovery Procedures
```bash
# Database recovery
gunzip -c /mnt/storage/backups/traffic_monitor_backup_YYYYMMDD_HHMMSS.sql.gz | \
    psql -h localhost -U traffic_user traffic_monitor

# Configuration recovery
tar -xzf /mnt/storage/backups/system_config_YYYYMMDD_HHMMSS.tar.gz -C /

# Service restart after recovery
sudo systemctl daemon-reload
sudo systemctl restart traffic-monitor-api
sudo systemctl restart traffic-monitor-processor
```

### 4.3. Maintenance Schedule

#### Daily Tasks (Automated)
- Database backup
- Log rotation
- System health monitoring
- Storage usage check

#### Weekly Tasks
```bash
# System updates (can be automated with caution)
sudo apt update && sudo apt list --upgradable
sudo apt upgrade -y

# Log analysis
sudo journalctl --since "1 week ago" | grep ERROR
sudo logrotate /etc/logrotate.conf

# Performance monitoring
iostat -x 1 5  # Check disk I/O
top -b -n 1 | head -20  # Check CPU/memory usage
```

#### Monthly Tasks
- Full system backup
- Security audit
- Performance optimization
- Hardware inspection

### 4.4. Monitoring & Alerting

#### System Health Scripts
```bash
#!/bin/bash
# Health check script: /opt/scripts/health_check.sh

# Check services
systemctl is-active --quiet traffic-monitor-api || echo "API service down"
systemctl is-active --quiet traffic-monitor-processor || echo "Processor service down"

# Check disk space
DISK_USAGE=$(df /mnt/storage | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "Warning: Disk usage at ${DISK_USAGE}%"
fi

# Check temperature
TEMP=$(vcgencmd measure_temp | cut -d= -f2 | cut -d\' -f1)
if [ ${TEMP%.*} -gt 70 ]; then
    echo "Warning: CPU temperature at ${TEMP}°C"
fi
```

### 4.5. Performance Tuning

#### Database Optimization
```sql
-- PostgreSQL performance tuning
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
SELECT pg_reload_conf();
```

#### System Optimization
```bash
# Increase file descriptor limits
echo "* soft nofile 65535" | sudo tee -a /etc/security/limits.conf
echo "* hard nofile 65535" | sudo tee -a /etc/security/limits.conf

# Optimize network settings
echo "net.core.rmem_max = 16777216" | sudo tee -a /etc/sysctl.conf
echo "net.core.wmem_max = 16777216" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```
