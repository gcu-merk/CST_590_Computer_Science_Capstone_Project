#!/bin/bash
# Disk Space Alert System
# Monitors disk usage and sends alerts when thresholds are exceeded
# Can be run from cron or as standalone monitoring

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="$PROJECT_DIR/config/maintenance.conf"
ALERT_LOG="/mnt/storage/logs/maintenance/disk-alerts.log"
ALERT_COOLDOWN_HOURS=6  # Don't spam alerts

# Thresholds (can be overridden by config)
WARNING_THRESHOLD=80
CRITICAL_THRESHOLD=90
SSD_WARNING_THRESHOLD=85
SSD_CRITICAL_THRESHOLD=95

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Ensure log directory exists
mkdir -p "$(dirname "$ALERT_LOG")"

log_alert() {
    local level="$1"
    local message="$2"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$level] $message" >> "$ALERT_LOG"
    echo -e "${level}: $message"
}

get_disk_usage() {
    local mount_point="$1"
    df "$mount_point" 2>/dev/null | awk 'NR==2 {print $5}' | sed 's/%//' || echo "0"
}

check_alert_cooldown() {
    local alert_type="$1"
    local cooldown_file="/tmp/disk_alert_${alert_type}_cooldown"
    
    if [ -f "$cooldown_file" ]; then
        local last_alert=$(stat -c %Y "$cooldown_file" 2>/dev/null || echo "0")
        local current_time=$(date +%s)
        local time_diff=$((current_time - last_alert))
        local cooldown_seconds=$((ALERT_COOLDOWN_HOURS * 3600))
        
        if [ $time_diff -lt $cooldown_seconds ]; then
            return 1  # Still in cooldown
        fi
    fi
    
    touch "$cooldown_file"
    return 0  # Not in cooldown
}

send_alert() {
    local level="$1"
    local title="$2"
    local message="$3"
    local alert_type="$4"
    
    # Check cooldown
    if ! check_alert_cooldown "$alert_type"; then
        return 0
    fi
    
    # Log the alert
    log_alert "$level" "$title: $message"
    
    # Send to system log
    logger -t "disk-monitor" "$level: $title - $message"
    
    # Try to send email if available (optional)
    if command -v mail >/dev/null 2>&1; then
        echo "$message" | mail -s "[$level] Traffic Monitor: $title" root 2>/dev/null || true
    fi
    
    # Create alert file for web dashboard (if exists)
    local alert_file="/mnt/storage/alerts/disk_${alert_type}_$(date +%s).json"
    if [ -d "$(dirname "$alert_file")" ] || mkdir -p "$(dirname "$alert_file")" 2>/dev/null; then
        cat > "$alert_file" << EOF
{
    "timestamp": "$(date -Iseconds)",
    "level": "$level",
    "type": "disk_space",
    "title": "$title",
    "message": "$message",
    "alert_type": "$alert_type"
}
EOF
    fi
}

trigger_emergency_cleanup() {
    log_alert "ACTION" "Triggering emergency cleanup due to critical disk usage"
    
    # Run emergency cleanup
    if python3 "$PROJECT_DIR/scripts/data-maintenance-manager.py" \
       --config "$CONFIG_FILE" --emergency-cleanup 2>&1 >> "$ALERT_LOG"; then
        log_alert "INFO" "Emergency cleanup completed successfully"
    else
        log_alert "ERROR" "Emergency cleanup failed"
    fi
}

