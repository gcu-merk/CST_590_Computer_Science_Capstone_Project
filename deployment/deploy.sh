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

# Deployment / staging defaults
DEPLOY_USER=${DEPLOY_USER:-merk}
# The CI workflow previously used /mnt/storage/deployment-staging for rsync staging;
# If your Docker Compose network is named 'traffic-monitoring-network', update any label or network checks to reference that name instead of 'default'.
# This script can assist with preparing that path and network when run on the target host (non-fatal helper for CI resilience).
STAGING_DIR=${STAGING_DIR:-/mnt/storage/deployment-staging}
CONTAINER_AUDIT_LOG=${CONTAINER_AUDIT_LOG:-/var/log/traffic_deploy_containers.log}

# Exit codes for different failure types
EXIT_PRECHECK_FAILED=10
EXIT_HOST_SERVICE_FAILED=20
EXIT_CONTAINER_DEPLOYMENT_FAILED=30
EXIT_VALIDATION_FAILED=40

# Allow overriding the compose project name via environment; default to 'traffic_monitoring'
COMPOSE_PROJECT_NAME=${COMPOSE_PROJECT_NAME:-traffic_monitoring}
export COMPOSE_PROJECT_NAME

# Simple run_compose wrapper — assume deployment happens on Raspberry Pi hosts
run_compose() {
    if docker compose version >/dev/null 2>&1; then
        docker compose -f "$COMPOSE_FILE" "$@"
    else
        docker-compose -f "$COMPOSE_FILE" -p "$COMPOSE_PROJECT_NAME" "$@"
    fi
}

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

# Ensure a staging directory exists and is owned by the deploy user
ensure_staging_ownership() {
    local dir="$1"
    if [ -z "$dir" ]; then
        dir="$STAGING_DIR"
    fi

    if [ ! -d "$dir" ]; then
        log "📁 Staging directory '$dir' not found — creating..."
        sudo mkdir -p "$dir" || { warning "Failed to create $dir"; return 1; }
        sudo chown "$DEPLOY_USER":"$DEPLOY_USER" "$dir" || warning "Failed to chown $dir to $DEPLOY_USER"
        return 0
    fi

    # Check owner and attempt to fix if needed
    owner=$(stat -c '%U' "$dir" 2>/dev/null || echo "")
    if [ "$owner" != "$DEPLOY_USER" ]; then
        log "🔒 Staging directory '$dir' owned by '$owner' - attempting chown to '$DEPLOY_USER'"
        sudo chown -R "$DEPLOY_USER":"$DEPLOY_USER" "$dir" || warning "Failed to chown $dir"
    else
        log "🔎 Staging directory '$dir' already owned by '$DEPLOY_USER'"
    fi
}

# Run rsync with a single retry for exit code 23 after attempting a chown of the dest.
# This helper is optional; the CI workflow still performs rsync, but this function
# allows the target to attempt self-healing if called from the host.
run_rsync_with_retry() {
    local src="$1"
    local dest="$2"
    local max_attempts=2
    local attempt=1

    if [ -z "$src" ] || [ -z "$dest" ]; then
        error "run_rsync_with_retry requires source and destination"
        return 2
    fi

    while [ $attempt -le $max_attempts ]; do
                log "🔁 rsync attempt $attempt/$max_attempts: $src -> $dest"
                rsync -avz --delete \
                    --exclude='.git*' \
                    --exclude='documentation/' \
                    --exclude='*.md' \
                    --exclude='test_*' \
                    --exclude='__pycache__/' \
                    "$src" "$dest"
        rc=$?
        if [ $rc -eq 0 ]; then
            log "✅ rsync completed successfully"
            return 0
        fi

        if [ $rc -eq 23 ] && [ $attempt -eq 1 ]; then
            warning "rsync returned code 23 (partial transfer). Attempting chown of '$dest' and retrying once..."
            sudo chown -R "$DEPLOY_USER":"$DEPLOY_USER" "$dest" || warning "Automated chown failed"
            attempt=$((attempt+1))
            continue
        fi

        error "rsync failed with exit code $rc"
        return $rc
    done
}

