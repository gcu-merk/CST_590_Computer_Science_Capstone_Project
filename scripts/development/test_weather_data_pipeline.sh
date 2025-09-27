#!/bin/bash
# Weather Data Pipeline Test Script
# Tests DHT22 service, airport weather service, and API endpoints

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

TESTS_PASSED=0
TESTS_FAILED=0

print_result() {
    if [ $1 -eq 0 ]; then
        echo -e "  ${GREEN}✓ PASS${NC}: $2"
        ((TESTS_PASSED++))
    else
        echo -e "  ${RED}✗ FAIL${NC}: $2"
        ((TESTS_FAILED++))
    fi
}

echo -e "\n${YELLOW}🌡️ 1. DHT22 Service Data Check${NC}"
echo "----------------------------------------"
# Test DHT22 service data in Redis
dht22_data=$(docker exec redis redis-cli get "weather:dht22:latest" 2>/dev/null)
if echo "$dht22_data" | grep -q '"temperature_c"' && echo "$dht22_data" | grep -q '"humidity"'; then
    print_result 0 "DHT22 Service Data"
else
    print_result 1 "DHT22 Service Data"
    echo "    Note: DHT22 service may not be running or data not yet collected"
fi

echo -e "\n${YELLOW}🌐 2. Airport Weather Service Data Check${NC}"
echo "----------------------------------------"
# Test Airport weather service data in Redis
airport_data=$(docker exec redis redis-cli get "weather:airport:latest" 2>/dev/null)
if echo "$airport_data" | grep -q '"temperature"' && echo "$airport_data" | grep -q '"timestamp"'; then
    print_result 0 "Airport Weather Service Data"
else
    print_result 1 "Airport Weather Service Data"
    echo "    Note: Airport weather service may not be running or data not yet collected"
fi

echo -e "\n${YELLOW}🔗 3. DHT22 API Endpoint Test${NC}"
echo "----------------------------------------"
API_URL="http://localhost:5000/api/weather/dht22"
response=$(curl -s "$API_URL")
if echo "$response" | grep -q '"temperature_c"' && echo "$response" | grep -q '"humidity"'; then
    print_result 0 "DHT22 API Endpoint (/api/weather/dht22)"
else
    print_result 1 "DHT22 API Endpoint (/api/weather/dht22)"
    echo "    Output: $response"
fi

echo -e "\n${YELLOW}🔗 4. Airport Weather API Endpoint Test${NC}"
echo "----------------------------------------"
API_URL="http://localhost:5000/api/weather/airport"
response=$(curl -s "$API_URL")
if echo "$response" | grep -q '"data"' && echo "$response" | grep -q '"source"'; then
    print_result 0 "Airport Weather API Endpoint (/api/weather/airport)"
else
    print_result 1 "Airport Weather API Endpoint (/api/weather/airport)"
    echo "    Output: $response"
fi

echo -e "\n${BLUE}Tests Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Tests Failed: $TESTS_FAILED${NC}"
