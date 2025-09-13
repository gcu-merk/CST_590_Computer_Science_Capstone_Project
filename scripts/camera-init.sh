#!/bin/bash
# Camera Infrastructure Initialization Script
# Sets up directories, permissions, and services for Raspberry Pi camera capture system
# Run this script with: sudo bash scripts/camera-init.sh

set -e  # Exit on error

echo "🚗 Camera Infrastructure Initialization - $(date)"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BASE_DIR="/mnt/storage/camera_capture"
REQUIRED_DIRS=("live" "metadata" "periodic_snapshots" "processed" "backups" "logs")
USER="pi"
GROUP="pi"
LOG_FILE="/var/log/camera-init.log"

# Function to log messages
log_message() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

# Function to check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        echo -e "${RED}ERROR: This script must be run as root (use sudo)${NC}"
        echo "Usage: sudo bash scripts/camera-init.sh"
        exit 1
    fi
}

# Function to check if user exists
check_user() {
    if ! id "$USER" &>/dev/null; then
        echo -e "${RED}ERROR: User '$USER' does not exist${NC}"
        exit 1
    fi
    
    if ! getent group "$GROUP" &>/dev/null; then
        echo -e "${RED}ERROR: Group '$GROUP' does not exist${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ User and group validation passed${NC}"
}

# Function to check storage mount
check_storage_mount() {
    echo -e "\n${BLUE}Checking storage mount...${NC}"
    
    if [ ! -d "/mnt/storage" ]; then
        echo -e "${YELLOW}WARNING: /mnt/storage does not exist${NC}"
        echo "Creating /mnt/storage directory..."
        mkdir -p "/mnt/storage"
        chown "$USER:$GROUP" "/mnt/storage"
        chmod 755 "/mnt/storage"
        echo -e "${GREEN}✓ Created /mnt/storage${NC}"
    else
        echo -e "${GREEN}✓ /mnt/storage exists${NC}"
    fi
    
    # Check if it's actually a mount point
    if mountpoint -q "/mnt/storage" 2>/dev/null; then
        echo -e "${GREEN}✓ /mnt/storage is a mount point${NC}"
        mount | grep "/mnt/storage" | head -1
    else
        echo -e "${YELLOW}⚠ /mnt/storage is not a mount point (using as regular directory)${NC}"
    fi
}

# Function to create directory structure
create_directories() {
    echo -e "\n${BLUE}Creating camera directory structure...${NC}"
    
    # Create base directory
    if [ ! -d "$BASE_DIR" ]; then
        mkdir -p "$BASE_DIR"
        log_message "INFO" "Created base directory: $BASE_DIR"
    fi
    
    # Create all subdirectories
    for subdir in "${REQUIRED_DIRS[@]}"; do
        local full_path="$BASE_DIR/$subdir"
        if [ ! -d "$full_path" ]; then
            mkdir -p "$full_path"
            echo -e "  ${GREEN}✓ Created: $subdir${NC}"
            log_message "INFO" "Created directory: $full_path"
        else
            echo -e "  ${BLUE}• Exists: $subdir${NC}"
        fi
    done
}

# Function to set permissions
set_permissions() {
    echo -e "\n${BLUE}Setting directory permissions...${NC}"
    
    # Set ownership recursively
    chown -R "$USER:$GROUP" "$BASE_DIR"
    echo -e "  ${GREEN}✓ Set ownership to $USER:$GROUP${NC}"
    
    # Set permissions for maximum compatibility
    # Base directory: 755 (rwxr-xr-x)
    chmod 755 "$BASE_DIR"
    
    # Subdirectories: 777 (rwxrwxrwx) for Docker container compatibility
    for subdir in "${REQUIRED_DIRS[@]}"; do
        local full_path="$BASE_DIR/$subdir"
        chmod 777 "$full_path"
        echo -e "  ${GREEN}✓ Set permissions 777 for: $subdir${NC}"
    done
    
    log_message "INFO" "Permissions set for all directories"
}

# Function to test directory access
test_directory_access() {
    echo -e "\n${BLUE}Testing directory access...${NC}"
    
    local test_passed=true
    
    for subdir in "${REQUIRED_DIRS[@]}"; do
        local full_path="$BASE_DIR/$subdir"
        local test_file="$full_path/.init_test_$(date +%s)"
        
        # Test as root
        if touch "$test_file" 2>/dev/null; then
            rm -f "$test_file"
            echo -e "  ${GREEN}✓ Root write access: $subdir${NC}"
        else
            echo -e "  ${RED}✗ Root write access failed: $subdir${NC}"
            test_passed=false
        fi
        
        # Test as pi user
        if sudo -u "$USER" touch "$test_file" 2>/dev/null; then
            sudo -u "$USER" rm -f "$test_file"
            echo -e "  ${GREEN}✓ User ($USER) write access: $subdir${NC}"
        else
            echo -e "  ${RED}✗ User ($USER) write access failed: $subdir${NC}"
            test_passed=false
        fi
    done
    
    if [ "$test_passed" = true ]; then
        echo -e "\n${GREEN}✓ All directory access tests passed${NC}"
        return 0
    else
        echo -e "\n${RED}✗ Some directory access tests failed${NC}"
        return 1
    fi
}

