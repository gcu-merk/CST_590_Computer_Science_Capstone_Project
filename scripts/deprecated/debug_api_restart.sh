#!/bin/bash

echo "=== Deploying API Server Debugging Fix ==="
echo "Date: $(date)"
echo

# Navigate to the correct project directory
cd /mnt/storage/traffic-monitor-deploy || exit 1

echo "1. Pulling latest code with enhanced logging..."
git pull origin main
echo

echo "2. Stopping current container to restart with new code..."
docker stop traffic-monitor || echo "Container may not be running"
echo

echo "3. Removing old container..."
docker rm traffic-monitor || echo "Container may not exist"
echo

echo "4. Pulling latest Docker image..."
docker pull gcumerk/cst590-capstone-public:latest || echo "Using existing image"
echo

echo "5. Starting container with enhanced logging..."
docker run -d \
  --name traffic-monitor \
  --network traffic-monitor_default \
  -p 5000:5000 \
  -v /mnt/storage:/mnt/storage \
  -e CAMERA_FREE_MODE=true \
  -e REDIS_HOST=redis \
  -e POSTGRES_HOST=postgres \
  -e POSTGRES_DB=traffic_monitoring \
  -e POSTGRES_USER=traffic_user \
  -e POSTGRES_PASSWORD=secure_password \
  --health-cmd="curl -f http://localhost:5000/api/health || exit 1" \
  --health-interval=30s \
  --health-timeout=10s \
  --health-start-period=60s \
  --health-retries=3 \
  gcumerk/cst590-capstone-public:latest
echo

echo "6. Waiting for container to start..."
sleep 15

echo "7. Checking new container logs for API server thread messages..."
docker logs --tail=30 traffic-monitor

echo
echo "8. Checking if port 5000 is listening..."
netstat -tlnp | grep :5000 || echo "Port 5000 not listening yet"

echo
echo "=== Deployment Complete ==="
echo "Check the logs above for API server thread status messages"
echo "Test Swagger API at: http://100.121.231.16:5000/docs/"