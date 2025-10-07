#!/bin/bash
#
# Vehicle Detection Workflow Monitor - Shell Script Version
# Comprehensive end-to-end monitoring from radar detection to API output
# Designed to run directly on the Raspberry Pi
#

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MONITOR_INTERVAL=5
DB_PATH="/app/data/traffic_data.db"
API_URL="http://localhost/api/recent-detections"

# Function to print timestamped messages
log_message() {
    echo -e "[$(date '+%H:%M:%S')] $1"
}

# Function to check Docker container health
check_docker_containers() {
    echo -e "\n${BLUE}🐳 DOCKER CONTAINERS:${NC}"
    
    # Key containers for the workflow
    containers=("redis" "vehicle-consolidator" "database-persistence" "realtime-events-broadcaster" "traffic-monitor" "radar-service" "nginx-proxy")
    
    for container in "${containers[@]}"; do
        if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "$container"; then
            status=$(docker ps --format "table {{.Names}}\t{{.Status}}" | grep "$container" | awk '{print $2}')
            if echo "$status" | grep -q "healthy"; then
                echo -e "  ${GREEN}✅${NC} $container: Healthy"
            elif echo "$status" | grep -q "Up"; then
                echo -e "  ${YELLOW}🟡${NC} $container: Running"
            else
                echo -e "  ${RED}❌${NC} $container: $status"
            fi
        else
            echo -e "  ${RED}❌${NC} $container: Not Running"
        fi
    done
}

# Function to check camera service
check_camera_service() {
    echo -e "\n${BLUE}📷 CAMERA SERVICE:${NC}"
    
    if systemctl is-active --quiet imx500-ai-capture; then
        echo -e "  ${GREEN}✅${NC} IMX500 Camera Service: Active"
        
        # Get service uptime
        uptime=$(systemctl show imx500-ai-capture --property=ActiveEnterTimestamp --value | cut -d' ' -f2-3)
        echo -e "  📊 Started: $uptime"
    else
        echo -e "  ${RED}❌${NC} IMX500 Camera Service: Inactive"
        
        # Show recent service logs
        echo -e "  📋 Recent logs:"
        systemctl status imx500-ai-capture --no-pager -l | tail -3 | sed 's/^/    /'
    fi
}

# Function to check Redis connectivity and channels
check_redis_channels() {
    echo -e "\n${BLUE}📡 REDIS CHANNELS:${NC}"
    
    # Check Redis connectivity
    if docker exec redis redis-cli ping >/dev/null 2>&1; then
        echo -e "  ${GREEN}✅${NC} Redis: Connected"
        
        # Check key channels
        channels=("traffic:radar" "camera_requests" "camera_responses")
        
        for channel in "${channels[@]}"; do
            count=$(docker exec redis redis-cli llen "$channel" 2>/dev/null || echo "0")
            if [ "$count" -gt 0 ]; then
                echo -e "  📨 $channel: $count messages"
            else
                echo -e "  📭 $channel: empty"
            fi
        done
        
        # Show recent radar detections
        echo -e "\n  🎯 Recent Radar Activity:"
        recent_radar=$(docker exec redis redis-cli lrange "traffic:radar" 0 2 2>/dev/null | head -3)
        if [ -n "$recent_radar" ]; then
            echo "$recent_radar" | while read -r line; do
                if echo "$line" | grep -q "correlation_id"; then
                    correlation_id=$(echo "$line" | grep -o '"correlation_id":"[^"]*"' | cut -d'"' -f4)
                    timestamp=$(echo "$line" | grep -o '"timestamp":"[^"]*"' | cut -d'"' -f4)
                    speed=$(echo "$line" | grep -o '"speed_mph":[0-9.]*' | cut -d':' -f2)
                    echo -e "    🚗 $correlation_id at $speed mph ($timestamp)"
                fi
            done
        else
            echo -e "    📭 No recent radar detections"
        fi
        
    else
        echo -e "  ${RED}❌${NC} Redis: Connection Failed"
    fi
}

