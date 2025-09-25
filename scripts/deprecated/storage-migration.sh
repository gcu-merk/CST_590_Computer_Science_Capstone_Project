#!/bin/bash
# Storage Migration Script - Move all application data from SD card to SSD
# Run this script on Raspberry Pi: sudo bash scripts/storage-migration.sh

set -e  # Exit on error

echo "🚛 Storage Migration Script - $(date)"
echo "Moving all application data from SD card to SSD"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SSD_BASE="/mnt/storage"
SSD_LOGS="$SSD_BASE/logs"
SSD_DOCKER="$SSD_BASE/docker"
BACKUP_DIR="$SSD_BASE/migration_backup_$(date +%Y%m%d_%H%M%S)"

# Function to check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        echo -e "${RED}ERROR: This script must be run as root (use sudo)${NC}"
        echo "Usage: sudo bash scripts/storage-migration.sh"
        exit 1
    fi
}

# Function to create backup before migration
create_backup() {
    echo -e "\n${BLUE}Creating backup directory...${NC}"
    mkdir -p "$BACKUP_DIR"
    echo -e "${GREEN}✓ Backup directory created: $BACKUP_DIR${NC}"
}

# Function to migrate application logs
migrate_logs() {
    echo -e "\n${BLUE}Migrating application logs to SSD...${NC}"
    
    # Create SSD log directory structure
    mkdir -p "$SSD_LOGS/applications"
    mkdir -p "$SSD_LOGS/system"
    mkdir -p "$SSD_LOGS/docker"
    mkdir -p "$SSD_LOGS/services"
    
    # Log files to migrate
    local log_files=(
        "/var/log/host-camera-capture.log"
        "/var/log/camera-init.log" 
        "/var/log/image-sync-manager.log"
    )
    
    for log_file in "${log_files[@]}"; do
        if [ -f "$log_file" ]; then
            # Backup original
            cp "$log_file" "$BACKUP_DIR/" 2>/dev/null || true
            
            # Move to SSD
            local filename=$(basename "$log_file")
            mv "$log_file" "$SSD_LOGS/applications/$filename"
            
            # Create symbolic link
            ln -sf "$SSD_LOGS/applications/$filename" "$log_file"
            
            echo -e "${GREEN}✓ Migrated: $filename${NC}"
        else
            echo -e "${YELLOW}⚠ Not found: $log_file${NC}"
        fi
    done
    
    # Set proper permissions
    chown -R pi:pi "$SSD_LOGS"
    chmod -R 755 "$SSD_LOGS"
    
    echo -e "${GREEN}✓ Application logs migrated to SSD${NC}"
}

# Function to update application log paths
update_log_paths() {
    echo -e "\n${BLUE}Updating application log configurations...${NC}"
    
    # Update host-camera-capture.py
    local camera_script="scripts/host-camera-capture.py"
    if [ -f "$camera_script" ]; then
        # Backup original
        cp "$camera_script" "$BACKUP_DIR/"
        
        # Update log path
        sed -i "s|'/var/log/host-camera-capture.log'|'$SSD_LOGS/applications/host-camera-capture.log'|g" "$camera_script"
        echo -e "${GREEN}✓ Updated: $camera_script${NC}"
    fi
    
    # Update camera-init.sh
    local init_script="scripts/camera-init.sh"
    if [ -f "$init_script" ]; then
        # Backup original
        cp "$init_script" "$BACKUP_DIR/"
        
        # Update log path
        sed -i "s|LOG_FILE=\"/var/log/camera-init.log\"|LOG_FILE=\"$SSD_LOGS/applications/camera-init.log\"|g" "$init_script"
        echo -e "${GREEN}✓ Updated: $init_script${NC}"
    fi
    
    # Update image-sync-manager.py
    local sync_script="scripts/image-sync-manager.py"
    if [ -f "$sync_script" ]; then
        # Backup original
        cp "$sync_script" "$BACKUP_DIR/"
        
        # Update log path
        sed -i "s|'/var/log/image-sync-manager.log'|'$SSD_LOGS/applications/image-sync-manager.log'|g" "$sync_script"
        echo -e "${GREEN}✓ Updated: $sync_script${NC}"
    fi
}

