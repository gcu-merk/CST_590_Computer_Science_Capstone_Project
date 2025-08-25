#!/usr/bin/env python3
"""
Setup Script for Raspberry Pi 5 Edge ML Traffic Monitoring System
Installs dependencies and prepares the system for operation
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"\n{description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def install_system_dependencies():
    """Install system-level dependencies"""
    commands = [
        ("sudo apt update", "Updating package lists"),
        ("sudo apt install -y python3-pip python3-venv python3-dev", "Installing Python development tools"),
        ("sudo apt install -y libhdf5-dev libhdf5-serial-dev libhdf5-103", "Installing HDF5 libraries for TensorFlow"),
        ("sudo apt install -y libatlas-base-dev gfortran", "Installing ATLAS libraries"),
        ("sudo apt install -y libjpeg-dev libtiff5-dev libpng-dev", "Installing image libraries"),
        ("sudo apt install -y libavcodec-dev libavformat-dev libswscale-dev libv4l-dev", "Installing video libraries"),
        ("sudo apt install -y libxvidcore-dev libx264-dev", "Installing video codecs"),
        ("sudo apt install -y libgtk-3-dev", "Installing GTK development libraries"),
        ("sudo apt install -y sqlite3 libsqlite3-dev", "Installing SQLite"),
        ("sudo apt install -y git wget curl", "Installing utilities")
    ]
    
    print("Installing system dependencies...")
    for command, description in commands:
        if not run_command(command, description):
            return False
    return True

def create_virtual_environment():
    """Create Python virtual environment"""
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("Virtual environment already exists")
        return True
    
    return run_command("python3 -m venv venv", "Creating virtual environment")

def install_python_dependencies():
    """Install Python dependencies"""
    
    # Activate virtual environment and install packages
    pip_command = "./venv/bin/pip" if os.name != 'nt' else "venv\\Scripts\\pip"
    
    commands = [
        (f"{pip_command} install --upgrade pip", "Upgrading pip"),
        (f"{pip_command} install wheel setuptools", "Installing build tools"),
        (f"{pip_command} install -r edge_processing/requirements.txt", "Installing edge processing dependencies"),
        (f"{pip_command} install -r edge_api/requirements.txt", "Installing edge API dependencies")
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            return False
    return True

def setup_directories():
    """Create necessary directories"""
    directories = [
        "logs",
        "data/exports",
        "data/backups",
        "data/models",
        "config"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {directory}")
    
    return True

def create_config_files():
    """Create default configuration files"""
    
    # Main configuration
    config_content = """# Traffic Monitoring System Configuration

# Hardware Settings
[hardware]
camera_index = 0
radar_port = /dev/ttyACM0
radar_baudrate = 9600

# Processing Settings
[processing]
detection_confidence_threshold = 0.5
speed_detection_threshold = 0.5
fusion_association_threshold = 100.0
max_track_age = 5.0

# API Settings
[api]
host = 0.0.0.0
port = 5000
enable_cors = true

# Database Settings
[database]
path = data/traffic_data.db
backup_interval = 3600

# Logging Settings
[logging]
level = INFO
log_file = logs/traffic_monitoring.log
max_file_size = 10MB
backup_count = 5

# System Health
[health]
cpu_threshold = 80.0
memory_threshold = 85.0
disk_threshold = 90.0
temp_threshold = 70.0
"""
    
    with open("config/traffic_monitoring.conf", "w") as f:
        f.write(config_content)
    
    print("✓ Created configuration file")
    return True

def main():
    """Main setup function"""
    print("=" * 60)
    print("Raspberry Pi 5 Edge ML Traffic Monitoring System Setup")
    print("=" * 60)
    
    # Check if running on Raspberry Pi
    try:
        with open("/proc/cpuinfo", "r") as f:
            cpuinfo = f.read()
            if "BCM" not in cpuinfo:
                print("Warning: This doesn't appear to be a Raspberry Pi")
                response = input("Continue anyway? (y/N): ")
                if response.lower() != 'y':
                    sys.exit(1)
    except FileNotFoundError:
        print("Warning: Cannot detect Raspberry Pi (running on non-Linux system)")
    
    steps = [
        ("Installing system dependencies", install_system_dependencies),
        ("Creating virtual environment", create_virtual_environment),
        ("Installing Python dependencies", install_python_dependencies),
        ("Setting up directories", setup_directories),
        ("Creating configuration files", create_config_files)
    ]
    
    for step_name, step_function in steps:
        print(f"\n{'='*20} {step_name} {'='*20}")
        if not step_function():
            print(f"\n✗ Setup failed at: {step_name}")
            sys.exit(1)
    
    print("\n" + "="*60)
    print("✓ Setup completed successfully!")
    print("="*60)
    print("\nNext steps:")
    print("1. Activate the virtual environment:")
    if os.name != 'nt':
        print("   source venv/bin/activate")
    else:
        print("   venv\\Scripts\\activate")
    print("2. Run the main application:")
    print("   python main_edge_app.py")
    print("3. Access the API at: http://localhost:5000")
    print("4. Check system health: http://localhost:5000/api/health")
    print("\nFor more information, see the documentation folder.")

if __name__ == "__main__":
    main()
