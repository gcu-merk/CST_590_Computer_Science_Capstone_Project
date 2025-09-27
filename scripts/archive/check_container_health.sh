#!/bin/bash

echo "=== Checking Container Health and Logs ==="
echo "Date: $(date)"
echo

echo "1. Checking container health status..."
docker inspect traffic-monitor | grep -A 10 "Health"
echo

echo "2. Getting recent container logs..."
echo "--- Last 50 lines of container logs ---"
docker logs --tail=50 traffic-monitor
echo

echo "3. Getting real-time logs (last 10 seconds)..."
echo "--- Real-time logs ---"
timeout 10s docker logs -f traffic-monitor || echo "Timeout reached"
echo

echo "4. Checking if the container can reach its health endpoint internally..."
docker exec traffic-monitor curl -s http://localhost:5000/api/health || echo "Health check failed inside container"
echo

echo "5. Checking what processes are running inside the container..."
docker exec traffic-monitor ps aux || echo "Cannot exec into container"
echo

echo "6. Checking if Flask app is bound to the right interface..."
docker exec traffic-monitor netstat -tlnp | grep :5000 || echo "Cannot check ports inside container"
echo

echo "=== Container Diagnostics Complete ==="