# Function to check database activity
check_database_activity() {
    echo -e "\n${BLUE}🗄️ DATABASE ACTIVITY:${NC}"
    
    # Recent detections count
    recent_count=$(docker exec database-persistence sqlite3 "$DB_PATH" \
        "SELECT COUNT(*) FROM traffic_detections WHERE timestamp > datetime('now', '-1 hour');" 2>/dev/null || echo "0")
    
    echo -e "  📊 Last hour: $recent_count detections"
    
    # Most recent detection
    recent_detection=$(docker exec database-persistence sqlite3 "$DB_PATH" \
        "SELECT timestamp, vehicle_type, correlation_id FROM traffic_detections ORDER BY timestamp DESC LIMIT 1;" 2>/dev/null)
    
    if [ -n "$recent_detection" ]; then
        timestamp=$(echo "$recent_detection" | cut -d'|' -f1)
        vehicle_type=$(echo "$recent_detection" | cut -d'|' -f2)
        correlation_id=$(echo "$recent_detection" | cut -d'|' -f3)
        echo -e "  🚗 Latest: $vehicle_type at $timestamp (ID: $correlation_id)"
    else
        echo -e "  📭 No recent detections in database"
    fi
    
    # Check for correlation between radar and final detections
    radar_count=$(docker exec database-persistence sqlite3 "$DB_PATH" \
        "SELECT COUNT(*) FROM radar_detections WHERE detected_at > datetime('now', '-1 hour');" 2>/dev/null || echo "0")
    
    echo -e "  🎯 Radar vs Final: $radar_count radar → $recent_count final (correlation rate: $(echo "scale=1; $recent_count * 100 / ($radar_count + 1)" | bc 2>/dev/null || echo "N/A")%)"
}

# Function to check API endpoint
check_api_endpoint() {
    echo -e "\n${BLUE}🌐 API ENDPOINT:${NC}"
    
    # Check API health
    if response=$(curl -s -w "%{http_code}" "$API_URL" -o /tmp/api_response.json --max-time 10); then
        http_code="${response: -3}"
        
        if [ "$http_code" = "200" ]; then
            echo -e "  ${GREEN}✅${NC} API: Healthy (HTTP $http_code)"
            
            # Parse response for detection count
            if command -v jq >/dev/null 2>&1; then
                detection_count=$(jq '.detections | length' /tmp/api_response.json 2>/dev/null || echo "unknown")
                echo -e "  📊 Current detections available: $detection_count"
                
                # Show latest detection from API
                latest_api=$(jq -r '.detections[0] | "\(.timestamp) - \(.vehicle_type) (\(.correlation_id))"' /tmp/api_response.json 2>/dev/null)
                if [ "$latest_api" != "null" ] && [ -n "$latest_api" ]; then
                    echo -e "  🚗 Latest via API: $latest_api"
                fi
            else
                echo -e "  📊 Response received (jq not available for parsing)"
            fi
        else
            echo -e "  ${RED}❌${NC} API: Error (HTTP $http_code)"
        fi
    else
        echo -e "  ${RED}❌${NC} API: Connection Failed"
    fi
    
    rm -f /tmp/api_response.json
}

# Function to check system resources
check_system_resources() {
    echo -e "\n${BLUE}💻 SYSTEM RESOURCES:${NC}"
    
    # CPU and Memory
    cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    memory_usage=$(free | grep Mem | awk '{printf "%.1f", ($3/$2) * 100.0}')
    
    echo -e "  🖥️ CPU: ${cpu_usage}% used"
    echo -e "  🧠 Memory: ${memory_usage}% used"
    
    # Disk space on SSD
    disk_usage=$(df -h /mnt/storage | tail -1 | awk '{print $5}' | sed 's/%//')
    disk_available=$(df -h /mnt/storage | tail -1 | awk '{print $4}')
    
    if [ "$disk_usage" -gt 90 ]; then
        echo -e "  ${RED}💾 SSD: ${disk_usage}% used (${disk_available} free)${NC}"
    elif [ "$disk_usage" -gt 75 ]; then
        echo -e "  ${YELLOW}💾 SSD: ${disk_usage}% used (${disk_available} free)${NC}"
    else
        echo -e "  ${GREEN}💾 SSD: ${disk_usage}% used (${disk_available} free)${NC}"
    fi
}

