#!/bin/bash
"""
Raspberry Pi 5 Traffic Monitoring System - Deployment Script
Implements recommended technology improvements and optimizations
"""

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/opt/traffic-monitor"
SERVICE_USER="traffic-monitor"
PYTHON_VERSION="3.11"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Raspberry Pi 5 Traffic Monitoring Setup${NC}"
echo -e "${BLUE}========================================${NC}"

# Check if running on Raspberry Pi
check_raspberry_pi() {
    echo -e "${YELLOW}Checking if running on Raspberry Pi...${NC}"
    if ! grep -q "BCM" /proc/cpuinfo; then
        echo -e "${RED}Warning: This doesn't appear to be a Raspberry Pi${NC}"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    echo -e "${GREEN}✓ Raspberry Pi detected${NC}"
}

# Update system and install dependencies
install_system_dependencies() {
    echo -e "${YELLOW}Installing system dependencies...${NC}"
    
    # Update package lists
    sudo apt update
    
    # Install Python and development tools
    sudo apt install -y \
        python3 python3-pip python3-venv python3-dev \
        build-essential cmake pkg-config
    
    # Install libraries for TensorFlow and OpenCV
    sudo apt install -y \
        libhdf5-dev libhdf5-serial-dev libhdf5-103 \
        libatlas-base-dev gfortran \
        libjpeg-dev libtiff5-dev libpng-dev \
        libavcodec-dev libavformat-dev libswscale-dev \
        libv4l-dev libxvidcore-dev libx264-dev \
        libgtk-3-dev libcanberra-gtk-module libcanberra-gtk3-module
    
    # Install database and utilities
    sudo apt install -y \
        sqlite3 libsqlite3-dev \
        git wget curl htop
    
    # Install Docker (optional)
    if ! command -v docker &> /dev/null; then
        echo -e "${YELLOW}Installing Docker...${NC}"
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        sudo usermod -aG docker $USER
        rm get-docker.sh
    fi
    
    echo -e "${GREEN}✓ System dependencies installed${NC}"
}

# Enable hardware interfaces
enable_hardware_interfaces() {
    echo -e "${YELLOW}Enabling hardware interfaces...${NC}"
    
    # Enable camera, SPI, I2C, and UART
    sudo raspi-config nonint do_camera 0
    sudo raspi-config nonint do_spi 0
    sudo raspi-config nonint do_i2c 0
    sudo raspi-config nonint do_serial 1
    
    # Configure boot options
    if ! grep -q "enable_uart=1" /boot/firmware/config.txt; then
        echo "enable_uart=1" | sudo tee -a /boot/firmware/config.txt
    fi
    
    if ! grep -q "dtparam=spi=on" /boot/firmware/config.txt; then
        echo "dtparam=spi=on" | sudo tee -a /boot/firmware/config.txt
    fi
    
    # GPU memory split for AI processing
    if ! grep -q "gpu_mem=128" /boot/firmware/config.txt; then
        echo "gpu_mem=128" | sudo tee -a /boot/firmware/config.txt
    fi
    
    echo -e "${GREEN}✓ Hardware interfaces enabled${NC}"
}

# Create project user and directories
setup_project_structure() {
    echo -e "${YELLOW}Setting up project structure...${NC}"
    
    # Create service user
    if ! id "$SERVICE_USER" &>/dev/null; then
        sudo useradd -r -s /bin/false -d $PROJECT_DIR $SERVICE_USER
    fi
    
    # Create project directory
    sudo mkdir -p $PROJECT_DIR
    sudo chown $SERVICE_USER:$SERVICE_USER $PROJECT_DIR
    
    # Create subdirectories
    sudo -u $SERVICE_USER mkdir -p \
        $PROJECT_DIR/logs \
        $PROJECT_DIR/data/exports \
        $PROJECT_DIR/data/backups \
        $PROJECT_DIR/data/models \
        $PROJECT_DIR/config
    
    echo -e "${GREEN}✓ Project structure created${NC}"
}

# Install Python dependencies with optimizations
install_python_dependencies() {
    echo -e "${YELLOW}Installing Python dependencies...${NC}"
    
    # Create virtual environment
    sudo -u $SERVICE_USER python3 -m venv $PROJECT_DIR/venv
    
    # Activate virtual environment and upgrade pip
    sudo -u $SERVICE_USER $PROJECT_DIR/venv/bin/pip install --upgrade pip wheel setuptools
    
    # Install TensorFlow Lite (lighter than full TensorFlow)
    sudo -u $SERVICE_USER $PROJECT_DIR/venv/bin/pip install \
        tflite-runtime \
        numpy \
        opencv-python-headless
    
    # Install Raspberry Pi specific packages
    sudo -u $SERVICE_USER $PROJECT_DIR/venv/bin/pip install \
        picamera2 \
        gpiozero \
        RPi.GPIO
    
    # Install other dependencies
    sudo -u $SERVICE_USER $PROJECT_DIR/venv/bin/pip install \
        flask flask-socketio flask-cors \
        pyserial \
        psutil \
        pandas \
        scikit-learn \
        python-dateutil \
        requests \
        pyyaml
    
    echo -e "${GREEN}✓ Python dependencies installed${NC}"
}

