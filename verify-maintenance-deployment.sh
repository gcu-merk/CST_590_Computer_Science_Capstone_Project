#!/bin/bash
# Post-Deployment Maintenance Verification Script
# Run this on your Raspberry Pi after CI/CD deployment to verify maintenance system

echo "🔍 Verifying Automated Maintenance System Deployment"
echo "=================================================="
echo "Time: $(date)"
echo ""

# Check if we're in the deployment directory
DEPLOY_DIR="/home/$(whoami)/traffic-monitor-deploy"
if [ -d "$DEPLOY_DIR" ]; then
    cd "$DEPLOY_DIR"
    echo "📁 Working from deployment directory: $DEPLOY_DIR"
else
    echo "⚠️  Deployment directory not found, using current directory"
fi

echo ""
echo "🐳 Container Status Check"
echo "------------------------"

# Check if both containers are running
echo "All containers:"
docker compose ps --format "table {{.Service}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "Maintenance service specific:"
if docker ps | grep -q "traffic-maintenance.*Up"; then
    echo "✅ Maintenance service: Running"
else
    echo "❌ Maintenance service: Not running"
    echo "Checking logs..."
    docker logs traffic-maintenance 2>/dev/null | tail -10 || echo "No maintenance container logs found"
fi

echo ""
echo "🔧 Maintenance System Verification"
echo "-----------------------------------"

# Test maintenance script availability
if docker exec traffic-monitor test -f /app/scripts/container-maintenance.py 2>/dev/null; then
    echo "✅ Maintenance scripts: Available in main container"
    
    # Test maintenance status
    echo ""
    echo "📊 Current maintenance status:"
    docker exec traffic-monitor python3 /app/scripts/container-maintenance.py --status 2>/dev/null | head -20 || echo "❌ Status check failed"
    
else
    echo "❌ Maintenance scripts: Not found in container"
    echo "   The maintenance system may not be included in the Docker image yet"
fi

# Check if maintenance service container has scripts
if docker ps | grep -q "traffic-maintenance"; then
    echo ""
    echo "📊 Maintenance service status:"
    docker exec traffic-maintenance python3 /app/scripts/container-maintenance.py --status 2>/dev/null | head -20 || echo "❌ Maintenance service status check failed"
fi

echo ""
echo "💾 Storage Configuration Check"
echo "------------------------------"

# Check SSD mount
if mountpoint -q /mnt/storage; then
    echo "✅ SSD mounted at /mnt/storage"
    echo "   Usage: $(df -h /mnt/storage | tail -1 | awk '{print $5}') used of $(df -h /mnt/storage | tail -1 | awk '{print $2}')"
else
    echo "❌ SSD not mounted at /mnt/storage"
    echo "   Maintenance system requires SSD to be mounted"
fi

# Check camera directories
echo ""
echo "📸 Camera directories:"
for dir in "/mnt/storage/camera_capture/live" "/mnt/storage/camera_capture/processed" "/mnt/storage/periodic_snapshots"; do
    if [ -d "$dir" ]; then
        count=$(find "$dir" -name "*.jpg" 2>/dev/null | wc -l)
        echo "  ✅ $dir: $count images"
    else
        echo "  ❌ $dir: Not found"
    fi
done

echo ""
echo "📋 Environment Variables Check"
echo "-----------------------------"

# Check maintenance environment variables in main container
echo "Maintenance configuration in main container:"
docker exec traffic-monitor printenv | grep MAINTENANCE 2>/dev/null || echo "  No MAINTENANCE_* environment variables found"

# Check in maintenance service if it exists
if docker ps | grep -q "traffic-maintenance"; then
    echo ""
    echo "Maintenance configuration in maintenance service:"
    docker exec traffic-maintenance printenv | grep MAINTENANCE 2>/dev/null || echo "  No MAINTENANCE_* environment variables found"
fi

echo ""
echo "🕐 Scheduled Maintenance Check"
echo "-----------------------------"

# Check if cron is available in containers
if docker exec traffic-monitor which cron >/dev/null 2>&1; then
    echo "✅ Cron available in main container"
    echo "Cron jobs:"
    docker exec traffic-monitor crontab -l 2>/dev/null || echo "  No cron jobs configured"
