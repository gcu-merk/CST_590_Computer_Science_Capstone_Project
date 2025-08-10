#!/bin/bash

# Traffic Monitor Project Setup Script for Raspberry Pi 5
# This script creates the complete directory structure for the traffic monitoring system

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Check if running on Raspberry Pi
check_raspberry_pi() {
    if [[ ! -f /proc/cpuinfo ]] || ! grep -q "Raspberry Pi" /proc/cpuinfo; then
        print_warning "This script is designed for Raspberry Pi but will continue anyway"
    else
        print_success "Running on Raspberry Pi - proceeding with setup"
    fi
}

# Create directory structure
create_directories() {
    print_status "Creating traffic monitor directory structure..."
    
    # Check if we're already in a traffic-monitor directory
    if [[ $(basename "$PWD") == "traffic-monitor" ]]; then
        print_status "Already in traffic-monitor directory, creating structure here..."
    else
        # Main project directory
        mkdir -p traffic_monitor
        cd traffic_monitor
    fi
    
    # Root level directories
    mkdir -p config
    mkdir -p src/{core,hardware,detection,data,monitoring,services,api,utils}
    mkdir -p tests/{unit,integration,fixtures}
    mkdir -p scripts
    mkdir -p data/{models,logs,cache}
    mkdir -p docs
    mkdir -p systemd
    
    # Hardware subdirectories
    mkdir -p src/hardware/{camera,radar}
    
    # Detection subdirectories
    mkdir -p src/detection/{models,tracking}
    
    # API subdirectories
    mkdir -p src/api/routes
    
    print_success "Directory structure created successfully"
}

