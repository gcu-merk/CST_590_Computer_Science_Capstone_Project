#!/bin/bash
# DHT22 Service Status Check Script
# Run this on your Raspberry Pi to check DHT22 service status

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🌡️ DHT22 Service Status Check${NC}"
echo "=========================================="

echo -e "\n${YELLOW}1. Container Status${NC}"
echo "-------------------"
if docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Health}}" | grep dht22-weather; then
    echo -e "${GREEN}✓ DHT22 container found${NC}"
else
    echo -e "${RED}✗ DHT22 container not running${NC}"
    echo "Checking if container exists but stopped..."
    docker ps -a | grep dht22-weather || echo "No DHT22 container found"
fi

echo -e "\n${YELLOW}2. Recent Container Logs${NC}"
echo "------------------------"
echo "Last 15 lines from DHT22 service:"
docker logs dht22-weather --tail=15 2>/dev/null || echo "Could not retrieve logs"

echo -e "\n${YELLOW}3. Redis Data Check${NC}"
echo "-------------------"
echo "DHT22 hash data:"
docker exec redis redis-cli hgetall "weather:dht22" 2>/dev/null || echo "Could not connect to Redis"

echo -e "\nDHT22 latest JSON data:"
docker exec redis redis-cli get "weather:dht22:latest" 2>/dev/null || echo "Could not retrieve latest data"

echo -e "\n${YELLOW}4. API Endpoint Test${NC}"
echo "--------------------"
echo "Testing DHT22 API endpoint..."
response=$(curl -s "http://localhost:5000/api/weather/dht22" 2>/dev/null)
if echo "$response" | grep -q '"temperature_c"'; then
    echo -e "${GREEN}✓ API endpoint responding${NC}"
    echo "Response: $response"
else
    echo -e "${RED}✗ API endpoint not responding or no data${NC}"
    echo "Response: $response"
fi

echo -e "\n${YELLOW}5. GPIO Hardware Check${NC}"
echo "-----------------------"
echo "GPIO chip devices:"
ls -l /dev/gpiochip* 2>/dev/null || echo "No GPIO chip devices found"

echo -e "\nGPIO memory device:"
ls -l /dev/gpiomem 2>/dev/null || echo "No GPIO memory device found"

echo -e "\nSystem GPIO status:"
if command -v pinctrl &> /dev/null; then
    pinctrl get 4 2>/dev/null || echo "Could not get GPIO 4 status"
else
    echo "pinctrl command not available"
fi

echo -e "\n${YELLOW}6. Service Health Check${NC}"
echo "------------------------"
echo "Running health check command..."
docker exec dht22-weather python3 -c "
import redis
try:
    r = redis.Redis(host='redis', port=6379)
    data = r.hget('weather:dht22', 'timestamp')
    if data:
        print('✓ Health check PASSED - Data found in Redis')
        print(f'Latest timestamp: {data.decode()}')
    else:
        print('✗ Health check FAILED - No data in Redis')
except Exception as e:
    print(f'✗ Health check ERROR: {e}')
" 2>/dev/null || echo "Could not run health check"

echo -e "\n${BLUE}DHT22 Status Check Complete${NC}"
echo "=========================================="