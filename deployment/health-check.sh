#!/bin/bash
# Complete system health check for traffic monitoring system

echo "🏥 Traffic Monitoring System - Health Check"
echo "==========================================="

# Complete system status check
echo "=== Host Camera Service ==="
sudo systemctl status host-camera-capture --no-pager

echo "=== Docker Services ==="
docker-compose ps

echo "=== Recent Captures ==="
ls -la /mnt/storage/camera_capture/live/ | tail -5

echo "=== Storage Usage ==="
du -sh /mnt/storage/camera_capture/

echo "=== API Health ==="
curl -s http://localhost:5000/api/health | python3 -m json.tool

echo "=== System Resources ==="
echo "Memory usage:"
free -h

echo "CPU usage:"
top -bn1 | grep "Cpu(s)" || echo "CPU info not available"

echo "Disk usage:"
df -h /mnt/storage

echo "=== Service Logs (last 5 lines) ==="
echo "Host camera service:"
sudo journalctl -u host-camera-capture -n 5 --no-pager

echo "Docker logs:"
docker-compose logs --tail=5

echo "==========================================="
echo "Health check completed at $(date)"