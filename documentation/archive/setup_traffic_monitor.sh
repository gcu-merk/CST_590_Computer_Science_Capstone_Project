#!/bin/bash
set -e

########################################################
# Traffic Monitoring System – Complete Setup Script
#
# This script performs two main functions:
# 1. Updates your Raspberry Pi environment by installing
#    required OS packages, enabling required interfaces,
#    and setting up a Python virtual environment.
#
# 2. Creates the full project scaffolding for the Traffic
#    Monitoring System including directories, placeholder
#    files (config, src, tests, scripts, docs, and systemd).
########################################################

#############################
# Part 1: Environment Setup #
#############################

echo "=========================================="
echo " Traffic Monitoring System – Environment Setup"
echo "=========================================="

# 1. Update and upgrade OS packages from repositories
echo "Updating system packages..."
sudo apt update && sudo apt full-upgrade -y
sudo apt autoremove -y

# 2. Enable Raspberry Pi camera, SPI, I2C and set GPU memory split
echo "Enabling camera, SPI, I2C interfaces and setting GPU memory..."
sudo raspi-config nonint do_camera 1
sudo raspi-config nonint do_spi 1
sudo raspi-config nonint do_i2c 1
sudo raspi-config nonint do_memory_split 128

# 3. Install required system dependencies
echo "Installing system dependencies..."
sudo apt install -y python3-venv python3-pip \
    libcamera-apps libcamera-dev python3-picamera2 python3-libcamera \
    libopencv-dev python3-opencv libatlas-base-dev libhdf5-dev libjpeg-dev libtiff5-dev libpng-dev \
    python3-serial python3-spidev python3-smbus python3-rpi.gpio python3-gpiozero \
    python3-flask python3-requests mosquitto mosquitto-clients \
    git vim htop tree curl wget build-essential cmake pkg-config iotop nethogs

# 4. Create the project directory (~/"traffic_monitor") and change to it
echo "Creating project directory ~/traffic_monitor if it doesn't exist..."
mkdir -p ~/traffic_monitor
cd ~/traffic_monitor

# 5. Setup Python virtual environment if not already created
if [ ! -d "venv" ]; then
    echo "Setting up Python virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip setuptools wheel
else
    echo "Virtual environment already exists. Activating..."
    source venv/bin/activate
fi

# (Optional) You can install any base Python packages now if desired.
echo "Base environment setup complete."
echo ""

###############################################
# Part 2: Project Structure & Placeholder Files
###############################################

# Define some color codes for output messaging
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'  # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on a Raspberry Pi (checks /proc/cpuinfo for "Raspberry Pi")
check_raspberry_pi() {
    if [[ ! -f /proc/cpuinfo ]] || ! grep -q "Raspberry Pi" /proc/cpuinfo; then
        print_warning "This script is designed for Raspberry Pi but will continue anyway"
    else
        print_success "Running on Raspberry Pi - proceeding with setup"
    fi
}

# Create the complete directory structure for the project
create_directories() {
    print_status "Creating traffic monitor directory structure..."
    
    # If you're already in the project root (named "traffic_monitor")
    if [[ $(basename "$PWD") == "traffic_monitor" ]]; then
        print_status "Already in traffic_monitor directory, creating structure here..."
    else
        mkdir -p traffic_monitor
        cd traffic_monitor
    fi
    
    # Root level directories and subdirectories
    mkdir -p config
    mkdir -p src/{core,hardware,detection,data,monitoring,services,api,utils}
    mkdir -p tests/{unit,integration,fixtures}
    mkdir -p scripts
    mkdir -p data/{models,logs,cache}
    mkdir -p docs
    mkdir -p systemd

    # Further organization
    mkdir -p src/hardware/{camera,radar}
    mkdir -p src/detection/{models,tracking}
    mkdir -p src/api/routes
    
    print_success "Directory structure created successfully"
}

