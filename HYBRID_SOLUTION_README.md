# Traffic Monitoring Hybrid Solution

**✅ PROVEN WORKING SOLUTION** for Raspberry Pi 5 + IMX500 AI Camera + Docker

## Overview

This hybrid architecture combines the best of both worlds:
- **Host capture**: Native `rpicam-still` for reliable camera access
- **Container processing**: Dockerized ML pipeline for vehicle detection
- **Shared storage**: Seamless data flow between host and container

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Raspberry Pi  │    │  Shared Storage  │    │ Docker Container│
│                 │    │                  │    │                 │
│ rpicam-still ───┼───▶│ /mnt/storage/   │◀───┼─── ML Pipeline  │
│ (Host Capture)  │    │ - images/        │    │ (Processing)    │
│                 │    │ - processed/     │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Quick Start

### 1. Setup (One-time)
```bash
# Clone and setup
cd /home/merk
git clone https://github.com/gcu-merk/CST_590_Computer_Science_Capstone_Project.git
cd CST_590_Computer_Science_Capstone_Project

# Run automated setup
chmod +x scripts/setup-hybrid-solution.sh
./scripts/setup-hybrid-solution.sh
```

### 2. Manual Operation
```bash
# Single capture and process
capture-traffic

# Test mode (check prerequisites)
capture-traffic test

# Capture only (no processing)
capture-traffic capture-only

# Cleanup old files
capture-traffic cleanup
```

### 3. Automated Operation
```bash
# Check timer status
sudo systemctl status traffic-monitoring.timer

# View logs
sudo journalctl -u traffic-monitoring.service -f

# Stop/start timer
sudo systemctl stop traffic-monitoring.timer
sudo systemctl start traffic-monitoring.timer
```

## File Structure

```
/mnt/storage/
├── periodic_snapshots/          # Raw captured images
│   ├── traffic_20250911_192125.jpg
│   └── traffic_20250911_192630.jpg
└── processed/                   # Annotated images (when vehicles detected)
    ├── traffic_20250911_192125_processed.jpg
    └── vehicle_detections.json
```

## Configuration

### Capture Settings
- **Resolution**: 4056x3040 (full IMX500 resolution)
- **Quality**: 95% JPEG
- **Interval**: Every 5 minutes (configurable)
- **Timeout**: 5 seconds per capture attempt
- **Retries**: 3 attempts if capture fails

### Processing Settings
- **Detection threshold**: 0.7 confidence
- **Vehicle types**: Car, truck, motorcycle, bus
- **Annotation**: Bounding boxes + confidence scores
- **Storage**: Automatic cleanup after 7 days

## Monitoring

### Health Checks
```bash
# Container status
docker ps | grep traffic-monitoring

# Storage usage
du -sh /mnt/storage

# Recent captures
ls -la /mnt/storage/periodic_snapshots/ | tail -5

# Container logs
docker logs traffic-monitoring-edge --tail=20
```

### Performance Metrics
```bash
# Capture success rate
grep "✅ Successfully captured" /var/log/syslog | tail -10

# Processing results
grep "vehicles detected" /var/log/syslog | tail -10

# System resources
docker stats traffic-monitoring-edge --no-stream
```

## Troubleshooting

### Common Issues

#### Camera Not Working
```bash
# Test camera directly
rpicam-still -o /tmp/test.jpg --immediate

# Check camera hardware
ls -la /dev/video*
```

#### Container Issues
```bash
# Restart container
docker-compose down && docker-compose up -d

# Check container logs
docker logs traffic-monitoring-edge -f

# Test container access to storage
docker exec traffic-monitoring-edge ls -la /mnt/storage
```

#### Storage Issues
```bash
# Check storage mount
mount | grep /mnt/storage

# Check permissions
ls -la /mnt/storage
sudo chown merk:merk /mnt/storage -R
```

### Log Locations
- **System logs**: `sudo journalctl -u traffic-monitoring.service`
- **Container logs**: `docker logs traffic-monitoring-edge`
- **Capture script logs**: Check syslog or systemd journal

## Advanced Usage

### Custom Processing
```bash
# Process specific image
docker exec traffic-monitoring-edge python3 /app/scripts/process_traffic.py /mnt/storage/image.jpg

# Process with custom output
docker exec traffic-monitoring-edge python3 /app/scripts/process_traffic.py /mnt/storage/image.jpg --output /mnt/storage/custom/
```

### Batch Processing
```bash
# Process all images in directory
for img in /mnt/storage/periodic_snapshots/*.jpg; do
    docker exec traffic-monitoring-edge python3 /app/scripts/process_traffic.py "$img"
done
```

### Custom Scheduling
```bash
# Edit timer interval
sudo systemctl edit traffic-monitoring.timer

# Add custom schedule
[Timer]
OnCalendar=*:0/2  # Every 2 minutes
```

## Performance

### Typical Performance
- **Capture time**: 2-3 seconds
- **Processing time**: 5-10 seconds per image
- **Image size**: 1.4MB (4056x3040)
- **Storage usage**: ~2GB per day (5-minute intervals)

### Optimization Tips
1. **Adjust capture interval** based on traffic patterns
2. **Enable cleanup timer** to manage storage
3. **Monitor container resources** and adjust if needed
4. **Use SSD storage** for better I/O performance

## Integration

### API Access
```bash
# Health check
curl http://localhost:5000/api/health

# Recent detections
curl http://localhost:5000/api/detections

# System status
curl http://localhost:5000/api/status
```

### Data Export
```bash
# Export detection data
docker exec traffic-monitoring-edge python3 -c "
from edge_processing.data_export import export_detections
export_detections('/mnt/storage/exports/detections.json')
"
```

## Success Criteria

✅ **Camera Access**: Native rpicam-still provides reliable image capture  
✅ **Image Quality**: Full 4056x3040 resolution, 1.4MB file size  
✅ **Container Processing**: ML pipeline processes images via shared volumes  
✅ **Automation**: Systemd timer enables unattended operation  
✅ **Monitoring**: Comprehensive logging and health checks  
✅ **Storage Management**: Automatic cleanup and organized file structure  

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review logs using the monitoring commands
3. Test individual components using the manual commands
4. Verify prerequisites with `capture-traffic test`

This hybrid solution has been tested and proven to work reliably on Raspberry Pi 5 with IMX500 AI Camera!