check_disk_health() {
    local mount_point="$1"
    local name="$2"
    local warn_threshold="$3"
    local crit_threshold="$4"
    
    local usage=$(get_disk_usage "$mount_point")
    local status="OK"
    
    if [ "$usage" -eq 0 ]; then
        send_alert "ERROR" "Disk Check Failed" \
            "Unable to check disk usage for $name ($mount_point)" \
            "${name}_error"
        return 1
    fi
    
    echo -e "\n${BLUE}📊 $name Usage: ${usage}%${NC}"
    
    if [ "$usage" -ge "$crit_threshold" ]; then
        status="CRITICAL"
        send_alert "CRITICAL" "$name Disk Critical" \
            "$name disk usage is at $usage% (>= $crit_threshold%). Immediate action required!" \
            "${name}_critical"
        
        # Trigger emergency cleanup for SSD
        if [ "$name" = "SSD" ]; then
            trigger_emergency_cleanup
        fi
        
    elif [ "$usage" -ge "$warn_threshold" ]; then
        status="WARNING"
        send_alert "WARNING" "$name Disk Warning" \
            "$name disk usage is at $usage% (>= $warn_threshold%). Consider cleanup." \
            "${name}_warning"
    else
        echo -e "${GREEN}✓ $name disk usage is healthy${NC}"
    fi
    
    return 0
}

check_file_counts() {
    echo -e "\n${BLUE}📁 File Count Analysis${NC}"
    
    local live_count=0
    local processed_count=0
    local snapshot_count=0
    local metadata_count=0
    
    # Count files
    if [ -d "/mnt/storage/camera_capture/live" ]; then
        live_count=$(find /mnt/storage/camera_capture/live -name "*.jpg" 2>/dev/null | wc -l)
    fi
    
    if [ -d "/mnt/storage/camera_capture/processed" ]; then
        processed_count=$(find /mnt/storage/camera_capture/processed -name "*.jpg" 2>/dev/null | wc -l)
    fi
    
    if [ -d "/mnt/storage/periodic_snapshots" ]; then
        snapshot_count=$(find /mnt/storage/periodic_snapshots -name "*.jpg" 2>/dev/null | wc -l)
    fi
    
    if [ -d "/mnt/storage/camera_capture/metadata" ]; then
        metadata_count=$(find /mnt/storage/camera_capture/metadata -name "*.json" 2>/dev/null | wc -l)
    fi
    
    echo "  Live images: $live_count"
    echo "  Processed images: $processed_count"
    echo "  Snapshots: $snapshot_count"
    echo "  Metadata files: $metadata_count"
    
    # Alert on high file counts
    if [ "$live_count" -gt 1000 ]; then
        send_alert "WARNING" "High Live Image Count" \
            "Live image directory has $live_count files. Consider cleanup." \
            "high_file_count"
    fi
    
    if [ "$metadata_count" -gt "$((live_count + processed_count + 100))" ]; then
        send_alert "WARNING" "Orphaned Metadata" \
            "Found $metadata_count metadata files vs $((live_count + processed_count)) images. Orphaned files detected." \
            "orphaned_metadata"
    fi
}

check_service_health() {
    echo -e "\n${BLUE}🔧 Service Health Check${NC}"
    
    # Check maintenance daemon
    if systemctl is-active --quiet data-maintenance 2>/dev/null; then
        echo -e "${GREEN}✓ Data maintenance daemon: Running${NC}"
    else
        echo -e "${YELLOW}⚠ Data maintenance daemon: Not running${NC}"
        send_alert "WARNING" "Maintenance Service Down" \
            "Data maintenance daemon is not running. Automated cleanup disabled." \
            "service_down"
    fi
    
    # Check Docker
    if systemctl is-active --quiet docker 2>/dev/null; then
        echo -e "${GREEN}✓ Docker service: Running${NC}"
    else
        echo -e "${RED}❌ Docker service: Not running${NC}"
        send_alert "CRITICAL" "Docker Service Down" \
            "Docker service is not running. Camera system offline." \
            "docker_down"
    fi
    
    # Check camera capture service (if exists)
    if systemctl list-units --all | grep -q "host-camera-capture"; then
        if systemctl is-active --quiet host-camera-capture 2>/dev/null; then
            echo -e "${GREEN}✓ Camera capture service: Running${NC}"
        else
            echo -e "${YELLOW}⚠ Camera capture service: Not running${NC}"
            send_alert "WARNING" "Camera Service Down" \
                "Camera capture service is not running. Image capture disabled." \
                "camera_down"
        fi
    fi
}