# Create placeholder files for README, requirements, setup, configuration, source code, tests, scripts, documentation, and systemd service
create_files() {
    print_status "Creating placeholder files..."
    
    # README file
    cat > README.md << 'EOF'
# Traffic Monitor System

A comprehensive traffic monitoring system for Raspberry Pi 5 using AI cameras and radar sensors.

## Features
- Multi-sensor data fusion (camera + radar)
- Real-time vehicle detection and tracking
- Speed measurement and traffic analysis
- RESTful API and WebSocket support
- System health monitoring

## Installation
Run the setup script: `./scripts/install.sh`

## Usage
Start monitoring: `python scripts/start_monitoring.py`

## Documentation
See the `docs/` directory for detailed documentation.
EOF

    # requirements file
    cat > requirements.txt << 'EOF'
# Core dependencies (compatible with your existing setup)
numpy>=2.1.0
opencv-python>=4.11.0
tensorflow>=2.19.0
flask>=2.0.0
flask-socketio>=5.0.0
requests>=2.25.0
pyyaml>=6.0
pyserial>=3.5

# Hardware interfaces
picamera2>=0.3.0
RPi.GPIO>=0.7.0

# Data processing
pandas>=1.3.0
scipy>=1.7.0

# Monitoring and logging
psutil>=5.8.0
prometheus-client>=0.12.0

# Testing
pytest>=6.2.0
pytest-cov>=3.0.0
mock>=4.0.0

# Additional dependencies for traffic monitoring
scikit-learn>=1.0.0
matplotlib>=3.5.0
pillow>=8.0.0
imutils>=0.5.4
filterpy>=1.4.5
EOF

    # setup.py for packaging
    cat > setup.py << 'EOF'
from setuptools import setup, find_packages

setup(
    name="traffic-monitor",
    version="1.0.0",
    description="Traffic monitoring system for Raspberry Pi",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.21.0",
        "opencv-python>=4.5.0",
        "tensorflow>=2.8.0",
        "flask>=2.0.0",
        "flask-socketio>=5.0.0",
        "pyyaml>=6.0",
        "pyserial>=3.5",
        "picamera2>=0.3.0",
        "RPi.GPIO>=0.7.0",
        "pandas>=1.3.0",
        "scipy>=1.7.0",
        "psutil>=5.8.0",
    ],
    entry_points={
        "console_scripts": [
            "traffic-monitor=src.main:main",
        ],
    },
)
EOF

    # Configuration settings and logging
    cat > config/settings.py << 'EOF'
"""Configuration settings for traffic monitor system."""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = DATA_DIR / "logs"
MODELS_DIR = DATA_DIR / "models"

# Hardware configuration
CAMERA_ENABLED = True
RADAR_ENABLED = True
CAMERA_RESOLUTION = (1920, 1080)
CAMERA_FPS = 30

# Detection settings
DETECTION_CONFIDENCE_THRESHOLD = 0.5
TRACKING_MAX_DISAPPEARED = 30
SPEED_CALCULATION_DISTANCE = 10.0  # meters

# API settings
API_HOST = "0.0.0.0"
API_PORT = 5000
WEBSOCKET_ENABLED = True

# Monitoring
HEALTH_CHECK_INTERVAL = 30  # seconds
METRICS_COLLECTION_INTERVAL = 60  # seconds
EOF

    cat > config/logging.yaml << 'EOF'
version: 1
formatters:
  default:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    datefmt: '%Y-%m-%d %H:%M:%S'
  detailed:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    datefmt: '%Y-%m-%d %H:%M:%S'

handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: default
    stream: ext://sys.stdout
  file:
    class: logging.handlers.RotatingFileHandler
    level: DEBUG
    formatter: detailed
    filename: data/logs/traffic_monitor.log
    maxBytes: 10485760
    backupCount: 5

loggers:
  traffic_monitor:
    level: DEBUG
    handlers: [console, file]
    propagate: false

root:
  level: INFO
  handlers: [console]
EOF

    cat > config/hardware_config.yaml << 'EOF'
camera:
  type: "ai_camera"
  device_id: 0
  resolution: [1920, 1080]
  fps: 30
  auto_exposure: true
  
radar:
  type: "ops243c"
  port: "/dev/ttyUSB0"
  baudrate: 9600
  timeout: 1.0
  
sensors:
  distance_between: 10.0
  calibration_required: true
EOF

    # Create placeholder __init__.py and core modules
    touch src/__init__.py
    cat > src/core/__init__.py << 'EOF'
"""Core module for traffic monitor system."""
EOF

    cat > src/core/base.py << 'EOF'
