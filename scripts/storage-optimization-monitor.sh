#!/bin/bash
# Storage Optimization Monitor
# Tracks the effectiveness of storage optimizations
# Run this script periodically: bash scripts/storage-optimization-monitor.sh

echo "📊 Storage Optimization Monitor - $(date)"
echo "=========================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "\n${BLUE}💾 STORAGE OVERVIEW${NC}"
echo "-------------------"
df -h | grep -E "(Filesystem|/dev/mmcblk0p2|/dev/sda1)" | while read line; do
    if [[ $line == *"mmcblk0p2"* ]]; then
        usage=$(echo $line | awk '{print $5}' | tr -d '%')
        if [ $usage -lt 10 ]; then
            echo -e "${GREEN}SD Card: $line${NC}"
        else
            echo -e "${YELLOW}SD Card: $line${NC}"
        fi
    elif [[ $line == *"sda1"* ]]; then
        echo -e "${GREEN}SSD:     $line${NC}"
    else
        echo "$line"
    fi
done

echo -e "\n${BLUE}🔗 USER DATA SYMLINKS${NC}"
echo "---------------------"
echo "VS Code Server:"
if [ -L "/home/merk/.vscode-server" ]; then
    echo -e "  ${GREEN}✓ Symlinked to SSD:${NC} $(readlink /home/merk/.vscode-server)"
    echo -e "  ${GREEN}✓ Size on SSD:${NC} $(du -sh /mnt/storage/user_data/vscode-server 2>/dev/null | cut -f1 || echo 'Not found')"
else
    echo -e "  ${YELLOW}⚠ Still on SD card${NC}"
fi

echo ""
echo "GitHub Actions Runner:"
if [ -L "/home/merk/actions-runner" ]; then
    echo -e "  ${GREEN}✓ Symlinked to SSD:${NC} $(readlink /home/merk/actions-runner)"
    echo -e "  ${GREEN}✓ Size on SSD:${NC} $(du -sh /mnt/storage/user_data/actions-runner 2>/dev/null | cut -f1 || echo 'Not found')"
else
    echo -e "  ${YELLOW}⚠ Still on SD card${NC}"
fi

echo -e "\n${BLUE}📋 SYSTEMD JOURNAL STATUS${NC}"
echo "-------------------------"
journal_storage=$(grep "^Storage=" /etc/systemd/journald.conf 2>/dev/null || echo "Storage=auto")
if [[ $journal_storage == *"volatile"* ]]; then
    echo -e "${GREEN}✓ Journal storage: $journal_storage (RAM only)${NC}"
else
    echo -e "${YELLOW}⚠ Journal storage: $journal_storage${NC}"
fi

# Check current journal usage
if command -v journalctl >/dev/null 2>&1; then
    journal_size=$(journalctl --disk-usage 2>/dev/null | grep -o '[0-9.]*[KMGT]' | head -1 || echo "Unknown")
    echo "  Current journal size: $journal_size"
fi

echo -e "\n${BLUE}🐳 DOCKER STORAGE${NC}"
echo "-----------------"
docker_root=$(docker info 2>/dev/null | grep "Docker Root Dir" | cut -d: -f2 | xargs)
if [[ $docker_root == *"/mnt/storage"* ]]; then
    echo -e "${GREEN}✓ Docker root: $docker_root${NC}"
    docker_size=$(du -sh "$docker_root" 2>/dev/null | cut -f1 || echo "Unknown")
    echo "  Docker data size: $docker_size"
else
    echo -e "${YELLOW}⚠ Docker root: $docker_root${NC}"
fi

echo -e "\n${BLUE}📸 CAMERA DATA${NC}"
echo "---------------"
for dir in "camera_capture" "periodic_snapshots" "ai_camera_images"; do
    path="/mnt/storage/$dir"
    if [ -d "$path" ]; then
        size=$(du -sh "$path" 2>/dev/null | cut -f1)
        count=$(find "$path" -name "*.jpg" 2>/dev/null | wc -l)
        echo -e "${GREEN}✓ $dir: $size ($count images)${NC}"
    else
        echo -e "${YELLOW}⚠ $dir: Not found${NC}"
    fi
done

echo -e "\n${BLUE}💡 OPTIMIZATION SUMMARY${NC}"
echo "---------------------------"

# Calculate total space saved
total_saved=0
if [ -L "/home/merk/.vscode-server" ]; then
    vscode_size=$(du -s /mnt/storage/user_data/vscode-server 2>/dev/null | cut -f1 || echo "0")
    total_saved=$((total_saved + vscode_size))
fi

if [ -L "/home/merk/actions-runner" ]; then
    runner_size=$(du -s /mnt/storage/user_data/actions-runner 2>/dev/null | cut -f1 || echo "0")
    total_saved=$((total_saved + runner_size))
fi

if [ $total_saved -gt 0 ]; then
    total_saved_mb=$((total_saved / 1024))
    echo -e "${GREEN}✓ Total space moved from SD to SSD: ${total_saved_mb}MB${NC}"
else
    echo -e "${YELLOW}⚠ No user data optimizations detected${NC}"
fi

echo ""
echo "Benefits achieved:"
echo "  • Reduced SD card wear and tear"
echo "  • Improved VS Code server performance"
echo "  • Faster GitHub Actions operations"
echo "  • Better overall system responsiveness"

echo -e "\n${BLUE}📅 NEXT STEPS${NC}"
echo "-------------"
echo "• Monitor SD card usage regularly (should stay < 10%)"
echo "• Consider moving /home/merk/Bookshelf to SSD if needed"
echo "• Keep systemd journal volatile for optimal performance"
echo "• Run this monitor monthly to ensure optimizations persist"

echo ""
echo "To run again: bash /mnt/storage/storage-optimization-monitor.sh"