#!/bin/bash
# Remote DHT22 Service Status Check Script
# Check DHT22 service status on Raspberry Pi at 100.121.231.16

PI_IP="100.121.231.16"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🌡️ Remote DHT22 Service Status Check${NC}"
echo -e "${BLUE}Raspberry Pi: ${PI_IP}${NC}"
echo "=========================================="

echo -e "\n${YELLOW}1. Testing Pi Connectivity${NC}"
echo "----------------------------"
if ping -c 2 $PI_IP > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Pi is reachable at ${PI_IP}${NC}"
else
    echo -e "${RED}✗ Pi is not reachable at ${PI_IP}${NC}"
    exit 1
fi

echo -e "\n${YELLOW}2. DHT22 API Endpoint Test${NC}"
echo "----------------------------"
API_URL="http://${PI_IP}:5000/api/weather/dht22"
echo "Testing: $API_URL"
response=$(curl -s --connect-timeout 10 "$API_URL" 2>/dev/null)
if echo "$response" | grep -q '"temperature_c"'; then
    echo -e "${GREEN}✓ DHT22 API endpoint responding${NC}"
    echo "Response: $response" | jq . 2>/dev/null || echo "Response: $response"
else
    echo -e "${RED}✗ DHT22 API endpoint not responding or no data${NC}"
    echo "Response: $response"
fi

echo -e "\n${YELLOW}3. Combined Weather API Test${NC}"
echo "------------------------------"
API_URL="http://${PI_IP}:5000/api/weather/latest"
echo "Testing: $API_URL"
response=$(curl -s --connect-timeout 10 "$API_URL" 2>/dev/null)
if echo "$response" | grep -q '"weather_latest"'; then
    echo -e "${GREEN}✓ Combined weather API responding${NC}"
    # Extract just the DHT22 data if present
    dht22_data=$(echo "$response" | jq '.weather_latest.weather_dht22' 2>/dev/null)
    if [ "$dht22_data" != "null" ] && [ "$dht22_data" != "" ]; then
        echo "DHT22 data from combined endpoint: $dht22_data"
    else
        echo "No DHT22 data in combined endpoint"
    fi
else
    echo -e "${RED}✗ Combined weather API not responding${NC}"
    echo "Response: $response"
fi

echo -e "\n${YELLOW}4. System Health Check${NC}"
echo "------------------------"
API_URL="http://${PI_IP}:5000/api/health"
echo "Testing: $API_URL"
response=$(curl -s --connect-timeout 10 "$API_URL" 2>/dev/null)
if echo "$response" | grep -q '"status"'; then
    echo -e "${GREEN}✓ System health endpoint responding${NC}"
    echo "Health status: $response" | jq . 2>/dev/null || echo "Health status: $response"
else
    echo -e "${RED}✗ System health endpoint not responding${NC}"
    echo "Response: $response"
fi

echo -e "\n${YELLOW}5. Swagger UI Check${NC}"
echo "--------------------"
SWAGGER_URL="http://${PI_IP}:5000/"
echo "Testing Swagger UI: $SWAGGER_URL"
if curl -s --connect-timeout 10 "$SWAGGER_URL" | grep -q "swagger" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Swagger UI is accessible${NC}"
    echo "Visit: $SWAGGER_URL"
else
    echo -e "${RED}✗ Swagger UI not accessible${NC}"
fi

echo -e "\n${YELLOW}6. Port Connectivity Check${NC}"
echo "-----------------------------"
echo "Checking if port 5000 is open..."
if nc -z -w5 $PI_IP 5000 2>/dev/null; then
    echo -e "${GREEN}✓ Port 5000 is open${NC}"
else
    echo -e "${RED}✗ Port 5000 is not accessible${NC}"
fi

echo -e "\n${BLUE}If you need to check container status directly on the Pi:${NC}"
echo "ssh to ${PI_IP} and run:"
echo "  docker ps | grep dht22"
echo "  docker logs dht22-weather --tail=10"
echo "  docker exec redis redis-cli get \"weather:dht22:latest\""

echo -e "\n${BLUE}Remote DHT22 Status Check Complete${NC}"
echo "=========================================="