#!/bin/bash
# Container Maintenance Scheduler
# Sets up cron jobs inside Docker container for automated maintenance
# Run during container startup: bash scripts/setup-container-cron.sh

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🕐 Setting up Container Maintenance Scheduler${NC}"
echo "================================================"

# Configuration
MAINTENANCE_SCRIPT="/app/scripts/container-maintenance.py"
LOG_DIR="/mnt/storage/logs/maintenance"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Ensure cron is installed (add to Dockerfile if needed)
if ! command -v cron >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Installing cron service...${NC}"
    apt-get update && apt-get install -y cron
fi

# Create cron configuration for container
echo -e "\n${BLUE}📅 Creating container cron schedule${NC}"

# Create crontab entries
cat > /tmp/container-maintenance-cron << EOF
# Container Data Maintenance Schedule
# Environment variables for cron
PYTHONPATH=/app
DATA_VOLUME=/mnt/storage

# Daily comprehensive maintenance at 2:00 AM
0 2 * * * /usr/bin/python3 $MAINTENANCE_SCRIPT --daily-cleanup >> $LOG_DIR/daily-maintenance.log 2>&1

# Emergency cleanup check every 2 hours
0 */2 * * * /usr/bin/python3 $MAINTENANCE_SCRIPT --status | grep -q "needs_emergency_cleanup.*true" && /usr/bin/python3 $MAINTENANCE_SCRIPT --emergency-cleanup >> $LOG_DIR/emergency-cleanup.log 2>&1

# Status report every 6 hours (for monitoring)
0 */6 * * * /usr/bin/python3 $MAINTENANCE_SCRIPT --status > $LOG_DIR/status-report.json 2>&1

# Weekly deep cleanup on Sunday at 3:00 AM
0 3 * * 0 /usr/bin/python3 $MAINTENANCE_SCRIPT --emergency-cleanup >> $LOG_DIR/weekly-cleanup.log 2>&1
EOF

# Install cron jobs
crontab /tmp/container-maintenance-cron
rm /tmp/container-maintenance-cron

echo -e "${GREEN}✓ Container cron jobs installed${NC}"

# Create maintenance status endpoint script
echo -e "\n${BLUE}🔍 Creating status monitoring script${NC}"

cat > /app/scripts/maintenance-status.py << 'EOF'
#!/usr/bin/env python3
"""
Maintenance Status API Endpoint
Provides maintenance status for container health checks and monitoring
"""

import json
import sys
import os
sys.path.append('/app/scripts')

try:
    from container_maintenance import ContainerMaintenanceConfig, ContainerMaintenance
    
    def get_maintenance_status():
        """Get current maintenance status"""
        try:
            config = ContainerMaintenanceConfig()
            maintenance = ContainerMaintenance(config)
            
            # Get status report
            status = maintenance.get_status_report()
            
            # Add health indicators
            health = status.get('health', {})
            status['health_summary'] = {
                'overall_status': 'healthy',
                'disk_usage_percent': health.get('disk_usage', {}).get('used_percent', 0),
                'needs_attention': health.get('needs_cleanup', False) or health.get('needs_emergency_cleanup', False),
                'warning_count': len(health.get('warnings', [])),
                'last_maintenance': status.get('statistics', {}).get('last_cleanup', 'never')
            }
            
            # Determine overall health
            if health.get('needs_emergency_cleanup', False):
                status['health_summary']['overall_status'] = 'critical'
            elif health.get('needs_cleanup', False):
                status['health_summary']['overall_status'] = 'warning'
            elif len(health.get('warnings', [])) > 0:
                status['health_summary']['overall_status'] = 'warning'
            
            return status
            
        except Exception as e:
            return {
                'error': str(e),
                'health_summary': {
                    'overall_status': 'error',
                    'last_error': str(e)
                }
            }
    
    if __name__ == '__main__':
        status = get_maintenance_status()
        print(json.dumps(status, indent=2))
        
        # Exit code based on health status
        health_status = status.get('health_summary', {}).get('overall_status', 'error')
        if health_status in ['critical', 'error']:
            sys.exit(1)
        elif health_status == 'warning':
            sys.exit(2)
        else:
            sys.exit(0)

except ImportError as e:
    print(json.dumps({
        'error': f'Import error: {e}',
        'health_summary': {'overall_status': 'error'}
    }))
    sys.exit(1)
EOF

chmod +x /app/scripts/maintenance-status.py

echo -e "${GREEN}✓ Status monitoring endpoint created${NC}"

# Create startup script for container
echo -e "\n${BLUE}🚀 Creating container startup script${NC}"

cat > /app/scripts/start-with-maintenance.sh << 'EOF'
#!/bin/bash
# Container Startup with Maintenance
# Starts both the main application and maintenance scheduler

set -euo pipefail

echo "🚀 Starting container with automated maintenance..."

# Start cron service
echo "📅 Starting cron service..."
service cron start

# Verify cron is running
if ! pgrep cron > /dev/null; then
    echo "❌ Failed to start cron service"
    exit 1
fi

echo "✓ Cron service started"

