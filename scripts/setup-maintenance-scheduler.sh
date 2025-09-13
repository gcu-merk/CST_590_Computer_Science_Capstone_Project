#!/bin/bash
# Data Maintenance Scheduler
# Sets up systemd services and cron jobs for automated maintenance
# Run: sudo bash scripts/setup-maintenance-scheduler.sh

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 Setting up Data Maintenance Scheduler${NC}"
echo "=================================================="

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SERVICE_USER="pi"
MAINTENANCE_SCRIPT="$PROJECT_DIR/scripts/data-maintenance-manager.py"
CONFIG_FILE="$PROJECT_DIR/config/maintenance.conf"

# Verify required files exist
if [ ! -f "$MAINTENANCE_SCRIPT" ]; then
    echo -e "${RED}❌ Maintenance script not found: $MAINTENANCE_SCRIPT${NC}"
    exit 1
fi

if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}❌ Configuration file not found: $CONFIG_FILE${NC}"
    exit 1
fi

echo -e "\n${BLUE}📋 Creating systemd service for maintenance daemon${NC}"

# Create systemd service file
cat > /tmp/data-maintenance.service << EOF
[Unit]
Description=Data File Maintenance Manager
After=docker.service
Requires=docker.service
StartLimitIntervalSec=0

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$PROJECT_DIR
ExecStart=/usr/bin/python3 $MAINTENANCE_SCRIPT --config $CONFIG_FILE --daemon
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal
SyslogIdentifier=data-maintenance

# Resource limits
MemoryMax=500M
CPUQuota=50%

# Security settings
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$PROJECT_DIR /mnt/storage /tmp
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

# Install service
sudo mv /tmp/data-maintenance.service /etc/systemd/system/
sudo systemctl daemon-reload

echo -e "${GREEN}✓ Systemd service created${NC}"

echo -e "\n${BLUE}📅 Setting up cron jobs for scheduled maintenance${NC}"

# Create cron entries
cat > /tmp/maintenance-cron << EOF
# Data Maintenance Cron Jobs
# Emergency cleanup check every 15 minutes
*/15 * * * * $SERVICE_USER /usr/bin/python3 $MAINTENANCE_SCRIPT --config $CONFIG_FILE --status | grep -q "needs_emergency_cleanup.*true" && /usr/bin/python3 $MAINTENANCE_SCRIPT --config $CONFIG_FILE --emergency-cleanup

# Daily database backup at 2:00 AM
0 2 * * * $SERVICE_USER /usr/bin/python3 $MAINTENANCE_SCRIPT --config $CONFIG_FILE --backup-db

# Weekly database vacuum on Sunday at 3:00 AM
0 3 * * 0 $SERVICE_USER /usr/bin/python3 $MAINTENANCE_SCRIPT --config $CONFIG_FILE --vacuum-db

# Daily cleanup cycle at 1:00 AM
0 1 * * * $SERVICE_USER /usr/bin/python3 $MAINTENANCE_SCRIPT --config $CONFIG_FILE --cleanup

# Monthly comprehensive cleanup on 1st of month at 4:00 AM
0 4 1 * * $SERVICE_USER /usr/bin/python3 $MAINTENANCE_SCRIPT --config $CONFIG_FILE --emergency-cleanup
EOF

# Install cron jobs
sudo cp /tmp/maintenance-cron /etc/cron.d/data-maintenance
sudo chmod 644 /etc/cron.d/data-maintenance
sudo chown root:root /etc/cron.d/data-maintenance

echo -e "${GREEN}✓ Cron jobs configured${NC}"

echo -e "\n${BLUE}📊 Creating maintenance monitoring script${NC}"

# Create monitoring script
cat > "$PROJECT_DIR/scripts/maintenance-monitor.sh" << 'EOF'
#!/bin/bash
# Maintenance Status Monitor
# Shows real-time maintenance status and alerts

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
MAINTENANCE_SCRIPT="$PROJECT_DIR/scripts/data-maintenance-manager.py"
CONFIG_FILE="$PROJECT_DIR/config/maintenance.conf"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}📊 Data Maintenance Status Monitor${NC}"
echo "=================================="
echo "$(date)"
echo ""

# Get status report
STATUS_JSON=$(python3 "$MAINTENANCE_SCRIPT" --config "$CONFIG_FILE" --status 2>/dev/null)

if [ $? -eq 0 ]; then
    # Parse JSON using basic tools (no jq dependency)
    echo -e "${BLUE}🔍 STORAGE HEALTH${NC}"
    echo "$STATUS_JSON" | grep -A 10 '"storage_health"' | head -15
    echo ""
    
    echo -e "${BLUE}📈 STATISTICS${NC}"
    echo "$STATUS_JSON" | grep -A 10 '"statistics"' | head -15
    echo ""
    
    echo -e "${BLUE}📁 FILE COUNTS${NC}"
    echo "$STATUS_JSON" | grep -A 10 '"file_counts"' | head -10
    echo ""
    
    # Check for warnings
    WARNINGS=$(echo "$STATUS_JSON" | grep '"warnings"' || true)
    if [ -n "$WARNINGS" ]; then
        echo -e "${YELLOW}⚠️  WARNINGS${NC}"
        echo "$WARNINGS"
        echo ""
    fi
    
    # Check service status
    echo -e "${BLUE}🔧 SERVICE STATUS${NC}"
    if systemctl is-active --quiet data-maintenance; then
        echo -e "${GREEN}✓ Maintenance daemon: Active${NC}"
    else
        echo -e "${RED}❌ Maintenance daemon: Inactive${NC}"
    fi
    
    # Check disk usage
    echo -e "\n${BLUE}💾 DISK USAGE${NC}"
    df -h / /mnt/storage 2>/dev/null | grep -E "(Filesystem|/dev/)" || echo "Storage check failed"
    