# Create placeholder files with basic structure
create_files() {
    print_status "Creating placeholder files..."
    
    # Root files
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

    # Config files
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
    maxBytes: 10485760  # 10MB
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
  type: "ai_camera"  # Options: ai_camera, usb_camera
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
  distance_between: 10.0  # meters between camera and radar
  calibration_required: true
EOF

    # Core module files
    touch src/__init__.py
    
    cat > src/core/__init__.py << 'EOF'
"""Core module for traffic monitor system."""
EOF

    cat > src/core/base.py << 'EOF'
"""Base classes for the traffic monitor system."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class BaseComponent(ABC):
    """Base class for all system components."""
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}
        self._initialized = False
        self._running = False
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the component."""
        pass
    
    @abstractmethod
    def start(self) -> bool:
        """Start the component."""
        pass
    
    @abstractmethod
    def stop(self) -> bool:
        """Stop the component."""
        pass
    
    @property
    def is_running(self) -> bool:
        """Check if component is running."""
        return self._running
    
    @property
    def is_initialized(self) -> bool:
        """Check if component is initialized."""
        return self._initialized
EOF

    cat > src/core/exceptions.py << 'EOF'
"""Custom exceptions for traffic monitor system."""

class TrafficMonitorError(Exception):
    """Base exception for traffic monitor system."""
    pass

class HardwareError(TrafficMonitorError):
    """Hardware-related errors."""
    pass

class DetectionError(TrafficMonitorError):
    """Detection and tracking errors."""
    pass

class ConfigurationError(TrafficMonitorError):
    """Configuration-related errors."""
    pass

class APIError(TrafficMonitorError):
    """API-related errors."""
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
    """Represents a detection result."""
    object_id: str
    class_name: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x, y, width, height
    timestamp: datetime
    speed: Optional[float] = None

@dataclass
class SensorData:
    """Represents sensor data."""
    sensor_type: str
    timestamp: datetime
    data: Dict[str, Any]

class ISensor(ABC):
    """Interface for sensor components."""
    
    @abstractmethod
    def read_data(self) -> Optional[SensorData]:
        """Read data from the sensor."""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if sensor is connected."""
        pass

class IDetector(ABC):
    """Interface for detection components."""
    
    @abstractmethod
    def detect(self, frame: Any) -> List[DetectionResult]:
        """Perform detection on a frame."""
        pass
    
    @abstractmethod
    def load_model(self, model_path: str) -> bool:
        """Load detection model."""
        pass
EOF

    # Create __init__.py files for all packages
    find src -type d -exec touch {}/__init__.py \;
    find tests -type d -exec touch {}/__init__.py \;
    
    # Create basic placeholder files for major modules
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
    
    # Test files
    touch tests/unit/{test_camera.py,test_radar.py,test_detection.py,test_services.py}
    touch tests/integration/test_system.py
    touch tests/fixtures/sample_data.py
    
    # Scripts
    cat > scripts/install.sh << 'EOF'
#!/bin/bash
# Installation script for traffic monitor system

echo "Installing traffic monitor system..."

# Check if virtual environment already exists
if [[ -d "venv" ]]; then
    echo "Virtual environment already exists, using existing one..."
    source venv/bin/activate
else
    echo "Creating new virtual environment..."
    # Update system
    sudo apt update && sudo apt upgrade -y
    
    # Install system dependencies
    sudo apt install -y python3-pip python3-venv git cmake build-essential
    
    # Install camera dependencies
    sudo apt install -y python3-picamera2
    
    # Create virtual environment
    python3 -m venv venv
    source venv/bin/activate
fi

# Install/upgrade Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

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
    
    # TODO: Initialize and start all components
    # - Hardware manager
    # - Detection services
    # - API server
    # - Monitoring services

if __name__ == "__main__":
    main()
EOF

    chmod +x scripts/start_monitoring.py
    
    cat > scripts/system_check.py << 'EOF'
#!/usr/bin/env python3
"""System health check script."""

import sys
import os

def check_system():
    """Perform system health checks."""
    print("Performing system health check...")
    
    # Check hardware connections
    print("✓ Hardware check placeholder")
    
    # Check dependencies
    print("✓ Dependencies check placeholder")
    
    # Check configuration
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
    """Calibrate camera and radar sensors."""
    print("Starting system calibration...")
    print("This is a placeholder - implement calibration logic here")

if __name__ == "__main__":
    calibrate_system()
EOF

    chmod +x scripts/calibration.py
    
    # Documentation files
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
   ```bash
   ./scripts/install.sh
   ```
3. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```
4. Configure hardware settings in `config/hardware_config.yaml`
5. Run system check:
   ```bash
   python scripts/system_check.py
   ```

## Hardware Setup
- Connect camera module to CSI port
- Connect radar sensor to USB port
- Ensure proper power supply for Pi 5
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
Modify configuration files before starting the system to match your hardware setup and requirements.
EOF

    cat > docs/api_reference.md << 'EOF'
# API Reference

## REST Endpoints

### Health Check
- `GET /health` - System health status

### Traffic Data
- `GET /traffic/current` - Current traffic status
- `GET /traffic/history` - Historical traffic data

### Configuration
- `GET /config` - Current configuration
- `POST /config` - Update configuration

## WebSocket Events
- `traffic_update` - Real-time traffic updates
- `system_status` - System status updates

## Response Formats
All responses are in JSON format with appropriate HTTP status codes.
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
Check `data/logs/traffic_monitor.log` for detailed error information.
EOF

    # Systemd service file
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

# Set proper permissions
set_permissions() {
    print_status "Setting file permissions..."
    
    # Make scripts executable
    chmod +x scripts/*.py scripts/*.sh
    
    # Create data directories with proper permissions
    mkdir -p data/{logs,models,cache}
    chmod 755 data
    chmod 755 data/*
    
    print_success "Permissions set successfully"
}

# Main execution
main() {
    print_status "Starting Traffic Monitor setup for Raspberry Pi 5"
    
    check_raspberry_pi
    create_directories
    create_files
    set_permissions
    
    print_success "Traffic Monitor project structure created successfully!"
    print_status "Project location: $(pwd)"
    print_status ""
    print_status "Next steps:"
    if [[ $(basename "$PWD") == "traffic-monitor" ]]; then
        print_status "1. Review and modify configuration files in config/"
        print_status "2. Activate your existing virtual environment: source venv/bin/activate"
        print_status "3. Run: ./scripts/install.sh (will use existing venv)"
        print_status "4. Start development or run system check: python scripts/system_check.py"
    else
        print_status "1. cd traffic_monitor"
        print_status "2. Review and modify configuration files in config/"
        print_status "3. Run: ./scripts/install.sh"
        print_status "4. Activate virtual environment: source venv/bin/activate"
        print_status "5. Start development or run system check: python scripts/system_check.py"
    fi
}

# Run main function
main