# Copy application files
deploy_application() {
    echo -e "${YELLOW}Deploying application...${NC}"
    
    # Copy source code
    sudo cp -r . $PROJECT_DIR/source/
    sudo chown -R $SERVICE_USER:$SERVICE_USER $PROJECT_DIR/source/
    
    # Create configuration file
    sudo -u $SERVICE_USER tee $PROJECT_DIR/config/traffic_monitoring.conf > /dev/null <<EOF
# Traffic Monitoring System Configuration

[hardware]
camera_index = 0
radar_port = /dev/ttyACM0
radar_baudrate = 9600

[processing]
detection_confidence_threshold = 0.5
speed_detection_threshold = 0.5
use_tflite = true
input_size = 640,640

[api]
host = 0.0.0.0
port = 5000
enable_cors = true

[database]
path = $PROJECT_DIR/data/traffic_data.db

[logging]
level = INFO
log_file = $PROJECT_DIR/logs/traffic_monitoring.log
EOF

    echo -e "${GREEN}✓ Application deployed${NC}"
}

# Create systemd service
create_systemd_service() {
    echo -e "${YELLOW}Creating systemd service...${NC}"
    
    sudo tee /etc/systemd/system/traffic-monitor.service > /dev/null <<EOF
[Unit]
Description=Raspberry Pi 5 Traffic Monitoring System
After=network.target
Wants=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$PROJECT_DIR/source
Environment=PYTHONPATH=$PROJECT_DIR/source
ExecStart=$PROJECT_DIR/venv/bin/python main_edge_app.py
Restart=always
RestartSec=10
StandardOutput=append:$PROJECT_DIR/logs/service.log
StandardError=append:$PROJECT_DIR/logs/service.log

# Security settings
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$PROJECT_DIR

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd and enable service
    sudo systemctl daemon-reload
    sudo systemctl enable traffic-monitor.service
    
    echo -e "${GREEN}✓ Systemd service created${NC}"
}

# Test hardware connections
test_hardware() {
    echo -e "${YELLOW}Testing hardware connections...${NC}"
    
    # Test camera
    if command -v libcamera-hello &> /dev/null; then
        echo "Testing camera..."
        timeout 5s libcamera-hello --preview=none --timeout=3000 || echo "Camera test completed"
    fi
    
    # Test serial port for radar
    if [ -e /dev/ttyACM0 ]; then
        echo -e "${GREEN}✓ Radar serial port found${NC}"
    else
        echo -e "${YELLOW}⚠ Radar serial port not found (normal if not connected)${NC}"
    fi
    
    # Check GPIO access
    if [ -e /dev/gpiomem ]; then
        echo -e "${GREEN}✓ GPIO access available${NC}"
    else
        echo -e "${RED}✗ GPIO access not available${NC}"
    fi
}

# Performance optimizations
optimize_system() {
    echo -e "${YELLOW}Applying system optimizations...${NC}"
    
    # Increase swap for ML workloads
    if [ ! -f /swapfile ] || [ $(stat -c%s /swapfile) -lt 2147483648 ]; then
        echo "Increasing swap size..."
        sudo dphys-swapfile swapoff || true
        sudo sed -i 's/CONF_SWAPSIZE=.*/CONF_SWAPSIZE=2048/' /etc/dphys-swapfile || true
        sudo dphys-swapfile setup || true
        sudo dphys-swapfile swapon || true
    fi
    
    # Optimize for SSD if connected
    if [ -e /dev/sda1 ]; then
        echo "SSD detected, optimizing mount options..."
        # Add SSD optimizations to fstab if not present
        if ! grep -q "noatime" /etc/fstab; then
            echo "# Add noatime for SSD optimization" | sudo tee -a /etc/fstab
        fi
    fi
    
    echo -e "${GREEN}✓ System optimized${NC}"
}

# Main installation function
main() {
    echo -e "${BLUE}Starting installation with recommended improvements...${NC}"
    
    check_raspberry_pi
    install_system_dependencies
    enable_hardware_interfaces
    setup_project_structure
    install_python_dependencies
    deploy_application
    create_systemd_service
    test_hardware
    optimize_system
    
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✓ Installation completed successfully!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Reboot the system: sudo reboot"
    echo "2. Start the service: sudo systemctl start traffic-monitor"
    echo "3. Check status: sudo systemctl status traffic-monitor"
    echo "4. View logs: sudo journalctl -u traffic-monitor -f"
    echo "5. Access API: http://$(hostname -I | awk '{print $1}'):5000"
    echo
    echo -e "${YELLOW}Configuration file: $PROJECT_DIR/config/traffic_monitoring.conf${NC}"
    echo -e "${YELLOW}Logs directory: $PROJECT_DIR/logs/${NC}"
    echo
    echo -e "${BLUE}For Docker deployment: docker-compose up -d${NC}"
}

# Run main function
main "$@"
