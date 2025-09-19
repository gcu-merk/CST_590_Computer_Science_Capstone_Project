#!/bin/bash

echo "=== Fixing CI/CD Container Conflicts ==="
echo "Date: $(date)"
echo

echo "1. Stopping all conflicting containers..."
docker stop traffic-monitor redis postgres || echo "Some containers may not be running"
echo

echo "2. Removing conflicting containers..."
docker rm traffic-monitor redis postgres || echo "Some containers may not exist"
echo

echo "3. Cleaning up any conflicting networks..."
docker network rm traffic-monitor_default traffic_monitoring_traffic-monitoring-network || echo "Networks may not exist"
echo

echo "4. Moving to deployment staging directory..."
cd /mnt/storage/deployment-staging || exit 1
echo

echo "5. Starting fresh deployment with latest image (has our fixes)..."
docker-compose -f docker-compose.pi.yml up -d
echo

echo "6. Waiting for containers to start..."
sleep 20

echo "7. Checking new container status..."
docker-compose -f docker-compose.pi.yml ps
echo

echo "8. Checking for our enhanced logging in new traffic-monitor..."
docker logs --tail=30 traffic-monitor | grep -E "🚀|📋|✅|❌|🧵|🔍" || echo "Enhanced logging not found yet"
echo

echo "9. Testing port 5000 accessibility..."
netstat -tlnp | grep :5000 || echo "Port 5000 not listening yet"
echo

echo "=== Deployment Fix Complete ==="
echo "The latest image with our fixes should now be running!"
echo "Test Swagger at: http://100.121.231.16:5000/docs/"

echo ""
echo "=== Waiting 30 seconds for startup ==="
sleep 30

echo ""
echo "=== Checking container status ==="
docker ps

echo ""
echo "=== Testing API endpoint ==="
curl -I http://localhost:5000/ || echo "API not responding yet"

echo ""
echo "=== Swagger endpoint test ==="
curl -I http://localhost:5000/docs/ || echo "Swagger not available - checking fallback"

echo ""
echo "=== Container logs if still failing ==="
docker logs traffic-monitor --tail 20