#!/bin/bash
# IMX500 AI Host Service Deployment Script
# Deploys the new IMX500 AI-enabled host camera capture service

set -e

echo "🚗 IMX500 AI Host Service Deployment"
echo "====================================="

# Configuration
SERVICE_NAME="imx500-ai-capture"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
SCRIPT_PATH="/home/merk/traffic-monitor-deploy/scripts/imx500_ai_host_capture.py"
DEPLOYMENT_DIR="/home/merk/traffic-monitor-deploy"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    log_error "This script must be run on a Raspberry Pi"
    exit 1
fi

# Check if running as root (needed for systemd service installation)
if [[ $EUID -ne 0 ]]; then
    log_error "This script must be run as root (use sudo)"
    exit 1
fi

log_info "Checking system requirements..."

# Check for IMX500 model files
IMX500_MODEL="/usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk"
if [[ ! -f "$IMX500_MODEL" ]]; then
    log_error "IMX500 model file not found: $IMX500_MODEL"
    log_info "Install with: sudo apt install imx500-all"
    exit 1
fi
log_success "IMX500 model file found"

# Check for picamera2
if ! python3 -c "import picamera2" 2>/dev/null; then
    log_error "picamera2 not available"
    log_info "Install with: sudo apt install python3-picamera2"
    exit 1
fi
log_success "picamera2 available"

# Check for redis-py
if ! python3 -c "import redis" 2>/dev/null; then
    log_warning "redis-py not available, installing..."
    pip3 install redis
fi
log_success "Redis Python client available"

# Check deployment directory
if [[ ! -d "$DEPLOYMENT_DIR" ]]; then
    log_error "Deployment directory not found: $DEPLOYMENT_DIR"
    exit 1
fi
log_success "Deployment directory found"

# Check script file
if [[ ! -f "$SCRIPT_PATH" ]]; then
    log_error "IMX500 AI script not found: $SCRIPT_PATH"
    exit 1
fi
log_success "IMX500 AI script found"

# Make script executable
chmod +x "$SCRIPT_PATH"
chown merk:merk "$SCRIPT_PATH"

# Create storage directories
log_info "Creating storage directories..."
mkdir -p /mnt/storage/camera_capture/{live,ai_results,metadata}
chown -R merk:merk /mnt/storage/camera_capture
log_success "Storage directories created"

# Stop old host camera service if it exists
OLD_SERVICE="host-camera-capture"
if systemctl list-units --full -all | grep -q "$OLD_SERVICE.service"; then
    log_info "Stopping old host camera service..."
    systemctl stop "$OLD_SERVICE" || true
    systemctl disable "$OLD_SERVICE" || true
    log_success "Old service stopped"
fi

# Install systemd service
log_info "Installing IMX500 AI service..."
cp "$DEPLOYMENT_DIR/deployment/${SERVICE_NAME}.service" "$SERVICE_FILE"

# Reload systemd and enable service
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
log_success "Service installed and enabled"

# Start the service
log_info "Starting IMX500 AI service..."
systemctl start "$SERVICE_NAME"

# Wait a moment for startup
sleep 3

# Check service status
if systemctl is-active --quiet "$SERVICE_NAME"; then
    log_success "IMX500 AI service is running"
    
    # Show service status
    echo ""
    systemctl status "$SERVICE_NAME" --no-pager -l
    
    echo ""
    log_info "Service logs (last 10 lines):"
    journalctl -u "$SERVICE_NAME" -n 10 --no-pager
    
else
    log_error "IMX500 AI service failed to start"
    echo ""
    log_info "Service status:"
    systemctl status "$SERVICE_NAME" --no-pager -l
    echo ""
    log_info "Recent logs:"
    journalctl -u "$SERVICE_NAME" -n 20 --no-pager
    exit 1
fi

echo ""
log_success "✅ IMX500 AI Host Service deployment complete!"
echo ""
echo "Service Management Commands:"
echo "  Status:  sudo systemctl status $SERVICE_NAME"
echo "  Start:   sudo systemctl start $SERVICE_NAME"
echo "  Stop:    sudo systemctl stop $SERVICE_NAME"
echo "  Restart: sudo systemctl restart $SERVICE_NAME"
echo "  Logs:    sudo journalctl -u $SERVICE_NAME -f"
echo ""
echo "Configuration:"
echo "  Script:  $SCRIPT_PATH"
echo "  Service: $SERVICE_FILE"
echo "  Storage: /mnt/storage/camera_capture/"
echo "  Model:   $IMX500_MODEL"
echo ""
echo "The IMX500 AI service will now:"
echo "  ✅ Capture 4K images using on-chip AI vehicle detection"
echo "  ✅ Provide sub-100ms inference with zero CPU usage"
echo "  ✅ Publish results to Redis for Docker container consumption"
echo "  ✅ Store images and AI metadata in shared volume"
echo ""
echo "Next steps:"
echo "  1. Monitor logs: sudo journalctl -u $SERVICE_NAME -f"
echo "  2. Check Redis data: redis-cli keys 'vehicle:detection:*'"
echo "  3. Verify Docker containers consume the AI results"