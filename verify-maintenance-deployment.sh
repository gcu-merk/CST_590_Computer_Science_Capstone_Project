#!/bin/bash
# Post-Deployment Maintenance Verification Script
# Run this on your Raspberry Pi after CI/CD deployment to verify maintenance system
#
# Note: Containers are resolved at runtime from docker compose services when available.
# Services referenced by this script:
#   - Main service: traffic-monitor
#   - Maintenance service: data-maintenance

echo "🔍 Verifying Automated Maintenance System Deployment"
echo "=================================================="
echo "Time: $(date)"
echo ""

# Check if we're in the deployment directory
DEPLOY_DIR="/mnt/storage/traffic-monitor-deploy"
if [ -d "$DEPLOY_DIR" ]; then
    cd "$DEPLOY_DIR"
    echo "📁 Working from deployment directory: $DEPLOY_DIR"
else
    echo "⚠️  Deployment directory not found, using current directory"
fi

# Dynamic container name detection from docker-compose.yml if available
echo ""
echo "🔍 Detecting container configuration..."
MAIN_CONTAINER=""
MAINTENANCE_CONTAINER_NAMES=""

# Helper: resolve container name from compose service
resolve_compose_service_name() {
    local svc="$1"
    # Prefer docker compose v2 command, fallback to docker-compose
    local cid
    cid=$(docker compose ps -q "$svc" 2>/dev/null || docker-compose ps -q "$svc" 2>/dev/null)
    if [ -n "$cid" ]; then
        # Get the container name as displayed by docker
        echo $(docker inspect --format='{{.Name}}' "$cid" 2>/dev/null | sed 's/^\///')
        return 0
    fi
    return 1
}

echo ""
echo "🔍 Detecting container configuration..."
if [ -f "docker-compose.yml" ]; then
    echo "📋 Found docker-compose.yml, resolving service container names via docker compose..."
    MAIN_CONTAINER=$(resolve_compose_service_name "traffic-monitor" || true)
    MAINTENANCE_SERVICE_CONTAINER=$(resolve_compose_service_name "data-maintenance" || true)

    # Fallbacks if resolution failed
    MAIN_CONTAINER=${MAIN_CONTAINER:-traffic-monitor}
    MAINTENANCE_SERVICE_CONTAINER=${MAINTENANCE_SERVICE_CONTAINER:-data-maintenance}

    echo "   Main container: $MAIN_CONTAINER"
    echo "   Maintenance container (candidate): $MAINTENANCE_SERVICE_CONTAINER"
    # Build a list of candidate maintenance container names to check
    MAINTENANCE_CONTAINER_NAMES="$MAINTENANCE_SERVICE_CONTAINER data-maintenance"
else
    echo "⚠️  No docker-compose.yml found, using default container name patterns"
    # Legacy fallback names kept for older deployments
    MAIN_CONTAINER="traffic-monitor"
    MAINTENANCE_CONTAINER_NAMES="data-maintenance"
fi

echo ""
echo "🐳 Container Status Check"
echo "------------------------"

# Check if both containers are running
echo "All containers:"
docker compose ps --format "table {{.Service}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "Maintenance service specific:"
# Check for any of the candidate maintenance container names to be more robust
MAINT_PATTERN=$(echo $MAINTENANCE_CONTAINER_NAMES | tr ' ' '|')
if docker ps | grep -q -E "($MAINT_PATTERN).*Up"; then
    echo "✅ Maintenance service: Running"
    # Show which container is running
    ACTIVE_MAINTENANCE_CONTAINER=$(docker ps --format "{{.Names}}" | grep -E "($MAINT_PATTERN)" | head -1)
    echo "   Container: $ACTIVE_MAINTENANCE_CONTAINER"
else
    echo "❌ Maintenance service: Not running"
    echo "Checking logs..."
    for container in $MAINTENANCE_CONTAINER_NAMES; do
        docker logs "$container" 2>/dev/null | tail -10 && break
    done || echo "No maintenance container logs found"
fi

echo ""
echo "🔧 Maintenance System Verification"
echo "-----------------------------------"

