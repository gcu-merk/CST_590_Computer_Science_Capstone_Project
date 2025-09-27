#!/bin/bash
# IMX500 AI Architecture Quick Deployment Validator
# Validates that the IMX500 AI implementation is ready for deployment

echo "🚗 IMX500 AI Architecture Deployment Validator"
echo "=============================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
    ((PASSED_TESTS++))
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

test_item() {
    ((TOTAL_TESTS++))
    echo -n "  Testing $1... "
}

test_pass() {
    echo -e "${GREEN}✅ PASS${NC}"
    ((PASSED_TESTS++))
}

test_fail() {
    echo -e "${RED}❌ FAIL${NC}"
}

# Test 1: Check if we're on Raspberry Pi
echo
log_info "Checking system compatibility..."
test_item "Raspberry Pi detection"
if [ -f /proc/device-tree/model ] && grep -q "Raspberry Pi" /proc/device-tree/model; then
    test_pass
else
    test_fail
    log_error "This system is not a Raspberry Pi. IMX500 AI requires Pi 5 with AI Kit."
fi

# Test 2: Check IMX500 model file
test_item "IMX500 model file"
if [ -f "/usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk" ]; then
    test_pass
else
    test_fail
    log_error "IMX500 model file not found. Install AI Kit software."
fi

# Test 3: Check Python dependencies
test_item "Python picamera2 library"
if python3 -c "import picamera2; from picamera2.devices.imx500 import IMX500" 2>/dev/null; then
    test_pass
else
    test_fail
    log_error "picamera2 with IMX500 support not available."
fi

# Test 4: Check Redis availability
test_item "Redis connection"
if command -v redis-cli >/dev/null 2>&1; then
    if redis-cli ping >/dev/null 2>&1; then
        test_pass
    else
        test_fail
        log_error "Redis server is not running."
    fi
else
    test_fail
    log_error "Redis CLI not available."
fi

# Test 5: Check Docker
test_item "Docker availability"
if command -v docker >/dev/null 2>&1; then
    if docker ps >/dev/null 2>&1; then
        test_pass
    else
        test_fail
        log_error "Docker is not running or user lacks permissions."
    fi
else
    test_fail
    log_error "Docker is not installed."
fi

# Test 6: Check storage directories
echo
log_info "Checking storage setup..."
test_item "Storage directories"
STORAGE_OK=true
for dir in "/mnt/storage/camera_capture/live" "/mnt/storage/camera_capture/ai_results" "/mnt/storage/camera_capture/metadata"; do
    if [ ! -d "$dir" ]; then
        STORAGE_OK=false
        break
    fi
done

if [ "$STORAGE_OK" = true ]; then
    test_pass
else
    test_fail
    log_error "Storage directories not set up. Run storage setup first."
fi

# Test 7: Check implementation files
echo
log_info "Checking implementation files..."
test_item "IMX500 AI host service"
if [ -f "scripts/imx500_ai_host_capture.py" ]; then
    test_pass
else
    test_fail
    log_error "IMX500 AI host service file missing."
fi

test_item "Vehicle consolidator service"
if [ -f "edge_processing/vehicle_detection/vehicle_consolidator_service.py" ]; then
    test_pass
else
    test_fail
    log_error "Vehicle consolidator service file missing."
fi

test_item "Systemd service file"
if [ -f "deployment/imx500-ai-capture.service" ]; then
    test_pass
else
    test_fail
    log_error "Systemd service file missing."
fi

test_item "Deployment script"
if [ -f "deployment/deploy-imx500-ai-service.sh" ] && [ -x "deployment/deploy-imx500-ai-service.sh" ]; then
    test_pass
else
    test_fail
    log_error "Deployment script missing or not executable."
fi

# Test 8: Check docker-compose configuration
test_item "Docker compose configuration"
if [ -f "docker-compose.yml" ] && grep -q "vehicle-consolidator" docker-compose.yml; then
    test_pass
else
    test_fail
    log_error "Docker compose not configured for vehicle consolidator."
fi

# Test 9: Check for conflicting services
echo
log_info "Checking for conflicts..."
test_item "No conflicting services"
if systemctl is-active --quiet host-camera-capture 2>/dev/null; then
    test_fail
    log_warning "host-camera-capture service is running. This will conflict with IMX500 AI service."
    log_info "Run: sudo systemctl stop host-camera-capture && sudo systemctl disable host-camera-capture"
else
    test_pass
fi

# Generate summary
echo
echo "📋 Deployment Readiness Summary"
echo "================================"
echo "Tests Passed: $PASSED_TESTS/$TOTAL_TESTS"

if [ $PASSED_TESTS -eq $TOTAL_TESTS ]; then
    log_success "🎉 System is ready for IMX500 AI deployment!"
    echo
    echo "Next steps:"
    echo "1. Deploy: sudo ./deployment/deploy-imx500-ai-service.sh"
    echo "2. Test:   python3 test_imx500_ai_implementation.py"
    echo "3. Monitor: sudo journalctl -u imx500-ai-capture -f"
    echo
    echo "Expected benefits:"
    echo "  ✅ Sub-100ms vehicle detection (vs seconds with software AI)"
    echo "  ✅ ~100% CPU usage reduction for AI processing"
    echo "  ✅ Real-time processing capability"
    echo "  ✅ Hardware-accelerated edge AI"
    exit 0
else
    FAILED=$((TOTAL_TESTS - PASSED_TESTS))
    log_error "❌ $FAILED tests failed. Address issues before deployment."
    echo
    echo "Common fixes:"
    echo "1. Install AI Kit: sudo apt update && sudo apt install imx500-all"
    echo "2. Setup storage: sudo mkdir -p /mnt/storage/camera_capture/{live,ai_results,metadata}"
    echo "3. Start Redis: sudo systemctl start redis-server"
    echo "4. Start Docker: sudo systemctl start docker"
    echo "5. Add user to docker group: sudo usermod -aG docker \$USER"
    exit 1
fi