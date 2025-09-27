#!/bin/bash

echo "=== Checking Container Code Version vs Latest Push ==="
echo "Date: $(date)"
echo

echo "1. Latest commit we just pushed:"
git rev-parse HEAD
echo

echo "2. Checking if container has our latest code..."
docker exec traffic-monitor bash -c "cd /app 2>/dev/null || cd /; git rev-parse HEAD 2>/dev/null" || echo "Cannot check git in container"
echo

echo "3. Looking for our enhanced logging in container..."
docker exec traffic-monitor grep -n "🚀 API server thread starting" main_edge_app.py 2>/dev/null || echo "Enhanced logging NOT found - container has old code"
echo

echo "4. Container creation time..."
docker inspect traffic-monitor --format '{{.Created}}' 2>/dev/null || echo "Cannot inspect container"
echo

echo "5. Container image info..."
docker inspect traffic-monitor --format '{{.Config.Image}}' 2>/dev/null || echo "Cannot get image info"
echo

echo "=== Status Summary ==="
echo "If enhanced logging is NOT found, the container is running old code"
echo "This means the API server threading issue persists"
echo "We need the CI/CD to succeed or manually update the container"