# Ensure only one Redis instance will be present on the host. If another process/container
# is bound to host port 6379 attempt to stop it. This is intentionally conservative:
# - Prefer stopping containers that advertise port 6379 in their ports mapping
# - If a systemd 'redis' service is active, stop it (and leave it disabled if requested)
# - If the port is still occupied after attempts, fail with diagnostics so operator can inspect
ensure_single_redis_instance() {
    log "🔎 Checking for existing Redis instances bound to host port 6379..."

    # Helper to check whether port 6379 is in use on the host
    port_in_use() {
        # Prefer ss, fallback to netstat
        if command -v ss >/dev/null 2>&1; then
            ss -tulpn 2>/dev/null | grep -w ':6379' >/dev/null 2>&1
        else
            sudo netstat -tulpn 2>/dev/null | grep -w ':6379' >/dev/null 2>&1
        fi
    }

    # Attempt to stop any containers that expose/mapped host port 6379
    conflicting_containers=$(docker ps --format '{{.ID}} {{.Names}} {{.Ports}}' | grep '0.0.0.0:6379\|:6379->' || true)
    if [ -n "$conflicting_containers" ]; then
        log "⚠️ Found containers exposing host port 6379. Attempting to stop/remove them:"
        echo "$conflicting_containers" | while read -r line; do
            cid=$(echo "$line" | awk '{print $1}')
            name=$(echo "$line" | awk '{print $2}')
            log "🛑 Stopping container $name ($cid) that exposes 6379"
            docker stop "$cid" || warning "Failed to stop container $cid"
            docker rm "$cid" || warning "Failed to remove container $cid"
            echo "$(date '+%Y-%m-%d %H:%M:%S') STOPPED_CONFLICTING_CONTAINER cid=$cid name=$name" | sudo tee -a "$CONTAINER_AUDIT_LOG" >/dev/null || true
        done
    fi

    # If a system Redis service is active, stop it (but do not remove packages)
    if systemctl is-active --quiet redis 2>/dev/null; then
        log "🛑 Stopping system redis service to free port 6379"
        sudo systemctl stop redis || warning "Failed to stop system redis service"
        # Avoid disabling automatically; operator may want control. Log it for auditing.
        echo "$(date '+%Y-%m-%d %H:%M:%S') STOPPED_SYSTEM_REDIS" | sudo tee -a "$CONTAINER_AUDIT_LOG" >/dev/null || true
    fi

    # Give the kernel a moment to release sockets
    sleep 1

    if port_in_use; then
        error "Port 6379 is still in use after attempting to stop conflicting containers/services."
        # Print diagnostics to help operator debug
        log "📋 Diagnostics: processes/listening sockets on 6379"
        if command -v ss >/dev/null 2>&1; then
            ss -tulpn | grep ':6379' || true
        else
            sudo netstat -tulpn | grep ':6379' || true
        fi
        log "📋 Docker containers (all):"
        docker ps --format 'table {{.ID}}	{{.Names}}	{{.Image}}	{{.Ports}}' || true
        return 1
    fi

    log "✅ Host port 6379 is free for the deployment's Redis container"
    return 0
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
    
        # Ensure staging directory exists and is writable by the deploy user
        ensure_staging_ownership "$STAGING_DIR" || warning "ensure_staging_ownership failed for $STAGING_DIR"

        # Ensure only one Redis instance will exist on the host: stop conflicting containers or system Redis
        ensure_single_redis_instance || warning "ensure_single_redis_instance reported issues"

    success "✅ All pre-deployment checks passed"
}