else
    echo "❌ Cron not available in main container"
fi

if docker ps | grep -q "traffic-maintenance"; then
    if docker exec traffic-maintenance which cron >/dev/null 2>&1; then
        echo "✅ Cron available in maintenance service"
        echo "Cron jobs:"
        docker exec traffic-maintenance crontab -l 2>/dev/null || echo "  No cron jobs configured"
    else
        echo "❌ Cron not available in maintenance service"
    fi
fi

echo ""
echo "🚀 Manual Maintenance Test"
echo "-------------------------"

# Test manual maintenance execution
echo "Testing manual maintenance execution..."
if docker exec traffic-monitor python3 /app/scripts/container-maintenance.py --status >/dev/null 2>&1; then
    echo "✅ Manual maintenance execution: Working"
    echo ""
    echo "🧹 You can run manual maintenance with:"
    echo "  docker exec traffic-monitor python3 /app/scripts/container-maintenance.py --daily-cleanup"
    echo "  docker exec traffic-monitor python3 /app/scripts/container-maintenance.py --emergency-cleanup"
elif docker ps | grep -q "traffic-maintenance" && docker exec traffic-maintenance python3 /app/scripts/container-maintenance.py --status >/dev/null 2>&1; then
    echo "✅ Manual maintenance execution: Working (via maintenance service)"
    echo ""
    echo "🧹 You can run manual maintenance with:"
    echo "  docker exec traffic-maintenance python3 /app/scripts/container-maintenance.py --daily-cleanup"
    echo "  docker exec traffic-maintenance python3 /app/scripts/container-maintenance.py --emergency-cleanup"
else
    echo "❌ Manual maintenance execution: Failed"
    echo "   Check if maintenance scripts are included in Docker image"
fi

echo ""
echo "📊 Next Steps"
echo "============"

# Determine what needs to be done based on findings
if docker ps | grep -q "traffic-maintenance.*Up" && docker exec traffic-maintenance python3 /app/scripts/container-maintenance.py --status >/dev/null 2>&1; then
    echo "🎉 Maintenance system is fully operational!"
    echo ""
    echo "✅ What's working:"
    echo "  • Maintenance service is running"
    echo "  • Scripts are accessible"
    echo "  • Manual operations available"
    echo ""
    echo "🕐 Automatic schedule:"
    echo "  • Daily cleanup: 2:00 AM"
    echo "  • Emergency checks: Every 2 hours"
    echo "  • Status reports: Every 6 hours"
    echo "  • Weekly deep clean: Sunday 3:00 AM"
    echo ""
    echo "📊 Monitor with:"
    echo "  docker logs traffic-maintenance -f"
    echo "  docker exec traffic-maintenance bash /app/scripts/maintenance-dashboard.sh"
    
elif docker exec traffic-monitor test -f /app/scripts/container-maintenance.py 2>/dev/null; then
    echo "⚠️  Partial deployment detected"
    echo ""
    echo "✅ Maintenance scripts are in main container"
    echo "❌ Dedicated maintenance service not running"
    echo ""
    echo "🔧 To enable full maintenance:"
    echo "  1. Check if docker-compose.yml includes maintenance service"
    echo "  2. Restart deployment: docker compose down && docker compose up -d"
    echo ""
    echo "🧹 For now, you can run manual maintenance:"
    echo "  docker exec traffic-monitor python3 /app/scripts/container-maintenance.py --daily-cleanup"
    
else
    echo "❌ Maintenance system not detected"
    echo ""
    echo "Possible issues:"
    echo "  • Docker image doesn't include maintenance scripts yet"
    echo "  • CI/CD hasn't deployed latest changes"
    echo "  • Docker image needs to be rebuilt with maintenance files"
    echo ""
    echo "🔧 Solutions:"
    echo "  1. Wait for next CI/CD deployment cycle"
    echo "  2. Trigger manual deployment if available"
    echo "  3. Check GitHub Actions for build/deployment status"
fi

echo ""
echo "🔍 View full status anytime with:"
echo "  bash verify-maintenance-deployment.sh"