#!/bin/bash
# Quick Fix Script for Deployment Issues
# Run this on the Raspberry Pi if containers aren't starting

echo "=== Stopping all containers ==="
cd /home/merk/CST_590_Computer_Science_Capstone_Project
docker-compose down

echo ""
echo "=== Cleaning up old containers ==="
docker container prune -f

echo ""
echo "=== Pulling latest image ==="
docker pull gcumerk/cst590-capstone-public:latest

echo ""
echo "=== Starting services ==="
docker-compose -f docker-compose.yml -f docker-compose.pi.yml up -d

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