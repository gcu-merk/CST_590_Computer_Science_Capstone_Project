#!/bin/bash
#
# Enhanced Last Detection Analyzer
# Comprehensive script to trace vehicle detection workflow with detailed diagnostics
# Usage: ./last_detection_analyzer.sh [--verbose] [--deep-dive] [--correlation-id <ID>]
#

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
VERBOSE=false
DEEP_DIVE=false
SPECIFIC_CORRELATION_ID=""
SHOW_HELP=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -d|--deep-dive)
            DEEP_DIVE=true
            VERBOSE=true
            shift
            ;;
        -c|--correlation-id)
            SPECIFIC_CORRELATION_ID="$2"
            shift 2
            ;;
        -h|--help)
            SHOW_HELP=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            SHOW_HELP=true
            shift
            ;;
    esac
done

# Show help if requested
if [ "$SHOW_HELP" = true ]; then
    echo -e "${GREEN}Enhanced Last Detection Analyzer${NC}"
    echo -e "${GREEN}================================${NC}"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -v, --verbose           Show detailed logs and debug information"
    echo "  -d, --deep-dive         Enable comprehensive diagnostics (implies --verbose)"
    echo "  -c, --correlation-id    Analyze specific correlation ID"
    echo "  -h, --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                      Basic analysis of last detection"
    echo "  $0 --verbose            Detailed analysis with extended logs"
    echo "  $0 --deep-dive          Comprehensive system analysis"
    echo "  $0 -c ABC123            Analyze specific detection by correlation ID"
    exit 0
fi

echo -e "${GREEN}🔍 Enhanced Last Detection Analysis${NC}"
echo -e "${GREEN}====================================${NC}"
if [ "$VERBOSE" = true ]; then
    echo -e "${CYAN}Mode: Verbose Analysis${NC}"
fi
if [ "$DEEP_DIVE" = true ]; then
    echo -e "${PURPLE}Mode: Deep Dive Diagnostics${NC}"
fi
echo ""

# Enhanced function to get detection data
get_detection_data() {
    if [ -n "$SPECIFIC_CORRELATION_ID" ]; then
        echo -e "${BLUE}📊 Analyzing Specific Detection: $SPECIFIC_CORRELATION_ID${NC}"
        recent_detection=$(docker exec database-persistence sqlite3 /app/data/traffic_data.db \
            "SELECT timestamp, trigger_source, correlation_id FROM traffic_detections WHERE correlation_id='$SPECIFIC_CORRELATION_ID' ORDER BY timestamp DESC LIMIT 1;" 2>/dev/null)
    else
        echo -e "${BLUE}📊 Most Recent Detection:${NC}"
        recent_detection=$(docker exec database-persistence sqlite3 /app/data/traffic_data.db \
            "SELECT timestamp, trigger_source, correlation_id FROM traffic_detections ORDER BY timestamp DESC LIMIT 1;" 2>/dev/null)
    fi
}