# Run initial maintenance check (non-blocking)
echo "🔧 Running initial maintenance check..."
python3 /app/scripts/container-maintenance.py --status > /mnt/storage/logs/maintenance/startup-status.json 2>&1 || true

# Check if emergency cleanup is needed
if python3 /app/scripts/container-maintenance.py --status | grep -q "needs_emergency_cleanup.*true" 2>/dev/null; then
    echo "⚠️  Emergency cleanup needed - running now..."
    python3 /app/scripts/container-maintenance.py --emergency-cleanup >> /mnt/storage/logs/maintenance/startup-emergency.log 2>&1 || true
fi

echo "✓ Initial maintenance check completed"

# If no arguments provided, start the main application
if [ $# -eq 0 ]; then
    echo "🎯 Starting main application..."
    exec python3 /app/main.py
else
    # Execute provided command
    echo "🎯 Starting custom command: $@"
    exec "$@"
fi
EOF

chmod +x /app/scripts/start-with-maintenance.sh

echo -e "${GREEN}✓ Container startup script created${NC}"

# Create maintenance monitoring dashboard script
echo -e "\n${BLUE}📊 Creating maintenance dashboard script${NC}"

cat > /app/scripts/maintenance-dashboard.sh << 'EOF'
#!/bin/bash
# Container Maintenance Dashboard
# Shows real-time maintenance status inside container

echo "📊 Container Maintenance Dashboard"
echo "=================================="
echo "Container: ${HOSTNAME:-unknown}"
echo "Time: $(date)"
echo ""

# Check if maintenance script exists
if [ ! -f "/app/scripts/container-maintenance.py" ]; then
    echo "❌ Maintenance script not found"
    exit 1
fi

# Get maintenance status
echo "🔍 Maintenance Status:"
python3 /app/scripts/maintenance-status.py 2>/dev/null || echo "❌ Failed to get status"

echo ""
echo "💾 Disk Usage:"
df -h /mnt/storage 2>/dev/null || echo "❌ Storage not mounted"

echo ""
echo "📁 File Counts:"
if [ -d "/mnt/storage/camera_capture/live" ]; then
    live_count=$(find /mnt/storage/camera_capture/live -name "*.jpg" 2>/dev/null | wc -l)
    echo "  Live images: $live_count"
fi

if [ -d "/mnt/storage/camera_capture/processed" ]; then
    processed_count=$(find /mnt/storage/camera_capture/processed -name "*.jpg" 2>/dev/null | wc -l)
    echo "  Processed images: $processed_count"
fi

if [ -d "/mnt/storage/periodic_snapshots" ]; then
    snapshot_count=$(find /mnt/storage/periodic_snapshots -name "*.jpg" 2>/dev/null | wc -l)
    echo "  Snapshots: $snapshot_count"
fi

echo ""
echo "📋 Cron Status:"
if pgrep cron > /dev/null; then
    echo "  ✓ Cron service: Running"
    echo "  📅 Scheduled jobs:"
    crontab -l 2>/dev/null | grep -v "^#" | grep -v "^$" || echo "    No jobs scheduled"
else
    echo "  ❌ Cron service: Not running"
fi

echo ""
echo "🎯 Quick Actions:"
echo "  Force cleanup:    python3 /app/scripts/container-maintenance.py --daily-cleanup"
echo "  Emergency clean:  python3 /app/scripts/container-maintenance.py --emergency-cleanup"
echo "  Status check:     python3 /app/scripts/maintenance-status.py"
EOF

chmod +x /app/scripts/maintenance-dashboard.sh

echo -e "${GREEN}✓ Maintenance dashboard created${NC}"

# Start cron service
echo -e "\n${BLUE}🔧 Starting cron service${NC}"

# Ensure cron service is running
service cron start || {
    echo -e "${YELLOW}⚠ Cron service start failed, will retry...${NC}"
    sleep 2
    service cron start || echo -e "${YELLOW}⚠ Cron may not be available in this environment${NC}"
}

# Verify cron is running
if pgrep cron > /dev/null; then
    echo -e "${GREEN}✓ Cron service is running${NC}"
    
    # Show installed cron jobs
    echo -e "\n${BLUE}📅 Installed cron jobs:${NC}"
    crontab -l 2>/dev/null | grep -v "^#" | grep -v "^$" || echo "No jobs found"
else
    echo -e "${YELLOW}⚠ Cron service not running (may not be available in container)${NC}"
    echo -e "${YELLOW}  Maintenance will need to be triggered manually or via daemon mode${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Container Maintenance Setup Complete!${NC}"
echo ""
echo -e "${BLUE}📋 Usage:${NC}"
echo "  Dashboard:        bash /app/scripts/maintenance-dashboard.sh"
echo "  Status:           python3 /app/scripts/maintenance-status.py"
echo "  Manual cleanup:   python3 /app/scripts/container-maintenance.py --daily-cleanup"
echo "  Emergency:        python3 /app/scripts/container-maintenance.py --emergency-cleanup"
echo ""
echo -e "${BLUE}🔄 Automatic Schedule:${NC}"
echo "  Daily cleanup:    2:00 AM"
echo "  Emergency check:  Every 2 hours"
echo "  Status report:    Every 6 hours"
echo "  Weekly deep clean: Sunday 3:00 AM"