#!/bin/bash

echo "=== Non-Intrusive API Debugging ==="
echo "Date: $(date)"
echo

echo "1. Current container status (no changes)..."
docker ps -a | grep traffic-monitor
echo

echo "2. Recent container logs (last 20 lines)..."
docker logs --tail=20 traffic-monitor
echo

echo "3. Check what the container thinks is running on port 5000..."
docker exec traffic-monitor bash -c "ps aux | grep -v grep | grep python" 2>/dev/null || echo "Cannot exec into container"
echo

echo "4. Test internal connectivity without restarting anything..."
docker exec traffic-monitor bash -c "curl -s -m 5 http://localhost:5000/api/health" 2>/dev/null || echo "Internal API test failed"
echo

echo "5. Check if Flask is bound correctly inside container..."
docker exec traffic-monitor bash -c "netstat -tlnp | grep :5000" 2>/dev/null || echo "Cannot check internal ports"
echo

echo "6. External connectivity test..."
timeout 5s curl -v http://localhost:5000/api/health 2>&1 | head -5 || echo "External connection failed"
echo

echo "=== Safe Diagnosis Complete ==="
echo "No CI/CD conflicts - just gathering information"
echo "If API server thread isn't starting, it's likely a code issue in the image"