# Function to migrate Docker data
migrate_docker_data() {
    echo -e "\n${BLUE}Migrating Docker data to SSD...${NC}"
    
    # Stop Docker service
    echo "Stopping Docker service..."
    systemctl stop docker
    
    # Create SSD Docker directory
    mkdir -p "$SSD_DOCKER"
    
    # Move Docker data if it exists
    if [ -d "/var/lib/docker" ]; then
        echo "Moving Docker data directory..."
        cp -a /var/lib/docker/* "$SSD_DOCKER/" 2>/dev/null || true
        
        # Backup original directory
        mv /var/lib/docker "$BACKUP_DIR/docker_original"
        
        # Create symbolic link
        ln -sf "$SSD_DOCKER" /var/lib/docker
        
        echo -e "${GREEN}✓ Docker data migrated to SSD${NC}"
    else
        echo -e "${YELLOW}⚠ Docker data directory not found${NC}"
    fi
    
    # Update Docker daemon configuration
    local docker_config="/etc/docker/daemon.json"
    mkdir -p "/etc/docker"
    
    cat > "$docker_config" << EOF
{
    "data-root": "$SSD_DOCKER",
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "10m",
        "max-file": "3"
    },
    "storage-driver": "overlay2"
}
EOF
    
    echo -e "${GREEN}✓ Docker daemon configured for SSD storage${NC}"
    
    # Start Docker service
    systemctl start docker
    echo -e "${GREEN}✓ Docker service restarted${NC}"
}

# Function to configure log rotation
configure_log_rotation() {
    echo -e "\n${BLUE}Configuring log rotation for SSD logs...${NC}"
    
    # Create logrotate configuration
    cat > /etc/logrotate.d/ssd-applications << EOF
$SSD_LOGS/applications/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 pi pi
    postrotate
        # Restart services that write to these logs
        systemctl reload-or-restart host-camera-capture 2>/dev/null || true
    endscript
}
EOF
    
    echo -e "${GREEN}✓ Log rotation configured${NC}"
}

# Function to update systemd service for log paths
update_systemd_service() {
    echo -e "\n${BLUE}Updating systemd service for SSD log paths...${NC}"
    
    local service_file="/etc/systemd/system/host-camera-capture.service"
    if [ -f "$service_file" ]; then
        # Update service to use SSD paths
        sed -i "s|StandardOutput=journal|StandardOutput=append:$SSD_LOGS/services/host-camera-capture.out|g" "$service_file"
        sed -i "s|StandardError=journal|StandardError=append:$SSD_LOGS/services/host-camera-capture.err|g" "$service_file"
        
        # Reload systemd
        systemctl daemon-reload
        
        echo -e "${GREEN}✓ Systemd service updated for SSD logging${NC}"
    fi
}

# Function to create monitoring script
create_storage_monitor() {
    echo -e "\n${BLUE}Creating storage monitoring script...${NC}"
    
    cat > "$SSD_BASE/storage-monitor.sh" << 'EOF'
#!/bin/bash
# Storage monitoring script - checks SD card vs SSD usage

echo "=== Storage Usage Monitor ==="
echo "Date: $(date)"
echo ""

echo "SD Card Usage (/):"
df -h / | tail -1
echo ""

echo "SSD Usage (/mnt/storage):"
df -h /mnt/storage | tail -1
echo ""

echo "Large files on SD card (>10MB):"
find / -maxdepth 3 -size +10M -type f 2>/dev/null | grep -v "/mnt/storage" | head -10
echo ""

echo "Application log sizes on SSD:"
du -sh /mnt/storage/logs/* 2>/dev/null
echo ""

echo "Camera image counts:"
echo "  Live images: $(find /mnt/storage/camera_capture/live -name "*.jpg" 2>/dev/null | wc -l)"
echo "  Snapshots: $(find /mnt/storage/periodic_snapshots -name "*.jpg" 2>/dev/null | wc -l)"
echo "  AI images: $(find /mnt/storage/ai_camera_images -name "*.jpg" 2>/dev/null | wc -l)"
EOF
    
    chmod +x "$SSD_BASE/storage-monitor.sh"
    
    # Add to crontab for daily monitoring
    (crontab -l 2>/dev/null; echo "0 6 * * * $SSD_BASE/storage-monitor.sh >> $SSD_LOGS/system/storage-monitor.log 2>&1") | crontab -
    
    echo -e "${GREEN}✓ Storage monitoring script created and scheduled${NC}"
}

# Function to verify migration
verify_migration() {
    echo -e "\n${BLUE}Verifying migration...${NC}"
    
    local issues=0
    
    # Check SSD directories exist
    local required_dirs=(
        "$SSD_LOGS/applications"
        "$SSD_LOGS/system" 
        "$SSD_LOGS/docker"
        "$SSD_LOGS/services"
        "$SSD_DOCKER"
    )
    
    for dir in "${required_dirs[@]}"; do
        if [ -d "$dir" ]; then
            echo -e "${GREEN}✓ Directory exists: $dir${NC}"
        else
            echo -e "${RED}✗ Directory missing: $dir${NC}"
            ((issues++))
        fi
    done
    
    # Check symbolic links
    local expected_links=(
        "/var/log/host-camera-capture.log"
        "/var/log/camera-init.log"
        "/var/log/image-sync-manager.log"
        "/var/lib/docker"
    )
    
    for link in "${expected_links[@]}"; do
        if [ -L "$link" ]; then
            echo -e "${GREEN}✓ Symbolic link exists: $link${NC}"
        else
            echo -e "${YELLOW}⚠ Symbolic link missing: $link${NC}"
        fi
    done
    
    # Check Docker status
    if systemctl is-active --quiet docker; then
        echo -e "${GREEN}✓ Docker service running${NC}"
    else
        echo -e "${RED}✗ Docker service not running${NC}"
        ((issues++))
    fi
    
    return $issues
}

# Function to display summary
display_summary() {
    echo -e "\n${YELLOW}📋 MIGRATION SUMMARY${NC}"
    echo "=========================================="
    
    echo -e "💾 Storage Usage:"
    df -h / | grep "/$"
    df -h /mnt/storage | grep "/mnt/storage"
    
    echo -e "\n📁 SSD Directory Structure:"
    tree "$SSD_BASE" -L 3 2>/dev/null || ls -la "$SSD_BASE"
    
    echo -e "\n🔗 Symbolic Links Created:"
    ls -la /var/log/host-camera-capture.log 2>/dev/null || echo "  Not found"
    ls -la /var/log/camera-init.log 2>/dev/null || echo "  Not found"
    ls -la /var/lib/docker 2>/dev/null || echo "  Not found"
    
    echo -e "\n📊 Log File Sizes:"
    du -sh "$SSD_LOGS"/* 2>/dev/null || echo "  No logs yet"
    
    echo -e "\n🚀 Next Steps:"
    echo "  1. Test applications: systemctl restart host-camera-capture"
    echo "  2. Test Docker: docker-compose up -d"
    echo "  3. Monitor storage: $SSD_BASE/storage-monitor.sh"
    echo "  4. Check logs: tail -f $SSD_LOGS/applications/host-camera-capture.log"
    
    echo -e "\n💾 Backup Location: $BACKUP_DIR"
    echo "    (Remove after verifying migration is successful)"
}

# Main execution
main() {
    echo -e "${BLUE}Starting storage migration...${NC}"
    
    check_root
    create_backup
    migrate_logs
    update_log_paths
    migrate_docker_data
    configure_log_rotation
    update_systemd_service
    create_storage_monitor
    
    if verify_migration; then
        display_summary
        echo -e "\n${GREEN}🎉 Storage migration completed successfully!${NC}"
        echo -e "${GREEN}All application data is now stored on SSD${NC}"
        exit 0
    else
        echo -e "\n${RED}❌ Storage migration completed with issues!${NC}"
        echo -e "${RED}Check the verification output above${NC}"
        exit 1
    fi
}

# Handle script interruption
trap 'echo -e "\n${YELLOW}Migration interrupted${NC}"; exit 1' INT TERM

# Run main function
main "$@"