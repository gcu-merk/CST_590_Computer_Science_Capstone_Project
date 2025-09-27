#!/bin/bash
# Log Path Verification Script
# Ensures all application logs are configured to use SSD storage (/mnt/storage)

set -e

echo "🔍 Verifying all logs are configured to use SSD storage..."
echo "==========================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

info() {
    echo -e "${BLUE}📋 $1${NC}"
}

# Check if /mnt/storage exists
if [ ! -d "/mnt/storage" ]; then
    error "SSD mount point /mnt/storage does not exist!"
    echo "Please ensure the SSD is mounted before continuing."
    exit 1
fi

success "SSD mount point /mnt/storage exists"

# Create log directories if they don't exist
echo ""
info "Creating log directory structure on SSD..."
sudo mkdir -p /mnt/storage/logs/{applications,docker,maintenance,system}
sudo chmod -R 777 /mnt/storage/logs
success "Log directory structure created"

# Verify Docker Compose logging configuration
echo ""
info "Checking Docker Compose logging configuration..."

if grep -q "/mnt/storage/logs/docker:/mnt/storage/logs/docker" docker-compose.yml; then
    success "Docker container logs configured for SSD"
else
    error "Docker container logs not configured for SSD"
fi

if grep -q "json-file" docker-compose.yml; then
    success "Docker logging driver set to json-file"
else
    warning "Docker logging driver may not be configured"
fi

# Verify systemd service logging
echo ""
info "Checking systemd service logging configuration..."

if [ -f "deployment/host-camera-capture.service" ]; then
    if grep -q "StandardOutput=journal" deployment/host-camera-capture.service; then
        success "Host camera service logs to systemd journal"
    else
        warning "Host camera service logging not configured for journal"
    fi
    
    if grep -q "/mnt/storage" deployment/host-camera-capture.service; then
        success "Host camera service has SSD write access"
    else
        error "Host camera service does not have SSD write access"
    fi
else
    error "Host camera service file not found"
fi

# Verify Python script logging
echo ""
info "Checking Python script logging configuration..."

if [ -f "scripts/hardware/host-camera-capture.py" ]; then
    if grep -q "/mnt/storage/logs" scripts/hardware/host-camera-capture.py; then
        success "Host camera capture script logs to SSD"
    else
        error "Host camera capture script not configured for SSD logging"
    fi
    
    # Check for any /var/log references
    if grep -q "/var/log" scripts/hardware/host-camera-capture.py; then
        warning "Host camera capture script still has /var/log references"
    else
        success "Host camera capture script has no /var/log references"
    fi
else
    error "Host camera capture script not found"
fi

if [ -f "scripts/image-sync-manager.py" ]; then
    if grep -q "/mnt/storage/logs" scripts/image-sync-manager.py; then
        success "Image sync manager logs to SSD"
    else
        error "Image sync manager not configured for SSD logging"
    fi
else
    warning "Image sync manager script not found"
fi

# Check for any remaining /var/log references in key files
echo ""
info "Scanning for remaining /var/log references..."

var_log_files=$(grep -r "/var/log" --include="*.py" --include="*.sh" --include="*.service" . 2>/dev/null | grep -v ".git" | grep -v "storage-migration.sh" | grep -v "storage-analysis.sh" || true)

if [ -z "$var_log_files" ]; then
    success "No problematic /var/log references found"
else
    warning "Found remaining /var/log references:"
    echo "$var_log_files"
fi

# Check current log files on system
echo ""
info "Checking current log file locations..."

# Host service logs
if systemctl is-active --quiet host-camera-capture 2>/dev/null; then
    success "Host camera service is running"
    echo "  Log command: journalctl -u host-camera-capture -f"
else
    info "Host camera service not currently running"
fi

# Application logs on SSD
if [ -d "/mnt/storage/logs/applications" ]; then
    log_files=$(find /mnt/storage/logs/applications -name "*.log" 2>/dev/null || true)
    if [ -n "$log_files" ]; then
        success "Application logs found on SSD:"
        ls -la /mnt/storage/logs/applications/
    else
        info "No application logs found yet (normal for new deployment)"
    fi
else
    warning "Application logs directory not found on SSD"
fi

# Docker logs
echo ""
info "Docker container logging status..."
if command -v docker-compose >/dev/null 2>&1; then
    if docker-compose ps >/dev/null 2>&1; then
        containers=$(docker-compose ps --services 2>/dev/null || true)
        if [ -n "$containers" ]; then
            success "Docker services detected:"
            docker-compose ps
            echo ""
            info "Container logs location: /var/lib/docker/containers/"
            info "Application logs in containers: /mnt/storage/logs/docker -> /mnt/storage/logs/docker"
        else
            info "No Docker services currently running"
        fi
    else
        info "Docker compose not configured in current directory"
    fi
else
    warning "docker-compose command not available"
fi

# Summary
echo ""
echo "==========================================================="
info "Log Configuration Summary:"
echo ""
echo "📍 SSD Log Locations:"
echo "  • Host service: journalctl -u host-camera-capture"
echo "  • Applications: /mnt/storage/logs/applications/"
echo "  • Docker containers: /mnt/storage/logs/docker/"
echo "  • Maintenance: /mnt/storage/logs/maintenance/"
echo ""
echo "🚀 To monitor logs:"
echo "  • Host service: journalctl -u host-camera-capture -f"
echo "  • Containers: docker-compose logs -f"
echo "  • Application files: tail -f /mnt/storage/logs/applications/*.log"
echo ""

if [ -z "$var_log_files" ]; then
    success "All logs are configured to use SSD storage! ✨"
    exit 0
else
    warning "Some log references may still need attention"
    exit 1
fi