#!/bin/bash

echo "=== Restarting Container with Swagger Fixes ==="
echo "Date: $(date)"
echo

echo "1. Moving to deployment staging directory..."
cd /mnt/storage/deployment-staging || exit 1

echo "2. Pulling latest code with Swagger fixes..."
git pull origin main
echo

echo "3. Stopping current containers..."
docker-compose -f docker-compose.yml -f docker-compose.pi.yml down
echo

echo "4. Rebuilding with latest code (if needed)..."
docker-compose -f docker-compose.yml -f docker-compose.pi.yml build --no-cache traffic-monitor || echo "Using existing image"
echo

echo "5. Starting containers with Swagger fixes..."
docker-compose -f docker-compose.yml -f docker-compose.pi.yml up -d
echo

echo "6. Waiting for container to start..."
sleep 15

echo "7. Testing swagger.json endpoint..."
curl -v http://localhost:5000/swagger.json 2>&1 | head -10
echo

echo "8. Testing Swagger UI..."
curl -s http://localhost:5000/docs/ | grep -i swagger || echo "Swagger UI not accessible"
echo

echo "=== Restart Complete ==="
echo "Test Swagger at: http://100.121.231.16:5000/docs/"
echo "If still failing, check container logs: docker logs traffic-monitor"