# Function to check container logs for errors
check_recent_errors() {
    echo -e "\n${BLUE}🚨 RECENT ERRORS:${NC}"
    
    # Check key containers for recent errors
    containers=("vehicle-consolidator" "radar-service" "database-persistence")
    error_found=false
    
    for container in "${containers[@]}"; do
        if docker ps --format "table {{.Names}}" | grep -q "$container"; then
            errors=$(docker logs "$container" --since="5m" 2>&1 | grep -i "error\|exception\|traceback" | tail -2)
            if [ -n "$errors" ]; then
                echo -e "  ${RED}❌ $container:${NC}"
                echo "$errors" | sed 's/^/    /'
                error_found=true
            fi
        fi
    done
    
    if [ "$error_found" = false ]; then
        echo -e "  ${GREEN}✅${NC} No recent errors in container logs"
    fi
}

# Function to display workflow correlation
show_workflow_correlation() {
    echo -e "\n${BLUE}🔄 WORKFLOW CORRELATION:${NC}"
    
    # Get recent activity from last 10 minutes
    echo -e "  📊 Activity in last 10 minutes:"
    
    # Radar detections
    radar_recent=$(docker exec database-persistence sqlite3 "$DB_PATH" \
        "SELECT COUNT(*) FROM radar_detections WHERE detected_at > datetime('now', '-10 minutes');" 2>/dev/null || echo "0")
    
    # Camera requests (check Redis)
    camera_requests=$(docker exec redis redis-cli llen "camera_requests" 2>/dev/null || echo "0")
    
    # Final detections
    final_recent=$(docker exec database-persistence sqlite3 "$DB_PATH" \
        "SELECT COUNT(*) FROM traffic_detections WHERE timestamp > datetime('now', '-10 minutes');" 2>/dev/null || echo "0")
    
    echo -e "    🎯 Radar detections: $radar_recent"
    echo -e "    📷 Camera requests queued: $camera_requests"
    echo -e "    ✅ Final detections: $final_recent"
    
    # Calculate success rate
    if [ "$radar_recent" -gt 0 ]; then
        success_rate=$(echo "scale=1; $final_recent * 100 / $radar_recent" | bc 2>/dev/null || echo "N/A")
        echo -e "    📈 Success rate: ${success_rate}%"
    fi
}

# Main monitoring loop
main_monitor() {
    echo -e "${GREEN}🚀 Vehicle Detection Workflow Monitor${NC}"
    echo -e "${GREEN}=====================================${NC}"
    echo "Press Ctrl+C to stop monitoring"
    echo ""
    
    # Handle Ctrl+C gracefully
    trap 'echo -e "\n${YELLOW}👋 Monitoring stopped${NC}"; exit 0' INT TERM
    
    while true; do
        # Clear screen and show header
        clear
        echo -e "${GREEN}🚗 Vehicle Detection System - $(date '+%Y-%m-%d %H:%M:%S')${NC}"
        echo -e "${GREEN}=============================================================${NC}"
        
        # Run all checks
        check_docker_containers
        check_camera_service
        check_redis_channels
        check_database_activity
        check_api_endpoint
        check_system_resources
        check_recent_errors
        show_workflow_correlation
        
        echo -e "\n${BLUE}⏱️ Next update in ${MONITOR_INTERVAL} seconds... (Ctrl+C to stop)${NC}"
        
        # Wait for next iteration
        sleep $MONITOR_INTERVAL
    done
}

# Run the monitor
main_monitor