check_log_sizes() {
    echo -e "\n${BLUE}📋 Log Size Analysis${NC}"
    
    # Check application logs
    local large_logs=()
    
    if [ -d "/mnt/storage/logs" ]; then
        while IFS= read -r -d '' log_file; do
            local size_mb=$(du -m "$log_file" 2>/dev/null | cut -f1)
            if [ "$size_mb" -gt 50 ]; then  # Logs > 50MB
                large_logs+=("$log_file:${size_mb}MB")
                echo -e "${YELLOW}⚠ Large log: $(basename "$log_file") = ${size_mb}MB${NC}"
            fi
        done < <(find /mnt/storage/logs -name "*.log" -type f -print0 2>/dev/null)
    fi
    
    if [ ${#large_logs[@]} -gt 0 ]; then
        local log_list=""
        for log in "${large_logs[@]}"; do
            log_list="$log_list\n  - $log"
        done
        
        send_alert "WARNING" "Large Log Files" \
            "Found large log files:$log_list" \
            "large_logs"
    else
        echo -e "${GREEN}✓ Log file sizes are reasonable${NC}"
    fi
}

main() {
    echo -e "${BLUE}🔍 Disk Space & System Health Monitor${NC}"
    echo "====================================="
    echo "$(date)"
    
    # Check disk usage
    check_disk_health "/" "SD Card" "$WARNING_THRESHOLD" "$CRITICAL_THRESHOLD"
    
    if [ -d "/mnt/storage" ]; then
        check_disk_health "/mnt/storage" "SSD" "$SSD_WARNING_THRESHOLD" "$SSD_CRITICAL_THRESHOLD"
    else
        send_alert "ERROR" "SSD Not Mounted" \
            "SSD storage is not mounted at /mnt/storage" \
            "ssd_missing"
    fi
    
    # Additional checks
    check_file_counts
    check_service_health
    check_log_sizes
    
    echo -e "\n${BLUE}📊 Summary${NC}"
    echo "Monitor run completed at $(date)"
    echo "Alert log: $ALERT_LOG"
    
    # Show recent alerts
    if [ -f "$ALERT_LOG" ]; then
        local recent_alerts=$(tail -5 "$ALERT_LOG" 2>/dev/null | wc -l)
        if [ "$recent_alerts" -gt 0 ]; then
            echo -e "\n${YELLOW}Recent alerts (last 5):${NC}"
            tail -5 "$ALERT_LOG" 2>/dev/null | while read -r line; do
                echo "  $line"
            done
        fi
    fi
    
    echo ""
    echo -e "${BLUE}🎯 Quick Actions:${NC}"
    echo "  Force cleanup:    bash scripts/quick-cleanup.sh"
    echo "  Emergency clean:  bash scripts/emergency-cleanup.sh"
    echo "  Full status:      bash scripts/maintenance-monitor.sh"
}

# Handle command line arguments
case "${1:-monitor}" in
    "monitor"|"")
        main
        ;;
    "status")
        # Quick status check
        sd_usage=$(get_disk_usage "/")
        ssd_usage=$(get_disk_usage "/mnt/storage")
        echo "SD Card: ${sd_usage}% | SSD: ${ssd_usage}%"
        ;;
    "alerts")
        # Show recent alerts
        if [ -f "$ALERT_LOG" ]; then
            echo "Recent alerts:"
            tail -20 "$ALERT_LOG" 2>/dev/null || echo "No alerts found"
        else
            echo "No alert log found"
        fi
        ;;
    "test")
        # Test alert system
        send_alert "INFO" "Test Alert" "This is a test alert from the monitoring system" "test"
        echo "Test alert sent"
        ;;
    *)
        echo "Usage: $0 [monitor|status|alerts|test]"
        exit 1
        ;;
esac