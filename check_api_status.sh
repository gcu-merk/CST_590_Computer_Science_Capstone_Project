#!/bin/bash

echo "=== Container Status Check ==="
echo "Checking running containers:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo -e "\n=== Container Health Check ==="
echo "Checking traffic-monitor container specifically:"
docker ps --filter name=traffic-monitor --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo -e "\n=== Port Binding Check ==="
echo "Checking if port 5000 is bound:"
netstat -tlnp | grep :5000 || echo "Port 5000 not found in netstat"

echo -e "\n=== Container Logs (Last 20 lines) ==="
echo "Traffic-monitor container logs:"
docker logs --tail=20 traffic-monitor 2>&1

echo -e "\n=== Network Connectivity Test ==="
echo "Testing local API access from host:"
curl -s -o /dev/null -w "HTTP Status: %{http_code}, Time: %{time_total}s\n" http://localhost:5000/api/health || echo "Localhost connection failed"

echo "Testing container IP access:"
CONTAINER_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' traffic-monitor)
echo "Container IP: $CONTAINER_IP"
if [ ! -z "$CONTAINER_IP" ]; then
    curl -s -o /dev/null -w "HTTP Status: %{http_code}, Time: %{time_total}s\n" http://$CONTAINER_IP:5000/api/health || echo "Container IP connection failed"
fi

echo -e "\n=== Docker Network Check ==="
echo "Checking Docker networks:"
docker network ls

echo -e "\n=== Container Inspection ==="
echo "Checking traffic-monitor container configuration:"
docker inspect traffic-monitor --format='{{.State.Status}}: {{.State.Error}}'
docker inspect traffic-monitor --format='Ports: {{.NetworkSettings.Ports}}'

echo -e "\n=== Process Check Inside Container ==="
echo "Checking processes inside traffic-monitor container:"
docker exec traffic-monitor ps aux | grep -E "(python|flask)" || echo "Could not check container processes"

echo -e "\n=== API Endpoint Test ==="
echo "Testing API endpoints directly:"
docker exec traffic-monitor curl -s http://localhost:5000/api/health || echo "Internal container API test failed"