# Enhanced radar analysis
analyze_radar_detection() {
    local correlation_id=$1
    local log_time=$2
    
    echo -e "${YELLOW}1. 📡 Radar Detection Analysis:${NC}"
    
    # Basic radar logs
    radar_logs=$(docker logs radar-service --since="15m" 2>&1 | grep -i "$correlation_id\|$log_time" | tail -5)
    if [ -n "$radar_logs" ]; then
        echo "$radar_logs" | sed 's/^/   /'
    else
        echo "   No radar logs found for this correlation ID"
    fi
    
    if [ "$VERBOSE" = true ]; then
        echo ""
        echo -e "${CYAN}   📋 Extended Radar Analysis:${NC}"
        
        # Check radar service health
        radar_health=$(docker inspect radar-service --format='{{.State.Health.Status}}' 2>/dev/null || echo "unknown")
        echo "   Health Status: $radar_health"
        
        # Recent radar statistics
        echo "   Recent radar activity (last 10 entries):"
        docker logs radar-service --since="15m" 2>&1 | grep -E "(speed|detection|alert)" | tail -10 | sed 's/^/     /'
        
        # Check Redis radar channel
        radar_channel_count=$(docker exec redis redis-cli llen "traffic:radar" 2>/dev/null || echo "0")
        echo "   Redis radar channel entries: $radar_channel_count"
        
        if [ "$DEEP_DIVE" = true ]; then
            echo ""
            echo -e "${PURPLE}   🔬 Deep Dive - Radar Service:${NC}"
            
            # Container resource usage
            radar_stats=$(docker stats radar-service --no-stream --format "table {{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null | tail -1)
            echo "   Resource usage: $radar_stats"
            
            # Recent radar messages in Redis
            echo "   Recent radar messages in Redis:"
            docker exec redis redis-cli lrange "traffic:radar" 0 2 2>/dev/null | sed 's/^/     /' | head -6
            
            # Check for radar service errors
            echo "   Recent radar service errors:"
            docker logs radar-service --since="30m" 2>&1 | grep -i "error\|exception\|fail" | tail -3 | sed 's/^/     /'
        fi
    fi
    echo ""
}

# Enhanced consolidator analysis
analyze_consolidator_processing() {
    local correlation_id=$1
    
    echo -e "${YELLOW}2. 🚗 Vehicle Consolidator Analysis:${NC}"
    
    # Basic consolidator logs
    consolidator_logs=$(docker logs vehicle-consolidator --since="15m" 2>&1 | grep -i "$correlation_id\|camera\|handshake\|request\|response" | tail -8)
    if [ -n "$consolidator_logs" ]; then
        echo "$consolidator_logs" | sed 's/^/   /'
    else
        echo "   No consolidator logs found for this correlation ID"
    fi
    
    if [ "$VERBOSE" = true ]; then
        echo ""
        echo -e "${CYAN}   📋 Extended Consolidator Analysis:${NC}"
        
        # Check consolidator health
        consolidator_health=$(docker inspect vehicle-consolidator --format='{{.State.Health.Status}}' 2>/dev/null || echo "unknown")
        echo "   Health Status: $consolidator_health"
        
        # Check for handshake protocol activity
        echo "   Recent handshake activity:"
        docker logs vehicle-consolidator --since="15m" 2>&1 | grep -E "(handshake|camera.*request|camera.*response|correlation)" | tail -8 | sed 's/^/     /'
        
        # Check Redis camera channels
        camera_req_count=$(docker exec redis redis-cli llen "camera_requests" 2>/dev/null || echo "0")
        camera_resp_count=$(docker exec redis redis-cli llen "camera_responses" 2>/dev/null || echo "0")
        echo "   Camera requests queued: $camera_req_count"
        echo "   Camera responses queued: $camera_resp_count"
        
        if [ "$DEEP_DIVE" = true ]; then
            echo ""
            echo -e "${PURPLE}   🔬 Deep Dive - Vehicle Consolidator:${NC}"
            
            # Container resource usage
            consolidator_stats=$(docker stats vehicle-consolidator --no-stream --format "table {{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null | tail -1)
            echo "   Resource usage: $consolidator_stats"
            
            # Recent camera requests
            echo "   Recent camera requests in Redis:"
            docker exec redis redis-cli lrange "camera_requests" 0 4 2>/dev/null | sed 's/^/     /' | head -10
            
            # Recent camera responses
            echo "   Recent camera responses in Redis:"
            docker exec redis redis-cli lrange "camera_responses" 0 4 2>/dev/null | sed 's/^/     /' | head -10
            
            # Check for NoneType errors or other issues
            echo "   Recent consolidator errors:"
            docker logs vehicle-consolidator --since="30m" 2>&1 | grep -i "error\|exception\|nonetype\|traceback" | tail -5 | sed 's/^/     /'
            
            # Performance metrics if available
            echo "   Performance metrics:"
            docker logs vehicle-consolidator --since="15m" 2>&1 | grep -i "performance\|processing.*time\|statistics" | tail -3 | sed 's/^/     /'
        fi
    fi
    echo ""
}

# Enhanced camera service analysis
analyze_camera_service() {
    local correlation_id=$1
    
    echo -e "${YELLOW}3. 📷 Camera Service Analysis:${NC}"
    
    # Basic camera logs
    camera_logs=$(journalctl -u imx500-ai-capture --since="15 minutes ago" -n 30 | grep -i "$correlation_id\|request\|response\|handshake" | tail -5)
    if [ -n "$camera_logs" ]; then
        echo "$camera_logs" | sed 's/^/   /'
    else
        echo "   No camera service logs found for this correlation ID"
    fi
    
    if [ "$VERBOSE" = true ]; then
        echo ""
        echo -e "${CYAN}   📋 Extended Camera Analysis:${NC}"
        
        # Camera service status
        camera_status=$(systemctl show imx500-ai-capture --property=SubState --value)
        camera_uptime=$(systemctl show imx500-ai-capture --property=ActiveEnterTimestamp --value)
        echo "   Service Status: $camera_status"
        echo "   Service Started: $camera_uptime"
        
        # Recent camera activity
        echo "   Recent camera service activity:"
        journalctl -u imx500-ai-capture --since="15 minutes ago" -n 20 | tail -10 | sed 's/^/     /'
        
        # Check camera script location and version
        camera_script_path=$(systemctl show imx500-ai-capture --property=ExecStart --value | grep -o '/[^[:space:]]*\.py')
        if [ -n "$camera_script_path" ]; then
            echo "   Camera script: $camera_script_path"
            if [ -f "$camera_script_path" ]; then
                script_size=$(stat -c%s "$camera_script_path" 2>/dev/null || echo "unknown")
                script_modified=$(stat -c%y "$camera_script_path" 2>/dev/null || echo "unknown")
                echo "   Script size: $script_size bytes"
                echo "   Last modified: $script_modified"
            fi
        fi
        
        if [ "$DEEP_DIVE" = true ]; then
            echo ""
            echo -e "${PURPLE}   🔬 Deep Dive - Camera Service:${NC}"
            
            # Camera hardware status
            echo "   Camera hardware detection:"
            lsusb | grep -i camera | sed 's/^/     /' || echo "     No USB cameras detected"
            
            # Check for IMX500 specific hardware
            echo "   IMX500 hardware status:"
            dmesg | grep -i imx500 | tail -3 | sed 's/^/     /' || echo "     No IMX500 messages in kernel log"
            
            # Camera service resource usage
            camera_pid=$(systemctl show imx500-ai-capture --property=MainPID --value)
            if [ "$camera_pid" != "0" ] && [ -n "$camera_pid" ]; then
                echo "   Process ID: $camera_pid"
                cpu_usage=$(ps -p $camera_pid -o %cpu --no-headers 2>/dev/null || echo "unknown")
                mem_usage=$(ps -p $camera_pid -o %mem --no-headers 2>/dev/null || echo "unknown")
                echo "   CPU usage: ${cpu_usage}%"
                echo "   Memory usage: ${mem_usage}%"
            fi
            
            # Recent camera errors
            echo "   Recent camera service errors:"
            journalctl -u imx500-ai-capture --since="30 minutes ago" -p err | tail -3 | sed 's/^/     /'
            
            # Check Redis connectivity from camera perspective
            echo "   Camera Redis connectivity test:"
            timeout 5 redis-cli -h localhost -p 6379 ping 2>/dev/null | sed 's/^/     /' || echo "     Redis connection test failed"
        fi
    fi
    echo ""
}

# Enhanced database analysis
analyze_database_storage() {
    local correlation_id=$1
    
    echo -e "${YELLOW}4. 🗄️ Database Storage Analysis:${NC}"
    
    # Basic database logs
    db_logs=$(docker logs database-persistence --since="15m" 2>&1 | grep -i "$correlation_id\|insert\|traffic_detection\|correlation" | tail -5)
    if [ -n "$db_logs" ]; then
        echo "$db_logs" | sed 's/^/   /'
    else
        echo "   No database logs found for this correlation ID"
    fi
    
    if [ "$VERBOSE" = true ]; then
        echo ""
        echo -e "${CYAN}   📋 Extended Database Analysis:${NC}"
        
        # Database health
        db_health=$(docker inspect database-persistence --format='{{.State.Health.Status}}' 2>/dev/null || echo "unknown")
        echo "   Health Status: $db_health"
        
        # Recent database activity
        echo "   Recent database operations:"
        docker logs database-persistence --since="15m" 2>&1 | grep -E "(INSERT|UPDATE|SELECT|correlation)" | tail -8 | sed 's/^/     /'
        
        # Database statistics
        total_detections=$(docker exec database-persistence sqlite3 /app/data/traffic_data.db "SELECT COUNT(*) FROM traffic_detections;" 2>/dev/null || echo "unknown")
        recent_detections=$(docker exec database-persistence sqlite3 /app/data/traffic_data.db "SELECT COUNT(*) FROM traffic_detections WHERE timestamp > datetime('now', '-1 hour');" 2>/dev/null || echo "unknown")
        echo "   Total detections in database: $total_detections"
        echo "   Detections in last hour: $recent_detections"
        
        if [ "$DEEP_DIVE" = true ]; then
            echo ""
            echo -e "${PURPLE}   🔬 Deep Dive - Database:${NC}"
            
            # Database container resource usage
            db_stats=$(docker stats database-persistence --no-stream --format "table {{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null | tail -1)
            echo "   Resource usage: $db_stats"
            
            # Database file information
            echo "   Database file info:"
            docker exec database-persistence ls -lah /app/data/traffic_data.db 2>/dev/null | sed 's/^/     /' || echo "     Database file not accessible"
            
            # Table schemas and counts
            echo "   Table statistics:"
            docker exec database-persistence sqlite3 /app/data/traffic_data.db "SELECT name, COUNT(*) as count FROM (SELECT 'traffic_detections' as name UNION SELECT 'radar_detections' UNION SELECT 'camera_detections') t LEFT JOIN sqlite_master s ON t.name = s.name WHERE s.type = 'table';" 2>/dev/null | sed 's/^/     /' || echo "     Unable to query table statistics"
            
            # Recent database errors
            echo "   Recent database errors:"
            docker logs database-persistence --since="30m" 2>&1 | grep -i "error\|exception\|fail\|lock" | tail -3 | sed 's/^/     /'
            
            # Database integrity check
            echo "   Database integrity:"
            docker exec database-persistence sqlite3 /app/data/traffic_data.db "PRAGMA integrity_check;" 2>/dev/null | head -1 | sed 's/^/     /' || echo "     Integrity check failed"
        fi
    fi
    echo ""
}

# Enhanced Redis message analysis
analyze_redis_messages() {
    local correlation_id=$1
    
    echo -e "${YELLOW}5. 📨 Redis Message Analysis:${NC}"
    
    # Check camera requests
    camera_req_count=$(docker exec redis redis-cli llen "camera_requests" 2>/dev/null || echo "0")
    echo "   Camera requests queued: $camera_req_count"
    
    # Check recent radar messages
    recent_radar=$(docker exec redis redis-cli lrange "traffic:radar" 0 2 2>/dev/null | grep "$correlation_id" | head -1)
    if [ -n "$recent_radar" ]; then
        echo "   Found in radar channel: $(echo "$recent_radar" | cut -c1-80)..."
    else
        echo "   Not found in recent radar messages"
    fi
    
    if [ "$VERBOSE" = true ]; then
        echo ""
        echo -e "${CYAN}   📋 Extended Redis Analysis:${NC}"
        
        # Redis health
        redis_health=$(docker inspect redis --format='{{.State.Health.Status}}' 2>/dev/null || echo "unknown")
        echo "   Redis Health: $redis_health"
        
        # All channel statistics
        echo "   Channel statistics:"
        for channel in "traffic:radar" "camera_requests" "camera_responses"; do
            count=$(docker exec redis redis-cli llen "$channel" 2>/dev/null || echo "0")
            echo "     $channel: $count messages"
        done
        
        # Recent activity across all channels
        echo "   Recent messages preview:"
        echo "     Radar channel (last 3):"
        docker exec redis redis-cli lrange "traffic:radar" 0 2 2>/dev/null | head -6 | sed 's/^/       /'
        
        if [ "$DEEP_DIVE" = true ]; then
            echo ""
            echo -e "${PURPLE}   🔬 Deep Dive - Redis:${NC}"
            
            # Redis resource usage
            redis_stats=$(docker stats redis --no-stream --format "table {{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null | tail -1)
            echo "   Resource usage: $redis_stats"
            
            # Redis configuration info
            echo "   Redis info:"
            docker exec redis redis-cli info memory | grep -E "(used_memory_human|maxmemory)" | sed 's/^/     /'
            
            # Connection info
            echo "   Client connections:"
            docker exec redis redis-cli info clients | grep "connected_clients" | sed 's/^/     /'
            
            # Search for correlation ID across all channels
            if [ -n "$correlation_id" ]; then
                echo "   Searching for correlation ID $correlation_id across all channels:"
                for channel in "traffic:radar" "camera_requests" "camera_responses"; do
                    found=$(docker exec redis redis-cli lrange "$channel" 0 -1 2>/dev/null | grep -c "$correlation_id" || echo "0")
                    echo "     $channel: $found matches"
                done
            fi
            
            # Recent Redis errors
            echo "   Recent Redis errors:"
            docker logs redis --since="30m" 2>&1 | grep -i "error\|warning\|fail" | tail -3 | sed 's/^/     /'
        fi
    fi
    echo ""
}

# Enhanced system status check
enhanced_system_status() {
    echo -e "${BLUE}🔧 Enhanced System Status:${NC}"
    
    # Check key containers
    containers=("redis" "vehicle-consolidator" "database-persistence" "radar-service" "realtime-events-broadcaster" "traffic-monitor")
    for container in "${containers[@]}"; do
        if docker ps --format "table {{.Names}}" | grep -q "$container"; then
            health=$(docker inspect "$container" --format='{{.State.Health.Status}}' 2>/dev/null || echo "no-health-check")
            if [ "$health" = "healthy" ]; then
                echo -e "  ${GREEN}✅${NC} $container: Running (Healthy)"
            elif [ "$health" = "no-health-check" ]; then
                echo -e "  ${YELLOW}🟡${NC} $container: Running (No health check)"
            else
                echo -e "  ${RED}❌${NC} $container: Running ($health)"
            fi
            
            if [ "$VERBOSE" = true ]; then
                # Container uptime
                started=$(docker inspect "$container" --format='{{.State.StartedAt}}' 2>/dev/null | cut -c1-19)
                echo "    Started: $started"
                
                if [ "$DEEP_DIVE" = true ]; then
                    # Resource usage
                    stats=$(docker stats "$container" --no-stream --format "CPU: {{.CPUPerc}} | Memory: {{.MemUsage}}" 2>/dev/null)
                    echo "    Resources: $stats"
                fi
            fi
        else
            echo -e "  ${RED}❌${NC} $container: Not Running"
        fi
    done
    
    # Check camera service
    if systemctl is-active --quiet imx500-ai-capture; then
        echo -e "  ${GREEN}✅${NC} Camera Service: Active"
        if [ "$VERBOSE" = true ]; then
            uptime=$(systemctl show imx500-ai-capture --property=ActiveEnterTimestamp --value | cut -d' ' -f2-3)
            echo "    Started: $uptime"
        fi
    else
        echo -e "  ${RED}❌${NC} Camera Service: Inactive"
        if [ "$VERBOSE" = true ]; then
            echo "    Recent status:"
            systemctl status imx500-ai-capture --no-pager -l | tail -3 | sed 's/^/      /'
        fi
    fi
    
    if [ "$DEEP_DIVE" = true ]; then
        echo ""
        echo -e "${PURPLE}   🔬 Deep Dive - System Resources:${NC}"
        
        # System load
        load_avg=$(uptime | awk -F'load average:' '{print $2}')
        echo "   System load:$load_avg"
        
        # Memory usage
        memory_info=$(free -h | grep Mem)
        echo "   Memory: $memory_info"
        
        # Disk space
        echo "   Storage usage:"
        df -h /mnt/storage | tail -1 | awk '{print "     SSD: " $3 " used / " $2 " total (" $5 " used)"}' 
        df -h / | tail -1 | awk '{print "     Root: " $3 " used / " $2 " total (" $5 " used)"}'
        
        # Network connectivity
        echo "   Network tests:"
        if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
            echo "     Internet: Connected"
        else
            echo "     Internet: Disconnected"
        fi
        
        # Docker daemon status
        docker_version=$(docker version --format '{{.Server.Version}}' 2>/dev/null || echo "unknown")
        echo "   Docker version: $docker_version"
    fi
    echo ""
}

# Enhanced recent activity analysis
analyze_recent_activity() {
    echo -e "${YELLOW}📋 Enhanced Recent Activity Analysis:${NC}"
    
    if [ "$VERBOSE" = true ]; then
        echo -e "${CYAN}Vehicle Consolidator (detailed):${NC}"
        docker logs vehicle-consolidator --since="10m" 2>&1 | tail -8 | sed 's/^/  /'
        
        echo ""
        echo -e "${CYAN}Radar Service (detailed):${NC}"
        docker logs radar-service --since="10m" 2>&1 | tail -8 | sed 's/^/  /'
        
        echo ""
        echo -e "${CYAN}Camera Service (detailed):${NC}"
        journalctl -u imx500-ai-capture --since="10 minutes ago" -n 8 | sed 's/^/  /'
        
        if [ "$DEEP_DIVE" = true ]; then
            echo ""
            echo -e "${PURPLE}🔬 Deep Dive - All Container Logs:${NC}"
            
            for container in database-persistence realtime-events-broadcaster traffic-monitor; do
                echo -e "${CYAN}$container:${NC}"
                docker logs "$container" --since="10m" 2>&1 | tail -5 | sed 's/^/  /'
                echo ""
            done
        fi
    else
        echo -e "${CYAN}Vehicle Consolidator:${NC}"
        docker logs vehicle-consolidator --since="5m" 2>&1 | tail -3 | sed 's/^/  /'
        
        echo ""
        echo -e "${CYAN}Radar Service:${NC}"
        docker logs radar-service --since="5m" 2>&1 | tail -3 | sed 's/^/  /'
    fi
}

# Main execution function
main() {
    # Get detection data
    get_detection_data
    
    if [ -n "$recent_detection" ]; then
        timestamp=$(echo "$recent_detection" | cut -d'|' -f1)
        trigger_source=$(echo "$recent_detection" | cut -d'|' -f2)
        correlation_id=$(echo "$recent_detection" | cut -d'|' -f3)
        
        echo -e "  🚗 Source: ${GREEN}$trigger_source${NC}"
        echo -e "  ⏰ Time: $timestamp"
        echo -e "  🆔 Correlation ID: $correlation_id"
        
        # Convert timestamp to approximate log time
        log_time=$(date -d "$timestamp" "+%H:%M" 2>/dev/null || echo "unknown")
        
        echo ""
        echo -e "${BLUE}🔍 Tracing Detection Process for ID: $correlation_id${NC}"
        echo ""
        
        # Run enhanced analysis functions
        analyze_radar_detection "$correlation_id" "$log_time"
        analyze_consolidator_processing "$correlation_id"
        analyze_camera_service "$correlation_id"
        analyze_database_storage "$correlation_id"
        analyze_redis_messages "$correlation_id"
        
        # Enhanced error analysis
        echo -e "${YELLOW}⚠️ Enhanced Error Analysis:${NC}"
        
        error_found=false
        for container in vehicle-consolidator radar-service database-persistence; do
            if docker ps --format "table {{.Names}}" | grep -q "$container"; then
                if [ "$VERBOSE" = true ]; then
                    errors=$(docker logs "$container" --since="15m" 2>&1 | grep -i "error\|exception\|traceback\|$correlation_id" | grep -v "No error" | tail -5)
                else
                    errors=$(docker logs "$container" --since="10m" 2>&1 | grep -i "error\|exception\|traceback\|$correlation_id" | grep -v "No error" | tail -2)
                fi
                
                if [ -n "$errors" ]; then
                    echo -e "  ${RED}❌ $container:${NC}"
                    echo "$errors" | sed 's/^/     /'
                    error_found=true
                fi
            fi
        done
        
        if [ "$error_found" = false ]; then
            echo -e "  ${GREEN}✅ No errors found during this detection${NC}"
        fi
        
        # Summary with recommendations
        echo ""
        echo -e "${BLUE}📋 Detection Summary & Recommendations:${NC}"
        echo -e "  🎯 Result: Detection from ${GREEN}$trigger_source${NC}"
        
        if [ "$DEEP_DIVE" = true ]; then
            echo ""
            echo -e "${PURPLE}🔬 Recommendations:${NC}"
            
            # Check if handshake protocol is working
            camera_req_count=$(docker exec redis redis-cli llen "camera_requests" 2>/dev/null || echo "0")
            if [ "$camera_req_count" -gt 10 ]; then
                echo -e "  ${YELLOW}⚠️ High camera request queue ($camera_req_count) - check camera service responsiveness${NC}"
            fi
            
            # Check detection success rate
            radar_recent=$(docker exec database-persistence sqlite3 /app/data/traffic_data.db "SELECT COUNT(*) FROM radar_detections WHERE detected_at > datetime('now', '-1 hour');" 2>/dev/null || echo "0")
            final_recent=$(docker exec database-persistence sqlite3 /app/data/traffic_data.db "SELECT COUNT(*) FROM traffic_detections WHERE timestamp > datetime('now', '-1 hour');" 2>/dev/null || echo "0")
            
            if [ "$radar_recent" -gt 0 ] && [ "$final_recent" -gt 0 ]; then
                success_rate=$(echo "scale=1; $final_recent * 100 / $radar_recent" | bc 2>/dev/null || echo "N/A")
                echo -e "  📈 Current success rate: ${success_rate}% ($final_recent/$radar_recent)"
                
                if [ "$(echo "$success_rate < 50" | bc 2>/dev/null)" = "1" ]; then
                    echo -e "  ${RED}⚠️ Low success rate - investigate handshake protocol${NC}"
                fi
            fi
        fi
        
    else
        echo -e "  ${RED}❌ No detections found in database${NC}"
        
        enhanced_system_status
        analyze_recent_activity
        
        if [ "$DEEP_DIVE" = true ]; then
            echo -e "${PURPLE}🔬 Troubleshooting Recommendations:${NC}"
            echo -e "  1. Check if radar service is generating detections"
            echo -e "  2. Verify handshake protocol between consolidator and camera"
            echo -e "  3. Ensure database persistence is storing results"
            echo -e "  4. Test Redis message channels"
        fi
    fi
    
    echo ""
    echo -e "${GREEN}Analysis complete!${NC}"
    
    if [ "$VERBOSE" = false ] && [ "$DEEP_DIVE" = false ]; then
        echo -e "${CYAN}Tip: Use --verbose for detailed analysis or --deep-dive for comprehensive diagnostics${NC}"
    fi
}

# Run main function
main