"""Base classes for the traffic monitor system."""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
class BaseComponent(ABC):
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}
        self._initialized = False
        self._running = False
    @abstractmethod
    def initialize(self) -> bool:
        pass
    @abstractmethod
    def start(self) -> bool:
        pass
    @abstractmethod
    def stop(self) -> bool:
        pass
    @property
    def is_running(self) -> bool:
        return self._running
    @property
    def is_initialized(self) -> bool:
        return self._initialized
EOF

    cat > src/core/exceptions.py << 'EOF'
"""Custom exceptions for traffic monitor system."""
class TrafficMonitorError(Exception):
    pass
class HardwareError(TrafficMonitorError):
    pass
class DetectionError(TrafficMonitorError):
    pass
class ConfigurationError(TrafficMonitorError):
    pass
class APIError(TrafficMonitorError):
    pass
EOF

    cat > src/core/interfaces.py << 'EOF'
"""Interface definitions for the traffic monitor system."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
@dataclass
class DetectionResult:
    object_id: str
    class_name: str
    confidence: float
    bbox: Tuple[int, int, int, int]
    timestamp: datetime
    speed: Optional[float] = None
@dataclass
class SensorData:
    sensor_type: str
    timestamp: datetime
    data: Dict[str, Any]
class ISensor(ABC):
    @abstractmethod
    def read_data(self) -> Optional[SensorData]:
        pass
    @abstractmethod
    def is_connected(self) -> bool:
        pass
class IDetector(ABC):
    @abstractmethod
    def detect(self, frame: Any) -> List[DetectionResult]:
        pass
    @abstractmethod
    def load_model(self, model_path: str) -> bool:
        pass
EOF

    # Create __init__.py files in all subdirectories
    find src -type d -exec touch {}/__init__.py \;
    find tests -type d -exec touch {}/__init__.py \;
    
    # Create placeholders for additional source modules
    touch src/hardware/manager.py
    touch src/hardware/camera/{base_camera.py,ai_camera.py,usb_camera.py}
    touch src/hardware/radar/{base_radar.py,ops243c.py}
    touch src/detection/{base_detector.py,vehicle_detector.py}
    touch src/detection/models/{tensorflow_model.py,fallback_model.py}
    touch src/detection/tracking/{tracker.py,correlation.py}
    touch src/data/{storage.py,buffer.py,serialization.py}
    touch src/monitoring/{system_monitor.py,health_check.py,metrics.py}
    touch src/services/{traffic_service.py,data_fusion.py,anomaly_detection.py}
    touch src/api/{flask_app.py,websocket.py}
    touch src/api/routes/{health.py,traffic.py,config.py}
    touch src/utils/{logger.py,decorators.py,helpers.py}
    
    # Create test files placeholders
    touch tests/unit/{test_camera.py,test_radar.py,test_detection.py,test_services.py}
    touch tests/integration/test_system.py
    touch tests/fixtures/sample_data.py

    # Create scripts with installation and start/recovery routines
    cat > scripts/install.sh << 'EOF'
#!/bin/bash
# Installation script for traffic monitor system

echo "Installing traffic monitor system..."

if [[ -d "venv" ]]; then
    echo "Virtual environment already exists, using existing one..."
    source venv/bin/activate
else
    echo "Creating new virtual environment..."
    sudo apt update && sudo apt upgrade -y
    sudo apt install -y python3-pip python3-venv git cmake build-essential
    sudo apt install -y python3-picamera2
    python3 -m venv venv
    source venv/bin/activate
fi

echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r ../requirements.txt

echo "Installation complete!"
echo "Virtual environment is ready at: $(pwd)/venv"
echo "Activate with: source venv/bin/activate"
EOF

    chmod +x scripts/install.sh

    cat > scripts/start_monitoring.py << 'EOF'
#!/usr/bin/env python3
"""Start the traffic monitoring system."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
def main():
    print("Starting traffic monitor system...")
    print("This is a placeholder - implement your main application logic here")
if __name__ == "__main__":
    main()
EOF

    chmod +x scripts/start_monitoring.py

    cat > scripts/system_check.py << 'EOF'
#!/usr/bin/env python3
"""System health check script."""
def check_system():
    print("Performing system health check...")
    print("✓ Hardware check placeholder")
    print("✓ Dependencies check placeholder")
    print("✓ Configuration check placeholder")
    print("System check complete!")
if __name__ == "__main__":
    check_system()