else
    echo -e "${RED}❌ Failed to get maintenance status${NC}"
    echo "Check if maintenance script is working:"
    echo "  python3 $MAINTENANCE_SCRIPT --status"
fi

echo ""
echo -e "${BLUE}🎯 Quick Actions:${NC}"
echo "  Status:           bash scripts/maintenance-monitor.sh"
echo "  Force cleanup:    python3 scripts/data-maintenance-manager.py --cleanup"
echo "  Emergency clean:  python3 scripts/data-maintenance-manager.py --emergency-cleanup"
echo "  Service logs:     sudo journalctl -u data-maintenance -f"
EOF

chmod +x "$PROJECT_DIR/scripts/maintenance-monitor.sh"

echo -e "${GREEN}✓ Monitoring script created${NC}"

echo -e "\n${BLUE}🎯 Creating maintenance convenience scripts${NC}"

# Create cleanup convenience script
cat > "$PROJECT_DIR/scripts/quick-cleanup.sh" << 'EOF'
#!/bin/bash
# Quick Cleanup Script - Immediate maintenance actions

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🧹 Running quick cleanup..."

# Run maintenance cycle
python3 "$PROJECT_DIR/scripts/data-maintenance-manager.py" \
    --config "$PROJECT_DIR/config/maintenance.conf" \
    --cleanup

echo "✓ Quick cleanup completed"
echo ""
echo "For status: bash scripts/maintenance-monitor.sh"
EOF

chmod +x "$PROJECT_DIR/scripts/quick-cleanup.sh"

# Create emergency cleanup script
cat > "$PROJECT_DIR/scripts/emergency-cleanup.sh" << 'EOF'
#!/bin/bash
# Emergency Cleanup Script - Aggressive space recovery

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🚨 Running emergency cleanup..."
echo "WARNING: This will remove most stored images and data!"
read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 1
fi

# Run emergency cleanup
python3 "$PROJECT_DIR/scripts/data-maintenance-manager.py" \
    --config "$PROJECT_DIR/config/maintenance.conf" \
    --emergency-cleanup

echo "✓ Emergency cleanup completed"
echo ""
echo "For status: bash scripts/maintenance-monitor.sh"
EOF

chmod +x "$PROJECT_DIR/scripts/emergency-cleanup.sh"

echo -e "${GREEN}✓ Convenience scripts created${NC}"

echo -e "\n${BLUE}🔍 Setting up log rotation for maintenance logs${NC}"

# Create logrotate configuration for maintenance logs
cat > /tmp/data-maintenance-logrotate << 'EOF'
/mnt/storage/logs/maintenance/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 pi pi
    postrotate
        systemctl reload data-maintenance 2>/dev/null || true
    endscript
}
EOF

sudo mv /tmp/data-maintenance-logrotate /etc/logrotate.d/data-maintenance
sudo chown root:root /etc/logrotate.d/data-maintenance
sudo chmod 644 /etc/logrotate.d/data-maintenance

echo -e "${GREEN}✓ Log rotation configured${NC}"

echo -e "\n${BLUE}🎛️  Configuring service startup${NC}"

# Enable service but don't start yet (let user decide)
sudo systemctl enable data-maintenance

echo -e "${GREEN}✓ Service enabled for automatic startup${NC}"

echo -e "\n${GREEN}🎉 Data Maintenance Scheduler Setup Complete!${NC}"
echo ""
echo -e "${BLUE}📋 NEXT STEPS:${NC}"
echo ""
echo -e "${YELLOW}1. Start the maintenance daemon:${NC}"
echo "   sudo systemctl start data-maintenance"
echo ""
echo -e "${YELLOW}2. Check status:${NC}"
echo "   bash scripts/maintenance-monitor.sh"
echo "   sudo systemctl status data-maintenance"
echo ""
echo -e "${YELLOW}3. View logs:${NC}"
echo "   sudo journalctl -u data-maintenance -f"
echo ""
echo -e "${YELLOW}4. Manual operations:${NC}"
echo "   bash scripts/quick-cleanup.sh        # Regular cleanup"
echo "   bash scripts/emergency-cleanup.sh    # Emergency cleanup"
echo ""
echo -e "${YELLOW}5. Configuration:${NC}"
echo "   Edit: $CONFIG_FILE"
echo "   Reload: sudo systemctl restart data-maintenance"
echo ""
echo -e "${BLUE}⚙️  Automated Schedule:${NC}"
echo "   • Continuous monitoring (5-minute intervals)"
echo "   • Hourly image cleanup"
echo "   • Daily database backup (2:00 AM)"
echo "   • Weekly database vacuum (Sunday 3:00 AM)"
echo "   • Emergency cleanup check (every 15 minutes)"
echo "   • Monthly deep cleanup (1st of month, 4:00 AM)"