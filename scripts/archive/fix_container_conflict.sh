#!/bin/bash

echo "=== Quick Fix for Docker Container Conflict ==="
echo "Removing conflicting traffic-monitor container..."

# Remove the specific conflicting container
docker rm -f da5b069e47f129f8219b2018c2c25f2ce69bd4bc365131f1af72e2f8d8d2c5c6 2>/dev/null || true
docker rm -f traffic-monitor 2>/dev/null || true

# Remove other containers that might conflict
docker rm -f redis postgres data-maintenance airport-weather dht22-weather 2>/dev/null || true

# Remove stuck networks
docker network rm traffic_monitoring_traffic-monitoring-network 2>/dev/null || true

echo "Containers and networks cleaned up."
echo ""
echo "Now try your deployment again:"
echo "cd ~/CST_590_Computer_Science_Capstone_Project"
echo "./deployment/deploy.sh"
echo ""
echo "Or use the emergency redeploy script:"
echo "chmod +x scripts/emergency_redeploy.sh"
echo "./scripts/emergency_redeploy.sh"