EOF

    chmod +x scripts/system_check.py

    cat > scripts/calibration.py << 'EOF'
#!/usr/bin/env python3
"""Calibration script for sensors."""
def calibrate_system():
    print("Starting system calibration...")
    print("This is a placeholder - implement calibration logic here")
if __name__ == "__main__":
    calibrate_system()
EOF

    chmod +x scripts/calibration.py

    # Create documentation placeholders
    cat > docs/installation.md << 'EOF'
# Installation Guide

## Prerequisites
- Raspberry Pi 5 with Raspberry Pi OS
- Python 3.8 or higher
- Camera module or USB camera
- Radar sensor (OPS243C compatible)

## Installation Steps
1. Clone or copy the project to your Raspberry Pi
2. Run the installation script:
   ./scripts/install.sh
3. Activate the virtual environment:
   source venv/bin/activate
4. Configure hardware settings in config/hardware_config.yaml
5. Run system check:
   python scripts/system_check.py
EOF

    cat > docs/configuration.md << 'EOF'
# Configuration Guide

## Configuration Files

### settings.py
Main application settings including paths, thresholds, and API configuration.

### hardware_config.yaml
Hardware-specific settings for camera and radar sensors.

### logging.yaml
Logging configuration with file rotation and different log levels.

## Customization
Modify configuration files before starting the system.
EOF

    cat > docs/api_reference.md << 'EOF'
# API Reference

## REST Endpoints

### Health Check
- GET /health - System health status

### Traffic Data
- GET /traffic/current - Current traffic status
- GET /traffic/history - Historical traffic data

### Configuration
- GET /config - Current configuration
- POST /config - Update configuration

## WebSocket Events
- traffic_update - Real-time traffic updates
- system_status - System status updates

## Response Formats
All responses are in JSON format.
EOF

    cat > docs/troubleshooting.md << 'EOF'
# Troubleshooting Guide

## Common Issues

### Camera Not Detected
- Check camera connection to CSI port
- Verify camera is enabled in raspi-config
- Check permissions for camera access

### Radar Connection Failed
- Verify USB connection
- Check device permissions
- Confirm correct baud rate settings

### High CPU Usage
- Monitor system resources
- Check detection model complexity
- Adjust frame rate if necessary

### API Not Responding
- Check if port 5000 is available
- Verify firewall settings
- Check application logs

## Log Files
Check data/logs/traffic_monitor.log for error details.
EOF

    # Create a systemd service file for deployment
    cat > systemd/traffic-monitor.service << 'EOF'
[Unit]
Description=Traffic Monitor System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/traffic_monitor
Environment=PATH=/home/pi/traffic_monitor/venv/bin
ExecStart=/home/pi/traffic_monitor/venv/bin/python /home/pi/traffic_monitor/scripts/start_monitoring.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    print_success "All placeholder files created successfully"
}

# Adjust file permissions appropriately
set_permissions() {
    print_status "Setting file permissions..."
    
    # Ensure all scripts are executable
    chmod +x scripts/*.py scripts/*.sh
    
    # Create data directories if missing and set permissions
    mkdir -p data/{logs,models,cache}
    chmod 755 data
    chmod 755 data/*
    
    print_success "Permissions set successfully"
}

# Main function to run the project scaffolding steps
main_project_setup() {
    print_status "Starting Traffic Monitor project structure setup for Raspberry Pi 5"
    check_raspberry_pi
    create_directories
    create_files
    set_permissions
    print_success "Traffic Monitor project structure created successfully!"
    print_status "Project location: $(pwd)"
    echo ""
    print_status "Next steps:"
    if [[ $(basename "$PWD") == "traffic_monitor" ]]; then
        print_status "1. Review and modify configuration files in config/"
        print_status "2. Activate your virtual environment: source venv/bin/activate"
        print_status "3. Run: ./scripts/install.sh"
        print_status "4. Start development or run system check: python scripts/system_check.py"
    else
        print_status "1. cd traffic_monitor"
        print_status "2. Review and modify configuration files in config/"
        print_status "3. Run: ./scripts/install.sh"
        print_status "4. Activate virtual environment: source venv/bin/activate"
        print_status "5. Start development or run system check: python scripts/system_check.py"
    fi
}

# Run the project structure setup
main_project_setup

echo ""
print_success "Setup complete! Your Traffic Monitoring System environment and project structure are ready."
