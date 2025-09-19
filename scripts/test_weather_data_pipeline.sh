#!/bin/bash
# Weather Data Pipeline Test Script
# Tests DHT22 sensor, weather.gov API, and local API endpoint

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

echo -e "\n${YELLOW}🌡️ 1. DHT22 & Weather.gov Data Collection${NC}"
echo "----------------------------------------"
python3 edge_processing/weather_data_collector.py > /tmp/weather_test.json 2>&1
if grep -q '"dht22"' /tmp/weather_test.json && grep -q '"weather_api"' /tmp/weather_test.json; then
    print_result 0 "Weather Data Collector Script"
else
    print_result 1 "Weather Data Collector Script"
fi

echo -e "\n${YELLOW}🌐 2. Local API Endpoint Test${NC}"
echo "----------------------------------------"
API_URL="http://localhost:5000/api/weather/latest"
response=$(curl -s "$API_URL")
if echo "$response" | grep -q '"dht22"' && echo "$response" | grep -q '"weather_api"'; then
    print_result 0 "Weather API Endpoint (/api/weather/latest)"
else
    print_result 1 "Weather API Endpoint (/api/weather/latest)"
    echo "    Output: $response"
fi

echo -e "\n${BLUE}Tests Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Tests Failed: $TESTS_FAILED${NC}"
