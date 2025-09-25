#!/bin/bash
# Storage Analysis Script - Check what files are on SD card vs SSD
# Run this script on Raspberry Pi: bash scripts/storage-analysis.sh

echo "📊 Storage Analysis Report - $(date)"
echo "Analyzing file distribution between SD card and SSD"
echo "=================================================="

# Colors for output  
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "\n${BLUE}💾 FILESYSTEM OVERVIEW${NC}"
echo "----------------------"
df -h | grep -E "(Filesystem|/dev/|/mnt/storage)"

echo -e "\n${BLUE}📁 SD CARD ANALYSIS (Large Files > 10MB)${NC}"
echo "----------------------------------------"
echo "Files on SD card that should potentially be moved to SSD:"
find / -maxdepth 4 -size +10M -type f 2>/dev/null | grep -v "/mnt/storage" | grep -v "/proc/" | grep -v "/sys/" | head -20

echo -e "\n${BLUE}📋 APPLICATION LOG LOCATIONS${NC}"
echo "-----------------------------"
echo "Current log file locations:"

# Check common log locations
log_files=(
    "/var/log/host-camera-capture.log"
    "/var/log/camera-init.log" 
    "/var/log/image-sync-manager.log"
    "/var/log/syslog"
    "/var/log/daemon.log"
)

for log_file in "${log_files[@]}"; do
    if [ -f "$log_file" ]; then
        size=$(du -sh "$log_file" 2>/dev/null | cut -f1)
        if [ -L "$log_file" ]; then
            target=$(readlink "$log_file")
            echo -e "  ${GREEN}✓ $log_file -> $target [$size]${NC}"
        else
            echo -e "  ${YELLOW}⚠ $log_file (on SD card) [$size]${NC}"
        fi
    else
        echo -e "  ${RED}✗ $log_file (not found)${NC}"
    fi
done

echo -e "\n${BLUE}🐳 DOCKER DATA ANALYSIS${NC}" 
echo "----------------------"
if [ -d "/var/lib/docker" ]; then
    if [ -L "/var/lib/docker" ]; then
        target=$(readlink "/var/lib/docker")
        size=$(du -sh "$target" 2>/dev/null | cut -f1)
        echo -e "  ${GREEN}✓ Docker data: /var/lib/docker -> $target [$size]${NC}"
    else
        size=$(du -sh "/var/lib/docker" 2>/dev/null | cut -f1)
        echo -e "  ${YELLOW}⚠ Docker data on SD card: /var/lib/docker [$size]${NC}"
    fi
else
    echo -e "  ${RED}✗ Docker data directory not found${NC}"
fi

# Check container logs
if [ -d "/var/lib/docker/containers" ]; then
    container_log_size=$(du -sh "/var/lib/docker/containers" 2>/dev/null | cut -f1)
    echo -e "  Container logs size: $container_log_size"
fi

echo -e "\n${BLUE}📸 CAMERA DATA ANALYSIS${NC}"
echo "----------------------"
echo "Camera data storage locations:"

camera_dirs=(
    "/mnt/storage/camera_capture"
    "/mnt/storage/periodic_snapshots"  
    "/mnt/storage/ai_camera_images"
)

for dir in "${camera_dirs[@]}"; do
    if [ -d "$dir" ]; then
        size=$(du -sh "$dir" 2>/dev/null | cut -f1)
        count=$(find "$dir" -name "*.jpg" 2>/dev/null | wc -l)
        echo -e "  ${GREEN}✓ $dir: $size ($count images)${NC}"
    else
        echo -e "  ${RED}✗ $dir: not found${NC}"
    fi
done

echo -e "\n${BLUE}⚙️ SYSTEMD SERVICE LOGS${NC}"
echo "---------------------"
echo "Service log locations (potential SD card usage):"

# Check systemd journal size
if command -v journalctl >/dev/null 2>&1; then
    journal_size=$(journalctl --disk-usage 2>/dev/null | grep -o '[0-9.]*[KMGT]B')
    echo -e "  ${YELLOW}⚠ Systemd journal: $journal_size (on SD card)${NC}"
fi

# Check specific service logs
services=("host-camera-capture" "docker" "ssh")
for service in "${services[@]}"; do
    if systemctl is-enabled "$service" >/dev/null 2>&1; then
        echo -e "  Service '$service': logs via journalctl (SD card)"
    fi
done

echo -e "\n${BLUE}💡 RECOMMENDATIONS${NC}"
echo "----------------"

# Check if migration is needed
needs_migration=false

# Check logs on SD card
for log_file in "${log_files[@]:0:3}"; do  # Only app logs
    if [ -f "$log_file" ] && [ ! -L "$log_file" ]; then
        needs_migration=true
        break
    fi
done

# Check Docker on SD card
if [ -d "/var/lib/docker" ] && [ ! -L "/var/lib/docker" ]; then
    needs_migration=true
fi

if [ "$needs_migration" = true ]; then
    echo -e "${YELLOW}⚠ Migration recommended:${NC}"
    echo "  1. Run: sudo bash scripts/storage-migration.sh"
    echo "  2. This will move application logs and Docker data to SSD"
    echo "  3. Reduces SD card wear and improves performance"
else
    echo -e "${GREEN}✓ Storage configuration looks good!${NC}"
    echo "  Most application data appears to be on SSD"
fi

echo -e "\n${BLUE}📈 CURRENT USAGE SUMMARY${NC}"
echo "----------------------"
sd_usage=$(df -h / | tail -1 | awk '{print $5}')
ssd_usage=$(df -h /mnt/storage 2>/dev/null | tail -1 | awk '{print $5}' || echo "N/A")

echo "  SD Card Usage: $sd_usage"
echo "  SSD Usage: $ssd_usage"

if [ "$ssd_usage" != "N/A" ]; then
    echo -e "\n${GREEN}💾 Optimal configuration:${NC}"
    echo "  • SD Card: < 50% (OS and system files only)"
    echo "  • SSD: Primary storage for all application data"
else
    echo -e "\n${RED}❌ SSD not mounted at /mnt/storage${NC}"
    echo "  • Check SSD connection and mount configuration"
fi

echo -e "\n${BLUE}🔍 For detailed analysis, run:${NC}"
echo "  • View largest files: sudo find / -size +50M -type f 2>/dev/null | head -10"
echo "  • Check Docker: docker system df"
echo "  • Monitor in real-time: sudo bash scripts/storage-migration.sh (includes monitoring)"

echo -e "\nAnalysis complete - $(date)"