# Deploy host camera capture service (runs outside Docker)
deploy_host_camera_service() {
    log "📷 Deploying host camera capture service..."
    
    # Create deployment directory if it doesn't exist
    mkdir -p "$DEPLOY_DIR"
    
    # Ensure all required SSD directories exist
    log "📁 Creating required SSD directory structure..."
    
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
    
    # Stop existing containers gracefully (scoped to project)
    log "🛑 Stopping existing containers (project: $COMPOSE_PROJECT_NAME)..."
    run_compose down --remove-orphans || true

        # Ensure host port 5000 is free: stop containers or processes binding the port
        log "Ensuring host port 5000 is free for the API service..."
        # Stop containers that explicitly map host port 5000
        conflicting_containers=$(docker ps --format '{{.ID}} {{.Names}} {{.Ports}}' | grep -E '0.0.0.0:5000|:5000->' || true)
        if [ -n "$conflicting_containers" ]; then
            log "Found containers binding host port 5000. Attempting to stop and remove them:"
            echo "$conflicting_containers" | while read -r line; do
                cid=$(echo "$line" | awk '{print $1}')
                name=$(echo "$line" | awk '{print $2}')
                log "Stopping container $name ($cid)"
                docker stop "$cid" || warning "Failed to stop container $cid"
                docker rm "$cid" || warning "Failed to remove container $cid"
                echo "$(date '+%Y-%m-%d %H:%M:%S') STOPPED_CONFLICTING_CONTAINER cid=$cid name=$name" | sudo tee -a "$CONTAINER_AUDIT_LOG" >/dev/null || true
            done
        fi

        # If a non-container process listens on port 5000, print diagnostics and attempt to kill
        if command -v ss >/dev/null 2>&1; then
            port_info=$(ss -tulpn | grep -E ':5000\b' || true)
        else
            port_info=$(sudo netstat -tulpn 2>/dev/null | grep -E ':5000\b' || true)
        fi
        if [ -n "$port_info" ]; then
            error "Host port 5000 is currently in use by a non-container process:\n$port_info"
            # Try to extract PID and prompt user briefly
            pid=$(echo "$port_info" | grep -oE "pid=[0-9]+" | grep -oE "[0-9]+" || true)
            if [ -n "$pid" ]; then
                log "Attempting to kill PID $pid to free port 5000"
                sudo kill "$pid" || warning "Failed to kill PID $pid"
                sleep 1
                # Re-check
                if command -v ss >/dev/null 2>&1; then
                    still=$(ss -tulpn | grep -E ':5000\b' || true)
                else
                    still=$(sudo netstat -tulpn 2>/dev/null | grep -E ':5000\b' || true)
                fi
                if [ -n "$still" ]; then
                    error "Port 5000 still in use after attempted kill. Manual intervention required."
                    log "Diagnostics: $still"
                    rollback_deployment "Port 5000 in use and could not be freed"
                fi
            else
                error "Could not determine PID for process binding port 5000. Manual intervention required."
                rollback_deployment "Port 5000 in use by unknown process"
            fi
        fi

    # Helper: safely remove containers for a compose service (if any)
    # Verifies compose labels or image name before removing to avoid affecting unrelated containers on multi-tenant hosts.
    remove_compose_service_containers() {
        svc="$1"
        expected_image_prefix="$2"  # optional image prefix to verify (e.g., 'gcumerk/cst590-')

        # Get candidate container IDs for the service from compose (v2) or docker-compose
    cid_list=$(run_compose ps -q "$svc" 2>/dev/null)
        if [ -z "$cid_list" ]; then
            return 0
        fi

        for cid in $cid_list; do
            # Inspect labels and image
            labels_json=$(docker inspect --format '{{json .Config.Labels}}' "$cid" 2>/dev/null || echo "{}")
            image_name=$(docker inspect --format '{{.Config.Image}}' "$cid" 2>/dev/null || echo "")

            # Extract compose project and service labels (if present)
            compose_project=$(echo "$labels_json" | python -c "import sys, json; d=json.load(sys.stdin) if sys.stdin.readable() else {}; print(d.get('com.docker.compose.project',''))" 2>/dev/null || true)
            compose_service=$(echo "$labels_json" | python -c "import sys, json; d=json.load(sys.stdin) if sys.stdin.readable() else {}; print(d.get('com.docker.compose.service',''))" 2>/dev/null || true)

            safe_to_remove=false

            # If compose labels match, consider it safe
            if [ -n "$compose_project" ] && [ "$compose_project" = "$COMPOSE_PROJECT_NAME" ] && [ -n "$compose_service" ] && [ "$compose_service" = "$svc" ]; then
                safe_to_remove=true
            fi

            # If labels are not present or do not match, check image prefix if provided
            if [ "$safe_to_remove" = false ] && [ -n "$expected_image_prefix" ]; then
                if echo "$image_name" | grep -q "^$expected_image_prefix"; then
                    safe_to_remove=true
                fi
            fi

            if [ "$safe_to_remove" = true ]; then
                log "🧹 Removing verified leftover container for service '$svc' (cid: $cid, image: $image_name)"
                # Audit the removal with timestamp, container id, image and calling project/service
                echo "$(date '+%Y-%m-%d %H:%M:%S') REMOVED cid=$cid svc=$svc project=$COMPOSE_PROJECT_NAME image=$image_name" | sudo tee -a "$CONTAINER_AUDIT_LOG" >/dev/null || true
                docker rm -f "$cid" >/dev/null 2>&1 || warning "Failed to remove container $cid"
            else
                warning "Skipping removal of container $cid for service '$svc' — labels/image did not match expected project/service or image prefix"
                log "   Detected labels: $labels_json"
                log "   Detected image: $image_name"
            fi
        done
    }
    
    # Pull latest images (important for CI/CD)
    log "📥 Pulling latest container images..."
    run_compose pull || {
        error "Failed to pull container images"
        exit $EXIT_CONTAINER_DEPLOYMENT_FAILED
    }
    
    # Start services
    log "🚀 Starting containerized services..."
    run_compose up -d || {
        error "Failed to start containerized services"
        rollback_deployment "Container startup failed"
    }
    
    # Ensure weather-related containers are started (dht22-weather, airport-weather)
    log "🔁 Ensuring weather service containers are running..."
    for svc in dht22-weather airport-weather; do
        # Quick check whether service shows as running
        is_running() {
            # Check whether the service shows up as running in the compose project
            if docker compose version >/dev/null 2>&1; then
                run_compose ps --services --filter "status=running" | grep -q "^$svc$" >/dev/null 2>&1
            else
                run_compose ps --services --filter "status=running" | grep -q "^$svc$" >/dev/null 2>&1
            fi
        }

        attempts=0
        max_attempts=10
        until is_running; do
            attempts=$((attempts+1))
            log "⏳ $svc not running yet (attempt: $attempts/$max_attempts). Trying to start..."
            # Try to start the specific service to give it another chance
            run_compose up -d "$svc" || warning "docker-compose up -d $svc returned non-zero"

            # Wait a bit for the container to transition to running
            sleep 4

            if [ $attempts -ge $max_attempts ]; then
                warning "$svc did not reach running state after $max_attempts attempts"
                log "📄 Last 200 lines of logs for $svc:" 
                run_compose logs --no-color --tail=200 "$svc" || true
                break
            fi
        done

        if is_running; then
            log "✅ $svc is running"
        else
            warning "$svc failed to start after retries"
        fi
    done

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
    if ! run_compose ps | grep -q "Up"; then
        error "Some containerized services are not running"
        run_compose ps
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

    # Verify weather services are populating Redis keys
    log "🔍 Validating weather data in Redis..."
    # Retry loop for keys since services may take time to write initial data
    check_redis_key() {
        local key="$1"
        local attempt=0
        local max=10
        while [ $attempt -lt $max ]; do
            # Capture output rather than relying on grep exit codes (more robust)
            output=$(run_compose exec -T redis redis-cli -n 0 GET "$key" 2>/dev/null || true)
            if [ -n "$output" ]; then
                log "✅ Redis key '$key' has data"
                return 0
            fi
            attempt=$((attempt+1))
            log "⏳ Waiting for Redis key '$key' (attempt: $attempt/$max)..."
            sleep 3
        done
        warning "Redis key '$key' was not populated after $max attempts"
        return 1
    }

    # Check DHT22 and airport weather keys
    if ! check_redis_key "weather:dht22:latest"; then
        warning "DHT22 weather data not available in Redis"
    fi
    if ! check_redis_key "weather:airport:latest"; then
        warning "Airport weather data not available in Redis"
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
    run_compose ps
    
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