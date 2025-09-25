#!/bin/bash

echo "=== Emergency Docker Cleanup & Redeploy Script ==="
echo "This script forcefully cleans up Docker conflicts and redeploys"
echo "Date: $(date)"
echo

# Navigate to project directory
cd ~/CST_590_Computer_Science_Capstone_Project || {
    echo "Error: Could not find project directory"
    exit 1
}

echo "1. Forcefully stopping and removing all traffic monitoring containers..."

# Force remove specific containers that are causing conflicts
docker rm -f traffic-monitor redis postgres data-maintenance airport-weather dht22-weather 2>/dev/null || true

echo "2. Removing stuck networks..."

# Remove networks that might be stuck
docker network rm traffic_monitoring_traffic-monitoring-network 2>/dev/null || true
docker network rm traffic-monitoring-network 2>/dev/null || true
docker network rm traffic_monitoring_default 2>/dev/null || true

echo "3. Cleaning up Docker system..."

# Prune unused resources
docker system prune -f

echo "4. Pulling latest code..."

# Get latest code
git pull origin main

echo "5. Pulling latest Docker image..."

# Pull latest image
docker pull gcumerk/cst590-capstone-public:latest

echo "6. Starting fresh deployment..."

# Try deployment methods in order of preference

# Method 1: Try the main deployment script
if [ -f "deployment/deploy.sh" ]; then
    echo "Using main deployment script..."
    chmod +x deployment/deploy.sh
    if ./deployment/deploy.sh; then
        echo "✓ Deployment successful via main script"
        exit 0
    else
        echo "✗ Main deployment script failed, trying alternative..."
    fi
fi

# Method 2: Try direct docker-compose
echo "Trying direct docker-compose deployment..."
if [ -f "docker-compose.yml" ]; then
    # Use same environment variables as deployment script
    export HOST_UID=1000
    export HOST_GID=1000
    export STORAGE_ROOT=/mnt/storage
    
    # Try with Pi-specific compose if GPIO available
    if [ -e "/dev/gpiochip4" ] && [ -f "docker-compose.pi.yml" ]; then
        echo "Using Raspberry Pi configuration..."
        if docker compose -f docker-compose.yml -f docker-compose.pi.yml up -d; then
            echo "✓ Deployment successful via docker-compose with Pi config"
            exit 0
        fi
    else
        echo "Using standard configuration..."
        if docker compose -f docker-compose.yml up -d; then
            echo "✓ Deployment successful via docker-compose"
            exit 0
        fi
    fi
fi

# Method 3: Try quick API deployment
echo "Trying quick API deployment..."
if [ -f "docker-compose.quick-api.yml" ]; then
    if docker compose -f docker-compose.quick-api.yml up -d; then
        echo "✓ Quick API deployment successful"
        exit 0
    fi
fi

echo "✗ All deployment methods failed"
echo "Manual steps needed:"
echo "1. Check Docker daemon: sudo systemctl status docker"
echo "2. Check disk space: df -h"
echo "3. Check container logs: docker logs <container_name>"
echo "4. Try manual container start: docker run gcumerk/cst590-capstone-public:latest"

exit 1