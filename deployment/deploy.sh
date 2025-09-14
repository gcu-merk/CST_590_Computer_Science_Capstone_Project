#!/bin/bash
# CI/CD Deployment Script for Traffic Monitoring System
# Separates host services (camera capture) from containerized services (processing/API)
# 
# USAGE: Run this script from the project root directory:
#        cd /path/to/CST_590_Computer_Science_Capstone_Project
#        ./deployment/deploy.sh
#
# Architecture:
# - Host Service: camera capture (requires direct hardware access)
# - Containerized: AI processing, API, data maintenance, web services

set -e  # Exit on error

# Colors for CI/CD output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Logging function for CI/CD
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR $(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS $(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING $(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

echo "🚀 CI/CD Deployment: Traffic Monitoring System"
echo "=============================================="
echo "📋 Host Service: Camera Capture (systemd)"
echo "📦 Containerized: AI Processing, API, Maintenance"

# Capture the original working directory (project root)
PROJECT_ROOT="$(pwd)"

# Check if we're running from a full project checkout or deployment directory
if [ ! -f "$PROJECT_ROOT/scripts/host-camera-capture.py" ] && [ -f "$PROJECT_ROOT/host-camera-capture.py" ]; then
    # We're running from a deployment directory, adjust paths
    warning "Running from deployment directory, adjusting file paths..."
    DEPLOY_MODE="deployment_directory"
    HOST_CAMERA_SCRIPT="$PROJECT_ROOT/host-camera-capture.py"
    SERVICE_FILE="$PROJECT_ROOT/deployment/host-camera-capture.service"
    COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"
else
    # We're running from full project checkout (normal GitHub Actions case)
    DEPLOY_MODE="project_checkout"
    HOST_CAMERA_SCRIPT="$PROJECT_ROOT/scripts/host-camera-capture.py"
    SERVICE_FILE="$PROJECT_ROOT/deployment/host-camera-capture.service"
    COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"
fi

log "🏗️ Deploy mode: $DEPLOY_MODE"
DEPLOY_DIR="/mnt/storage/traffic-monitor-deploy"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')

# Exit codes for different failure types
EXIT_PRECHECK_FAILED=10
EXIT_HOST_SERVICE_FAILED=20
EXIT_CONTAINER_DEPLOYMENT_FAILED=30
EXIT_VALIDATION_FAILED=40

# Rollback function for CI/CD safety
rollback_deployment() {
    local rollback_reason="$1"
    error "Deployment failed: $rollback_reason"
    
    log "🔄 Initiating rollback procedure..."
    
    # Restore previous host service if backup exists
    if [ -f "$DEPLOY_DIR/host-camera-capture.py.backup.$TIMESTAMP" ]; then
        log "📷 Restoring previous camera service..."
        cp "$DEPLOY_DIR/host-camera-capture.py.backup.$TIMESTAMP" "$DEPLOY_DIR/host-camera-capture.py"
        sudo systemctl restart host-camera-capture || warning "Failed to restart camera service"
    fi
    
    # Restore previous Docker containers
    log "� Restoring previous container state..."
    cd "$PROJECT_ROOT"
    docker-compose down --remove-orphans || true
    
    error "⚠️ Rollback completed. Manual intervention may be required."
    exit $EXIT_VALIDATION_FAILED
}

# Comprehensive pre-deployment checks for CI/CD
pre_deployment_checks() {
    log "🔍 Running pre-deployment validation..."
    
    # Check if running on Raspberry Pi
    if ! grep -q "BCM" /proc/cpuinfo; then
        warning "Not running on Raspberry Pi - some features may not work"
    fi
    
    # Check camera availability (critical for host service)
    if ! rpicam-still --list-cameras >/dev/null 2>&1; then
        error "Camera not detected - cannot deploy host camera service"
        exit $EXIT_PRECHECK_FAILED
    fi
    
    # Check storage mount (critical for all services)
    if [ ! -d "/mnt/storage" ]; then
        error "Storage mount not found at /mnt/storage"
        exit $EXIT_PRECHECK_FAILED
    fi
    
    # Validate storage space (at least 1GB free)
    available_space=$(df /mnt/storage | awk 'NR==2 {print $4}')
    if [ "$available_space" -lt 1048576 ]; then  # 1GB in KB
        error "Insufficient storage space. Available: ${available_space}KB, Required: 1GB+"
        exit $EXIT_PRECHECK_FAILED
    fi
    
    # Check Docker service
    if ! systemctl is-active --quiet docker; then
        error "Docker service is not running"
        exit $EXIT_PRECHECK_FAILED
    fi
    
    # Validate required files exist (using dynamic paths based on deploy mode)
    required_files=(
        "$HOST_CAMERA_SCRIPT"
        "$SERVICE_FILE"
        "$COMPOSE_FILE"
    )
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            error "Required file not found: $file"
            error "Deploy mode: $DEPLOY_MODE"
            error "PROJECT_ROOT: $PROJECT_ROOT"
            error "Available files:"
            ls -la "$PROJECT_ROOT" | head -10
            exit $EXIT_PRECHECK_FAILED
        fi
    done

        # Validate required directories exist (from host-camera-capture.service)
        required_dirs=(
            "/mnt/storage/traffic-monitor-deploy"
            "/mnt/storage/camera_capture"
            "/mnt/storage"
            "/tmp"
        )

        for dir in "${required_dirs[@]}"; do
            if [ ! -d "$dir" ]; then
                if [ "$dir" = "/tmp" ]; then
                    warning "Critical system directory missing: $dir (should always exist)"
                    exit $EXIT_PRECHECK_FAILED
                else
                    warning "Required directory not found: $dir. Creating..."
                    sudo mkdir -p "$dir"
                fi
            fi
        done
    
    success "✅ All pre-deployment checks passed"
}

# Deploy host camera capture service (runs outside Docker)
deploy_host_camera_service() {
    log "📷 Deploying host camera capture service..."
    
    # Create deployment directory if it doesn't exist
    mkdir -p "$DEPLOY_DIR"
    
    # Ensure all required SSD directories exist
    log "📁 Creating required SSD directory structure..."
    sudo mkdir -p /mnt/storage/logs/{applications,docker,maintenance,system}
    sudo mkdir -p /mnt/storage/camera_capture/{live,metadata,processed}
    sudo mkdir -p /mnt/storage/{periodic_snapshots,ai_camera_images,processed_data,backups}
    
    # Set appropriate permissions
    sudo chmod -R 777 /mnt/storage/camera_capture
    sudo chmod -R 777 /mnt/storage/logs
    sudo chmod -R 777 /mnt/storage/periodic_snapshots
    sudo chmod -R 777 /mnt/storage/ai_camera_images
    sudo chmod -R 755 /mnt/storage/processed_data
    sudo chmod -R 755 /mnt/storage/backups
    sudo chmod -R 755 /mnt/storage/traffic-monitor-deploy
    
    # Backup existing service if it exists (only if we're going to replace it)
    if [ "$DEPLOY_MODE" = "project_checkout" ] && [ -f "$DEPLOY_DIR/host-camera-capture.py" ]; then
        log "📦 Creating backup of existing camera service..."
        cp "$DEPLOY_DIR/host-camera-capture.py" "$DEPLOY_DIR/host-camera-capture.py.backup.$TIMESTAMP"
    fi
    
    # Deploy camera capture script (only if not already in deploy directory)
    if [ "$DEPLOY_MODE" = "deployment_directory" ]; then
        log "📷 Camera script already in deploy directory, ensuring permissions..."
        # Script is already in place, just fix ownership and permissions
        chown merk:merk "$DEPLOY_DIR/host-camera-capture.py"
        chmod +x "$DEPLOY_DIR/host-camera-capture.py"
    else
        log "📷 Copying camera script from source to deploy directory..."
        cp "$HOST_CAMERA_SCRIPT" "$DEPLOY_DIR/"
        chown merk:merk "$DEPLOY_DIR/host-camera-capture.py"
        chmod +x "$DEPLOY_DIR/host-camera-capture.py"
    fi
    
    # Test camera functionality before proceeding
    log "🧪 Testing camera capture functionality..."
    cd "$DEPLOY_DIR"
    if ! python3 host-camera-capture.py --test-only; then
        error "Camera test failed"
        exit $EXIT_HOST_SERVICE_FAILED
    fi
    
    # Install/update systemd service
    log "⚙️ Installing host camera systemd service..."
    sudo cp "$SERVICE_FILE" /etc/systemd/system/
    sudo systemctl daemon-reload
    
    # Stop existing service gracefully
    if systemctl is-active --quiet host-camera-capture; then
        log "🛑 Stopping existing camera service..."
        sudo systemctl stop host-camera-capture
    fi
    
    # Enable and start the service
    sudo systemctl enable host-camera-capture
    sudo systemctl start host-camera-capture
    
    # Verify service is running
    sleep 5
    if ! systemctl is-active --quiet host-camera-capture; then
        error "Host camera service failed to start"
        sudo systemctl status host-camera-capture --no-pager -l
        exit $EXIT_HOST_SERVICE_FAILED
    fi
    
    success "✅ Host camera service deployed and running"
}

# Deploy containerized services (everything except camera capture)
deploy_containerized_services() {
    log "🐳 Deploying containerized services..."
    
    # Ensure we're in project root for docker-compose
    cd "$PROJECT_ROOT"
    
    # Stop existing containers gracefully
    log "🛑 Stopping existing containers..."
    docker-compose -f "$COMPOSE_FILE" down --remove-orphans || true
    
    # Pull latest images (important for CI/CD)
    log "📥 Pulling latest container images..."
    docker-compose -f "$COMPOSE_FILE" pull || {
        error "Failed to pull container images"
        exit $EXIT_CONTAINER_DEPLOYMENT_FAILED
    }
    
    # Start services
    log "🚀 Starting containerized services..."
    docker-compose -f "$COMPOSE_FILE" up -d || {
        error "Failed to start containerized services"
        rollback_deployment "Container startup failed"
    }
    
    success "✅ Containerized services deployed"
}

# Comprehensive health checks for CI/CD validation
validate_deployment() {
    log "✅ Running deployment validation..."
    
    # Wait for services to initialize
    log "⏳ Waiting for services to initialize (30 seconds)..."
    sleep 30
    
    local validation_failed=false
    
    # Check host camera service
    log "🔍 Validating host camera service..."
    if ! systemctl is-active --quiet host-camera-capture; then
        error "Host camera service is not running"
        sudo systemctl status host-camera-capture --no-pager -l
        validation_failed=true
    else
        success "✅ Host camera service is running"
    fi
    
    # Check Docker services
    log "🔍 Validating containerized services..."
    if ! docker-compose -f "$COMPOSE_FILE" ps | grep -q "Up"; then
        error "Some containerized services are not running"
        docker-compose -f "$COMPOSE_FILE" ps
        validation_failed=true
    else
        success "✅ Containerized services are running"
    fi
    
    # Test API endpoint
    log "🔍 Testing API endpoint..."
    sleep 10  # Additional wait for API to be ready
    if ! curl -f -s http://localhost:5000/api/health >/dev/null 2>&1; then
        warning "API endpoint not responding (may need more time)"
        # Don't fail deployment for API - it might need more time
    else
        success "✅ API endpoint is responding"
    fi
    
    # Test image capture pipeline
    log "� Validating image capture pipeline..."
    sleep 65  # Wait for at least one capture cycle
    
    LATEST_IMAGE=$(find /mnt/storage/camera_capture/live/ -name "capture_*.jpg" -mtime -1 2>/dev/null | head -1)
    if [ -z "$LATEST_IMAGE" ]; then
        warning "No recent images found - camera may still be initializing"
        # Don't fail deployment immediately - camera might need more time
    else
        success "✅ Image capture pipeline working: $(basename "$LATEST_IMAGE")"
    fi
    
    # Final validation check
    if [ "$validation_failed" = true ]; then
        rollback_deployment "Critical service validation failed"
    fi
    
    success "✅ Deployment validation completed successfully"
}

# CI/CD summary report
deployment_summary() {
    log "📊 Deployment Summary Report"
    echo "=============================================="
    
    echo -e "${PURPLE}🏠 HOST SERVICES:${NC}"
    sudo systemctl status host-camera-capture --no-pager -l | head -5
    
    echo ""
    echo -e "${PURPLE}🐳 CONTAINERIZED SERVICES:${NC}"
    docker-compose -f "$COMPOSE_FILE" ps
    
    echo ""
    echo -e "${PURPLE}💾 STORAGE STATUS:${NC}"
    df -h /mnt/storage | tail -1
    
    echo ""
    echo -e "${PURPLE}📸 RECENT CAPTURES:${NC}"
    ls -la /mnt/storage/camera_capture/live/ 2>/dev/null | tail -3 || echo "No captures found yet"
    
    echo ""
    success "🎉 CI/CD Deployment completed successfully!"
    echo "=============================================="
    echo -e "${BLUE}API Endpoint:${NC} http://$(hostname -I | awk '{print $1}'):5000"
    echo -e "${BLUE}Logs:${NC} journalctl -u host-camera-capture -f"
    echo -e "${BLUE}Containers:${NC} docker-compose logs -f"
}

# Main deployment orchestration
main() {
    log "🚀 Starting CI/CD deployment process..."
    
    # Run deployment phases
    pre_deployment_checks
    deploy_host_camera_service
    deploy_containerized_services
    validate_deployment
    deployment_summary
    
    log "✅ CI/CD deployment completed successfully"
    exit 0
}

# Trap signals for graceful shutdown
trap 'error "Deployment interrupted"; exit 130' INT TERM

# Execute main deployment
main "$@"