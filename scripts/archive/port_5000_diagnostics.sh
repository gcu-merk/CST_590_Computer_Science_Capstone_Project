#!/bin/bash

echo "=== Detailed Port 5000 Diagnostics ==="
echo "Date: $(date)"
echo

echo "1. Checking what's listening on port 5000..."
sudo netstat -tlnp | grep :5000
echo

echo "2. Checking if it's bound to localhost only..."
sudo ss -tlnp | grep :5000
echo

echo "3. Testing local connection to port 5000..."
curl -v http://localhost:5000/api/health 2>&1 || echo "Local connection failed"
echo

echo "4. Testing connection to 127.0.0.1:5000..."
curl -v http://127.0.0.1:5000/api/health 2>&1 || echo "127.0.0.1 connection failed"
echo

echo "5. Testing connection to external IP..."
curl -v http://100.121.231.16:5000/api/health 2>&1 || echo "External IP connection failed"
echo

echo "6. Checking if there are any Docker containers running..."
docker ps -a
echo

echo "7. Checking Docker compose status..."
cd /mnt/storage/traffic-monitor-deploy 2>/dev/null && docker-compose -f docker-compose.quick-api.yml ps || echo "No compose file or not in correct directory"
echo

echo "8. Checking what process is using port 5000..."
sudo lsof -i :5000 || echo "No process found using lsof"
echo

echo "9. Checking firewall status..."
sudo ufw status || echo "UFW not available"
echo

echo "10. Checking if any Python processes are running..."
ps aux | grep python | grep -v grep
echo

echo "=== Diagnostics Complete ==="