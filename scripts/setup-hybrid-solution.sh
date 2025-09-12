#!/bin/bash
# Setup script for Traffic Monitoring Hybrid Solution
# Run this script on the Raspberry Pi to set up the complete system

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Configuration
PROJECT_DIR="/home/merk/CST_590_Computer_Science_Capstone_Project"
STORAGE_DIR="/mnt/storage"
SCRIPTS_DIR="$PROJECT_DIR/scripts"

log_info "=== Traffic Monitoring Hybrid Solution Setup ==="

# Step 1: Check system requirements
log_info "Checking system requirements..."

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    log_warning "This doesn't appear to be a Raspberry Pi"
fi

# Check for required commands
for cmd in docker docker-compose rpicam-still git; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        log_error "Required command not found: $cmd"
        case $cmd in
            "rpicam-apps"|"rpicam-still")
                echo "Install with: sudo apt update && sudo apt install -y rpicam-apps"
                ;;
            "docker")
                echo "Install Docker following Raspberry Pi documentation"
                ;;
            "docker-compose")
                echo "Install with: sudo apt install -y docker-compose"
                ;;
        esac
        exit 1
    fi
done

log_success "System requirements check passed"

# Step 2: Create storage directories
log_info "Setting up storage directories..."

sudo mkdir -p "$STORAGE_DIR"
sudo chown $(whoami):$(whoami) "$STORAGE_DIR"
mkdir -p "$STORAGE_DIR/periodic_snapshots"
mkdir -p "$STORAGE_DIR/processed"

log_success "Storage directories created"

# Step 3: Make scripts executable
log_info "Setting up scripts..."

chmod +x "$SCRIPTS_DIR/capture-and-process.sh"
chmod +x "$SCRIPTS_DIR/process_traffic.py"

# Create symlink for easy access
sudo ln -sf "$SCRIPTS_DIR/capture-and-process.sh" /usr/local/bin/capture-traffic
log_success "Scripts configured"

# Step 4: Test camera functionality
log_info "Testing camera functionality..."

if rpicam-still -o /tmp/camera_test.jpg --immediate --timeout 5000 2>/dev/null; then
    if [[ -f /tmp/camera_test.jpg ]] && [[ $(stat -c%s /tmp/camera_test.jpg) -gt 50000 ]]; then
        log_success "Camera test passed"
        rm -f /tmp/camera_test.jpg
    else
        log_error "Camera test failed - image too small or missing"
        exit 1
    fi
else
    log_error "Camera test failed - rpicam-still command failed"
    exit 1
fi

# Step 5: Test Docker container
log_info "Testing Docker container..."

if ! docker ps --format "table {{.Names}}" | grep -q "traffic-monitoring-edge"; then
    log_info "Starting Docker container..."
    cd "$PROJECT_DIR"
    docker-compose up -d
    sleep 10
fi

# Test container access to storage
if docker exec traffic-monitoring-edge test -d /mnt/storage; then
    log_success "Container can access storage directory"
else
    log_error "Container cannot access storage directory"
    log_info "Check docker-compose.yml volume mounts"
    exit 1
fi

# Step 6: Run initial test
log_info "Running initial capture and process test..."

if "$SCRIPTS_DIR/capture-and-process.sh" test; then
    log_success "Initial test passed"
else
    log_error "Initial test failed"
    exit 1
fi

# Step 7: Install systemd services (optional)
log_info "Installing systemd services for automated operation..."

read -p "Install systemd timer for automatic captures every 5 minutes? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Update service file with correct paths
    sed "s|/home/merk/CST_590_Computer_Science_Capstone_Project|$PROJECT_DIR|g" \
        "$SCRIPTS_DIR/traffic-monitoring.service" | sudo tee /etc/systemd/system/traffic-monitoring.service > /dev/null
    
    sudo cp "$SCRIPTS_DIR/traffic-monitoring.timer" /etc/systemd/system/
    
    sudo systemctl daemon-reload
    sudo systemctl enable traffic-monitoring.timer
    sudo systemctl start traffic-monitoring.timer
    
    log_success "Systemd timer installed and started"
    log_info "Check status with: sudo systemctl status traffic-monitoring.timer"
    log_info "View logs with: sudo journalctl -u traffic-monitoring.service -f"
else
    log_info "Systemd timer not installed. You can run captures manually with:"
    log_info "  capture-traffic"
fi

# Step 8: Final summary
log_success "=== Setup Complete! ==="
echo
echo "📸 Hybrid Solution Ready:"
echo "  • Host capture: rpicam-still (native performance)"
echo "  • Container processing: Docker-based ML pipeline"
echo "  • Storage: $STORAGE_DIR"
echo
echo "🚀 Usage:"
echo "  Manual capture:    capture-traffic"
echo "  Test mode:         capture-traffic test"
echo "  Capture only:      capture-traffic capture-only"
echo "  Cleanup old files: capture-traffic cleanup"
echo
echo "📊 Monitor:"
echo "  Container logs:    docker logs traffic-monitoring-edge -f"
echo "  Service status:    sudo systemctl status traffic-monitoring.timer"
echo "  Service logs:      sudo journalctl -u traffic-monitoring.service -f"
echo "  Storage usage:     du -sh $STORAGE_DIR"
echo
echo "📁 Files:"
echo "  Snapshots:         $STORAGE_DIR/periodic_snapshots/"
echo "  Processed images:  $STORAGE_DIR/processed/"
echo
log_success "Traffic monitoring system is operational!"
