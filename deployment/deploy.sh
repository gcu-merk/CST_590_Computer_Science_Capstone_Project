#!/bin/bash
# CI/CD Deployment Script for Traffic Monitoring System
# Updated to handle Redis and PostgreSQL services properly

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
echo "📦 Containerized: Redis, PostgreSQL, AI Processing, API, Maintenance"

# Capture the original working directory (project root)
PROJECT_ROOT="$(pwd)"

# Check if we're running from a full project checkout or deployment directory
if [ ! -f "$PROJECT_ROOT/scripts/host-camera-capture.py" ] && [ -f "$PROJECT_ROOT/host-camera-capture.py" ]; then
    warning "Running from deployment directory, adjusting file paths..."
    DEPLOY_MODE="deployment_directory"
    HOST_CAMERA_SCRIPT="$PROJECT_ROOT/host-camera-capture.py"
    SERVICE_FILE="$PROJECT_ROOT/deployment/host-camera-capture.service"
    COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"
else
    DEPLOY_MODE="project_checkout"
    HOST_CAMERA_SCRIPT="$PROJECT_ROOT/scripts/host-camera-capture.py"
    SERVICE_FILE="$PROJECT_ROOT/deployment/host-camera-capture.service"
    COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"
fi

log "🗂️ Deploy mode: $DEPLOY_MODE"
DEPLOY_DIR="/mnt/storage/traffic-monitor-deploy"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')

# Deployment defaults
DEPLOY_USER=${DEPLOY_USER:-merk}
STAGING_DIR=${STAGING_DIR:-/mnt/storage/deployment-staging}
CONTAINER_AUDIT_LOG=${CONTAINER_AUDIT_LOG:-/var/log/traffic_deploy_containers.log}

# Exit codes for different failure types
EXIT_PRECHECK_FAILED=10
EXIT_HOST_SERVICE_FAILED=20
EXIT_