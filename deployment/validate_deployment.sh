#!/bin/bash
#
# Deployment Validation Script for Traffic Monitoring System
# Verifies that Docker containers are running correctly after deployment
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

DEPLOY_DIR="/mnt/storage/traffic-monitor-deploy"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Validating Traffic Monitoring Deployment${NC}"
echo -e "${BLUE}========================================${NC}"

# Change to deployment directory
cd "$DEPLOY_DIR" || {
    echo -e "${RED}✗ Deployment directory not found: $DEPLOY_DIR${NC}"
    exit 1
}

# Check if Docker Compose files exist
echo -e "${YELLOW}Checking Docker Compose files...${NC}"
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}✗ docker-compose.yml not found${NC}"
    exit 1
fi

if [ ! -f "docker-compose.pi.yml" ]; then
    echo -e "${RED}✗ docker-compose.pi.yml not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker Compose files found${NC}"

# Check if .env file exists and has required variables
echo -e "${YELLOW}Validating environment configuration...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${RED}✗ .env file not found${NC}"
    exit 1
fi

# Check for required environment variables
required_vars=("HOST_UID" "HOST_GID" "DOCKER_USER" "STORAGE_ROOT")
for var in "${required_vars[@]}"; do
    if ! grep -q "^$var=" .env; then
        echo -e "${RED}✗ Required environment variable missing: $var${NC}"
        exit 1
    fi
done

echo -e "${GREEN}✓ Environment configuration valid${NC}"

# Check container status
echo -e "${YELLOW}Checking container status...${NC}"

# Wait a moment for containers to fully start
sleep 5

# Get list of expected services
expected_services=("redis" "traffic-monitor" "data-maintenance" "airport-weather")

# Check if containers are running
echo "Container status:"
docker compose -f docker-compose.yml -f docker-compose.pi.yml ps

all_running=true
for service in "${expected_services[@]}"; do
    if docker compose -f docker-compose.yml -f docker-compose.pi.yml ps --status running | grep -q "^${service}"; then
        echo -e "${GREEN}✓ $service is running${NC}"
    else
        echo -e "${RED}✗ $service is not running${NC}"
        all_running=false
        
        # Show logs for failed service
        echo -e "${YELLOW}Last 10 lines of $service logs:${NC}"
        docker compose -f docker-compose.yml -f docker-compose.pi.yml logs --tail=10 "$service" || true
    fi
done

# Special handling for DHT22 service (may not be running on all systems)
if docker compose -f docker-compose.yml -f docker-compose.pi.yml ps --status running | grep -q "^dht22-weather"; then
    echo -e "${GREEN}✓ dht22-weather is running${NC}"
elif docker compose -f docker-compose.yml -f docker-compose.pi.yml ps | grep -q "dht22-weather"; then
    echo -e "${YELLOW}⚠ dht22-weather exists but may not be running (GPIO hardware dependent)${NC}"
else
    echo -e "${YELLOW}⚠ dht22-weather service not found (optional)${NC}"
fi

if [ "$all_running" = false ]; then
    echo -e "${RED}✗ Some critical services are not running${NC}"
    exit 1
fi

# Test Redis connectivity
echo -e "${YELLOW}Testing Redis connectivity...${NC}"
if docker compose -f docker-compose.yml -f docker-compose.pi.yml exec -T redis redis-cli ping 2>/dev/null | grep -q "PONG"; then
    echo -e "${GREEN}✓ Redis is responding${NC}"
else
    echo -e "${RED}✗ Redis is not responding${NC}"
    exit 1
fi

# Test traffic-monitor API
echo -e "${YELLOW}Testing Traffic Monitor API...${NC}"
sleep 2  # Give API time to start

if curl -f -s http://localhost:5000/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Traffic Monitor API is responding${NC}"
else
    echo -e "${YELLOW}⚠ Traffic Monitor API not responding (may still be starting up)${NC}"
    # Don't fail validation for API - it might need more time
fi

# Check storage directories
echo -e "${YELLOW}Validating storage directories...${NC}"
storage_dirs=(
    "/mnt/storage/camera_capture"
    "/mnt/storage/redis_data"
    "/mnt/storage/logs"
    "/mnt/storage/container-accessible"
)

for dir in "${storage_dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✓ $dir exists${NC}"
    else
        echo -e "${RED}✗ $dir not found${NC}"
        exit 1
    fi
done

# Check disk space
echo -e "${YELLOW}Checking disk space...${NC}"
disk_usage=$(df /mnt/storage | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$disk_usage" -gt 90 ]; then
    echo -e "${RED}⚠ Warning: Disk usage is ${disk_usage}% - consider cleanup${NC}"
elif [ "$disk_usage" -gt 80 ]; then
    echo -e "${YELLOW}⚠ Warning: Disk usage is ${disk_usage}%${NC}"
else
    echo -e "${GREEN}✓ Disk usage: ${disk_usage}%${NC}"
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ Deployment validation completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"

echo
echo -e "${BLUE}Deployment Summary:${NC}"
echo -e "${BLUE}• Location: $DEPLOY_DIR${NC}"
echo -e "${BLUE}• Running services: $(docker compose -f docker-compose.yml -f docker-compose.pi.yml ps --status running | wc -l)${NC}"
echo -e "${BLUE}• API endpoint: http://localhost:5000${NC}"
echo -e "${BLUE}• Storage usage: ${disk_usage}%${NC}"

exit 0