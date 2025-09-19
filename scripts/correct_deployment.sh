#!/bin/bash

echo "=== Fixed Deployment with Correct Compose Files ==="
echo "Date: $(date)"
echo

echo "1. Moving to deployment staging directory..."
cd /mnt/storage/deployment-staging || exit 1
pwd
echo

echo "2. Checking environment variables..."
echo "--- .env file content ---"
cat .env
echo

echo "3. Using both compose files (base + Pi overlay)..."
echo "Starting with: docker-compose.yml + docker-compose.pi.yml"
docker-compose -f docker-compose.yml -f docker-compose.pi.yml up -d
echo

echo "4. Waiting for containers to start..."
sleep 25

echo "5. Checking container status..."
docker-compose -f docker-compose.yml -f docker-compose.pi.yml ps
echo

echo "6. Checking if traffic-monitor is running..."
docker ps | grep traffic-monitor || echo "Traffic-monitor not running"
echo

echo "7. Checking for our enhanced logging..."
docker logs --tail=20 traffic-monitor | grep -E "🚀|📋|✅|❌|🧵|🔍" || echo "Enhanced logging not found yet"
echo

echo "8. Testing port 5000..."
netstat -tlnp | grep :5000 || echo "Port 5000 not listening yet"
echo

echo "9. Quick API test..."
curl -s http://localhost:5000/api/health || echo "API not responding yet"
echo

echo "=== Deployment Complete ==="
echo "Test Swagger at: http://100.121.231.16:5000/docs/"