# Function to create systemd service
create_systemd_service() {
    echo -e "\n${BLUE}Creating systemd service for camera capture...${NC}"
    
    local service_file="/etc/systemd/system/host-camera-capture.service"
    local script_path="$(pwd)/scripts/host-camera-capture.py"
    
    if [ ! -f "$script_path" ]; then
        echo -e "${YELLOW}⚠ Camera capture script not found at: $script_path${NC}"
        echo "  Service file will be created but may need path adjustment"
        script_path="/home/pi/camera-system/scripts/host-camera-capture.py"
    fi
    
    cat > "$service_file" << EOF
[Unit]
Description=Host Camera Capture Service
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
Restart=always
RestartSec=10
User=$USER
Group=$GROUP
WorkingDirectory=/home/$USER
ExecStart=/usr/bin/python3 $script_path --capture-dir $BASE_DIR --interval 1.0
StandardOutput=journal
StandardError=journal
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd and enable service
    systemctl daemon-reload
    systemctl enable host-camera-capture.service
    
    echo -e "  ${GREEN}✓ Created systemd service: $service_file${NC}"
    echo -e "  ${BLUE}• To start: sudo systemctl start host-camera-capture${NC}"
    echo -e "  ${BLUE}• To check status: sudo systemctl status host-camera-capture${NC}"
    
    log_message "INFO" "Created systemd service for camera capture"
}

# Function to install dependencies
install_dependencies() {
    echo -e "\n${BLUE}Checking Python dependencies...${NC}"
    
    # Check if pip is available
    if ! command -v pip3 &> /dev/null; then
        echo -e "${YELLOW}⚠ pip3 not found, installing...${NC}"
        apt-get update
        apt-get install -y python3-pip
    fi
    
    # Install required Python packages
    local packages=("opencv-python" "numpy" "Pillow")
    for package in "${packages[@]}"; do
        if sudo -u "$USER" python3 -c "import ${package//-/_}" 2>/dev/null; then
            echo -e "  ${GREEN}✓ $package already installed${NC}"
        else
            echo -e "  ${YELLOW}Installing $package...${NC}"
            sudo -u "$USER" pip3 install "$package"
        fi
    done
}

# Function to display summary
display_summary() {
    echo -e "\n${YELLOW}📋 INITIALIZATION SUMMARY${NC}"
    echo "=========================================="
    
    echo -e "📁 Directory Structure:"
    ls -la "$BASE_DIR"
    
    echo -e "\n🔧 Disk Usage:"
    du -sh "$BASE_DIR"
    
    echo -e "\n🐳 Docker Integration:"
    echo "  Volume mount: $BASE_DIR:/app/data/camera_capture"
    
    echo -e "\n🚀 Next Steps:"
    echo "  1. Test camera: rpicam-hello -t 5s"
    echo "  2. Start capture service: sudo systemctl start host-camera-capture"
    echo "  3. Start Docker containers: docker-compose up -d"
    echo "  4. Test API: curl http://localhost:5000/api/weather"
    echo "  5. Run full test: bash test_complete_camera_pipeline.sh"
    
    log_message "INFO" "Camera infrastructure initialization completed successfully"
}

# Main execution
main() {
    echo -e "${BLUE}Starting camera infrastructure initialization...${NC}"
    
    # Initialize log file
    touch "$LOG_FILE"
    chmod 644 "$LOG_FILE"
    log_message "INFO" "Camera infrastructure initialization started"
    
    # Run all initialization steps
    check_root
    check_user
    check_storage_mount
    create_directories
    set_permissions
    
    if test_directory_access; then
        install_dependencies
        create_systemd_service
        display_summary
        echo -e "\n${GREEN}🎉 Camera infrastructure initialization completed successfully!${NC}"
        exit 0
    else
        echo -e "\n${RED}❌ Camera infrastructure initialization failed!${NC}"
        echo -e "${RED}Check the log file: $LOG_FILE${NC}"
        exit 1
    fi
}

# Handle script interruption
trap 'echo -e "\n${YELLOW}Initialization interrupted${NC}"; exit 1' INT TERM

# Run main function
main "$@"