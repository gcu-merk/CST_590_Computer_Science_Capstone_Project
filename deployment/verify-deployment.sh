#!/bin/bash
# Post-deployment verification script for host camera capture integration

set -e

echo "🔍 Host Camera Capture Integration - Verification Script"
echo "========================================================"

DEPLOY_DIR="/home/merk/traffic-monitor-deploy"
SERVICE_NAME="host-camera-capture"

# Function to check service status
check_service_status() {
    echo "🔧 Checking systemd service status..."
    
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        echo "✅ Host camera service is running"
        sudo systemctl status "$SERVICE_NAME" --no-pager -l | head -8
    else
        echo "❌ Host camera service is not running"
        sudo systemctl status "$SERVICE_NAME" --no-pager -l | head -10
        return 1
    fi
}

# Function to check Docker services
check_docker_services() {
    echo "🐳 Checking Docker services..."
    
    cd "$DEPLOY_DIR"
    if docker-compose ps | grep -q "Up"; then
        echo "✅ Docker services are running"
        docker-compose ps
    else
        echo "❌ Docker services are not running properly"
        docker-compose ps
        return 1
    fi
}

# Function to check recent image captures
check_image_captures() {
    echo "📸 Checking recent image captures..."
    
    CAPTURE_DIR="/mnt/storage/camera_capture/live"
    if [ ! -d "$CAPTURE_DIR" ]; then
        echo "❌ Capture directory does not exist: $CAPTURE_DIR"
        return 1
    fi
    
    # Check for recent images (within last 5 minutes)
    RECENT_IMAGES=$(find "$CAPTURE_DIR" -name "capture_*.jpg" -mmin -5 2>/dev/null | wc -l)
    
    if [ "$RECENT_IMAGES" -gt 0 ]; then
        echo "✅ Found $RECENT_IMAGES recent image(s) captured"
        echo "Recent captures:"
        find "$CAPTURE_DIR" -name "capture_*.jpg" -mmin -5 -exec basename {} \; | head -3
    else
        echo "⚠️ No recent images found (captured within last 5 minutes)"
        echo "All captures:"
        ls -la "$CAPTURE_DIR" | tail -5 2>/dev/null || echo "No captures found"
    fi
}

# Function to check API health
check_api_health() {
    echo "🌐 Checking API health..."
    
    if curl -f -s http://localhost:5000/api/health >/dev/null 2>&1; then
        echo "✅ Weather API is responding"
        curl -s http://localhost:5000/api/health | python3 -m json.tool 2>/dev/null || echo "API responded but JSON parsing failed"
    else
        echo "⚠️ Weather API is not responding (may still be starting up)"
    fi
}

# Function to check storage usage
check_storage_usage() {
    echo "💾 Checking storage usage..."
    
    if [ -d "/mnt/storage/camera_capture" ]; then
        echo "Camera capture storage:"
        du -sh /mnt/storage/camera_capture/* 2>/dev/null || echo "Storage directories not yet populated"
        
        echo "Available disk space:"
        df -h /mnt/storage | tail -1
    else
        echo "❌ Storage mount not found at /mnt/storage"
        return 1
    fi
}

# Function to check logs
check_logs() {
    echo "📋 Checking recent logs..."
    
    echo "Host camera service logs (last 10 lines):"
    sudo journalctl -u "$SERVICE_NAME" -n 10 --no-pager || echo "No logs available"
    
    echo ""
    echo "Docker container logs (last 5 lines each):"
    cd "$DEPLOY_DIR"
    docker-compose logs --tail=5 2>/dev/null || echo "Docker logs not available"
}

# Main verification sequence
main() {
    echo "Starting verification at $(date)"
    echo ""
    
    FAILED_CHECKS=0
    
    # Run all checks
    check_service_status || ((FAILED_CHECKS++))
    echo ""
    
    check_docker_services || ((FAILED_CHECKS++))
    echo ""
    
    check_image_captures
    echo ""
    
    check_api_health
    echo ""
    
    check_storage_usage || ((FAILED_CHECKS++))
    echo ""
    
    check_logs
    echo ""
    
    # Final summary
    echo "========================================================"
    if [ $FAILED_CHECKS -eq 0 ]; then
        echo "🎉 All critical checks passed! System is healthy."
    else
        echo "⚠️ $FAILED_CHECKS critical check(s) failed. Review the output above."
    fi
    
    echo "Verification completed at $(date)"
    
    return $FAILED_CHECKS
}

# Run main function
main