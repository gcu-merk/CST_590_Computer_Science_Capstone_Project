#!/bin/bash
# Deployment Diagnostic Script
# Run this on the Raspberry Pi to check deployment status

echo "=== Docker Container Status ==="
docker ps -a

echo ""
echo "=== Traffic Monitor Container Logs (last 30 lines) ==="
docker logs traffic-monitor --tail 30

echo ""
echo "=== Redis Container Status ==="
docker logs redis --tail 10

echo ""
echo "=== PostgreSQL Container Status ==="
docker logs postgres --tail 10

echo ""
echo "=== Port 5000 Status ==="
netstat -tlnp | grep :5000 || echo "Port 5000 not in use"

echo ""
echo "=== Docker Compose Status ==="
cd /home/merk/CST_590_Computer_Science_Capstone_Project
docker-compose ps

echo ""
echo "=== Recent Docker Images ==="
docker images | head -5

echo ""
echo "=== System Resources ==="
free -h
df -h /

echo ""
echo "=== Check if services are defined ==="
docker-compose config --services