# Test maintenance script availability
if docker exec "$MAIN_CONTAINER" test -f /mnt/storage/scripts/container-maintenance.py 2>/dev/null; then
    echo "✅ Maintenance scripts: Available in main container"
    
    # Test maintenance status
    echo ""
    echo "📊 Current maintenance status:"
    docker exec "$MAIN_CONTAINER" python3 /mnt/storage/scripts/container-maintenance.py --status 2>/dev/null | head -20 || echo "❌ Status check failed"
    
else
    echo "❌ Maintenance scripts: Not found in container"
    echo "   The maintenance system may not be included in the Docker image yet"
fi

# Check if any maintenance service container has scripts
if docker ps | grep -q -E "($MAINT_PATTERN)"; then
    MAINTENANCE_CONTAINER=$(docker ps --format "{{.Names}}" | grep -E "($MAINT_PATTERN)" | head -1)
    echo ""
    echo "📊 Maintenance service status ($MAINTENANCE_CONTAINER):"
    docker exec "$MAINTENANCE_CONTAINER" python3 /mnt/storage/scripts/container-maintenance.py --status 2>/dev/null | head -20 || echo "❌ Maintenance service status check failed"
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
docker exec "$MAIN_CONTAINER" printenv | grep MAINTENANCE 2>/dev/null || echo "  No MAINTENANCE_* environment variables found"

# Check in maintenance service if it exists
if docker ps | grep -q -E "(data-maintenance)"; then
    MAINTENANCE_CONTAINER=$(docker ps --format "{{.Names}}" | grep -E "(data-maintenance)" | head -1)
    echo ""
    echo "Maintenance configuration in maintenance service ($MAINTENANCE_CONTAINER):"
    docker exec "$MAINTENANCE_CONTAINER" printenv | grep MAINTENANCE 2>/dev/null || echo "  No MAINTENANCE_* environment variables found"
fi

echo ""
echo "🕐 Scheduled Maintenance Check"
echo "-----------------------------"

# Check if cron is available in containers
if docker exec "$MAIN_CONTAINER" which cron >/dev/null 2>&1; then
    echo "✅ Cron available in main container"
    echo "Cron jobs:"
    docker exec "$MAIN_CONTAINER" crontab -l 2>/dev/null || echo "  No cron jobs configured"
else
    echo "❌ Cron not available in main container"
fi

if docker ps | grep -q -E "($MAINT_PATTERN)"; then
    MAINTENANCE_CONTAINER=$(docker ps --format "{{.Names}}" | grep -E "($MAINT_PATTERN)" | head -1)
    if docker exec "$MAINTENANCE_CONTAINER" which cron >/dev/null 2>&1; then
        echo "✅ Cron available in maintenance service ($MAINTENANCE_CONTAINER)"
        echo "Cron jobs:"
        docker exec "$MAINTENANCE_CONTAINER" crontab -l 2>/dev/null || echo "  No cron jobs configured"
    else
        echo "ℹ️  Cron not available in maintenance service ($MAINTENANCE_CONTAINER) - using daemon mode instead"
    fi
fi

echo ""
echo "🚀 Manual Maintenance Test"
echo "-------------------------"

# Test manual maintenance execution
echo "Testing manual maintenance execution..."
MAINTENANCE_CONTAINER=$(docker ps --format "{{.Names}}" | grep -E "($MAINT_PATTERN)" | head -1)

if docker exec "$MAIN_CONTAINER" python3 /mnt/storage/scripts/container-maintenance.py --status >/dev/null 2>&1; then
    echo "✅ Manual maintenance execution: Working (main container)"
    echo ""
    echo "🧹 You can run manual maintenance with:"
    echo "  docker exec $MAIN_CONTAINER python3 /mnt/storage/scripts/container-maintenance.py --daily-cleanup"
    echo "  docker exec $MAIN_CONTAINER python3 /mnt/storage/scripts/container-maintenance.py --emergency-cleanup"
elif [ -n "$MAINTENANCE_CONTAINER" ] && docker exec "$MAINTENANCE_CONTAINER" python3 /mnt/storage/scripts/container-maintenance.py --status >/dev/null 2>&1; then
    echo "✅ Manual maintenance execution: Working (via maintenance service: $MAINTENANCE_CONTAINER)"
    echo ""
    echo "🧹 You can run manual maintenance with:"
    echo "  docker exec $MAINTENANCE_CONTAINER python3 /mnt/storage/scripts/container-maintenance.py --daily-cleanup"
    echo "  docker exec $MAINTENANCE_CONTAINER python3 /mnt/storage/scripts/container-maintenance.py --emergency-cleanup"
else
    echo "❌ Manual maintenance execution: Failed"
    echo "   Check if maintenance scripts are included in Docker image"
fi

echo ""
echo "📊 Next Steps"
echo "============"

# Determine what needs to be done based on findings
MAINTENANCE_CONTAINER=$(docker ps --format "{{.Names}}" | grep -E "($MAINT_PATTERN)" | head -1)

# Check if both main container has scripts AND maintenance service is running
MAIN_HAS_SCRIPTS=$(docker exec "$MAIN_CONTAINER" test -f /mnt/storage/scripts/container-maintenance.py 2>/dev/null && echo "true" || echo "false")
MAINTENANCE_SERVICE_RUNNING=$([ -n "$MAINTENANCE_CONTAINER" ] && docker ps | grep -q -E "($MAINT_PATTERN).*Up" && echo "true" || echo "false")

if [ "$MAIN_HAS_SCRIPTS" = "true" ] && [ "$MAINTENANCE_SERVICE_RUNNING" = "true" ]; then
    echo "🎉 OPTIMAL: Dual-Container Maintenance System Fully Operational!"
    echo ""
    echo "✅ What's working:"
    echo "  • Main container ($MAIN_CONTAINER): Has maintenance scripts"
    echo "  • Dedicated service ($MAINTENANCE_CONTAINER): Running in daemon mode"
    echo "  • Dual redundancy: Maintenance available in both containers"
    echo "  • Manual operations: Available via both containers"
    echo ""
    echo "🕐 Automatic schedule (via $MAINTENANCE_CONTAINER):"
    echo "  • Daemon mode: Continuous monitoring and maintenance"
    echo "  • Background cleanup: As needed based on thresholds"
    echo "  • Storage monitoring: Real-time space management"
    echo ""
    echo "📊 Monitor with:"
    echo "  docker logs $MAINTENANCE_CONTAINER -f"
    echo "  docker exec $MAINTENANCE_CONTAINER python3 /mnt/storage/scripts/container-maintenance.py --status"
    
elif [ "$MAINTENANCE_SERVICE_RUNNING" = "true" ] && [ -n "$MAINTENANCE_CONTAINER" ]; then
    echo "🎉 Maintenance service is fully operational!"
    echo ""
    echo "✅ What's working:"
    echo "  • Maintenance service ($MAINTENANCE_CONTAINER) is running"
    echo "  • Scripts are accessible"
    echo "  • Manual operations available"
    echo ""
    echo "🕐 Automatic schedule:"
    echo "  • Daemon mode: Continuous monitoring"
    echo "  • Background cleanup: As needed"
    echo "  • Storage monitoring: Real-time"
    echo ""
    echo "📊 Monitor with:"
    echo "  docker logs $MAINTENANCE_CONTAINER -f"
    echo "  docker exec $MAINTENANCE_CONTAINER python3 /mnt/storage/scripts/container-maintenance.py --status"
    
elif docker exec "$MAIN_CONTAINER" test -f /mnt/storage/scripts/container-maintenance.py 2>/dev/null; then
    echo "⚠️  Single-container deployment detected"
    echo ""
    echo "✅ Maintenance scripts are in main container"
    echo "❌ Dedicated maintenance service not running"
    echo ""
    echo "🔧 To enable full maintenance:"
    echo "  1. Check if docker-compose.yml includes maintenance service"
    echo "  2. Restart deployment: docker compose down && docker compose up -d"
    echo ""
    echo "🧹 For now, you can run manual maintenance:" 
    echo "  docker exec $MAIN_CONTAINER python3 /mnt/storage/scripts/container-maintenance.py --daily-cleanup"
    
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