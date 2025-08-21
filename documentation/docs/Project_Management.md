# Project Management Summary

**Document Version:** 1.0  
> **Note:**
> This project is managed with a Minimal Viable Product (MVP)-first approach, emphasizing incremental development, future extensibility, and robust risk management. Phase 1 is designed to deliver a working MVP, with later phases planned for future implementation as time and resources allow. For full feedback and rationale, see [AI Feedback for Capstone Completion plan](../archive/AI%20Feedback%20for%20Capstone%20Completion%20plan.txt).
**Last Updated:** August 7, 2025  
**Project:** Raspberry Pi 5 Edge ML Traffic Monitoring System  
**Authors:** Project Team  

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Implementation Timeline](#1-implementation-timeline)
3. [Budget & Cost Estimates](#2-budget--cost-estimates)
4. [Risk Management Matrix](#3-risk-management-matrix--contingency-planning)
5. [Quality Assurance & Testing Protocols](#4-quality-assurance--testing-protocols)
6. [Architectural Design Comparison](#architectural-design-comparison)

**See also:**

- [Technical Design Document](./Technical_Design.md)
- [Implementation & Deployment Guide](./Implementation_Deployment.md)
- [User Guide](./User_Guide.md)
- [References & Appendices](./References_Appendices.md)

## Executive Summary

The Raspberry Pi 5 Edge ML Traffic Monitoring System is a comprehensive, edge-based solution for real-time vehicle detection, speed measurement, and traffic analytics. Leveraging a Raspberry Pi 5, AI-enabled camera, and radar sensor, the system processes data locally to reduce bandwidth, enhance privacy, and enable rapid response to traffic events. This documentation provides a clear roadmap for implementation, risk management, and quality assurance, ensuring the project is delivered on time, robustly tested, and aligned with best practices for smart city and transportation applications.

## 1. Phased Implementation Overview

The project is delivered in four major phases, each building on the previous:

### Phase 1 (Weeks 1-2): Get Basic Detection Working

- Project planning, hardware setup, software environment, and basic vehicle detection implementation

### Phase 2 (Weeks 3-4): Add Radar Integration and Simple Correlation

- Radar sensor integration, data fusion development, and speed correlation algorithms

### Phase 3 (Weeks 5-6): Build Web Interface and API

- API development, web dashboard creation, and real-time communication implementation

### Phase 4 (Weeks 7-8): Integration Testing, Documentation and Basic Optimization

- System testing, performance optimization, documentation completion, and deployment preparation

Each phase below lists the relevant milestones and their target completion dates, aligned with the Capstone Completion Plan.

## 1. Implementation Timeline

### Phase 1 Milestones: Get Basic Detection Working (Weeks 1-2)

| Milestone | Description & Sub-Tasks | Target Completion |
|-----------|-------------------------|------------------|
| Hardware Setup | Assemble Raspberry Pi 5, Sony IMX500 AI camera, storage; verify hardware connectivity; allocate buffer for hardware issues | Week 1 |
| Software Environment | Install Raspberry Pi OS, Python 3.11+, TensorFlow Lite, OpenCV; set up development environment; test camera interface | Week 1 |
| Basic Vehicle Detection | Implement TensorFlow Lite inference, configure picamera2 interface, basic object detection pipeline, initial testing | Week 2 |
| Data Storage Foundation | Set up SQLite database, basic data persistence, system health monitoring, logging infrastructure | Week 2 |

### Phase 2: Add Radar Integration and Simple Correlation (Weeks 3-4)

| Milestone | Description & Sub-Tasks | Target Completion |
|-----------|-------------------------|------------------|
| Radar Integration | Install OPS243-C radar sensor, configure GPIO/UART communication, test radar data acquisition, calibration | Week 3 |
| Data Fusion Development | Implement basic correlation algorithms, synchronize camera and radar data, Kalman filtering foundation | Week 4 |
| Speed Correlation | Develop speed calculation from radar data, correlate with camera detections, basic accuracy validation | Week 4 |

### Phase 3: Build Web Interface and API (Weeks 5-6)

| Milestone | Description & Sub-Tasks | Target Completion |
|-----------|-------------------------|------------------|
| API Gateway Development | Implement Flask-SocketIO server, REST endpoints, WebSocket communication, CORS configuration | Week 5 |
| Web Dashboard | Create real-time monitoring interface, data visualization, system status display, responsive design | Week 6 |
| Real-time Communication | Implement live data streaming, event broadcasting, API documentation, integration testing | Week 6 |

### Phase 4: Integration Testing, Documentation and Basic Optimization (Weeks 7-8)

| Milestone | Description & Sub-Tasks | Target Completion |
|-----------|-------------------------|------------------|
| System Integration Testing | End-to-end testing, performance validation, bug fixes, system reliability testing | Week 7 |
| Performance Optimization | Edge inference optimization, memory management, CPU/GPU utilization, Docker containerization | Week 7 |
| Documentation & Deployment | Complete technical documentation, user guides, deployment scripts, final system validation | Week 8 |

**Iterative Development & MVP:**
This project follows an agile, milestone-based approach. The initial focus is on delivering a Minimal Viable Product (MVP) with core features, followed by iterative improvements based on feedback and testing. Each milestone includes buffer time for unforeseen issues and is broken into actionable sub-tasks to ensure steady progress and risk mitigation.

**Note:** For a visual Gantt chart, use project management tools like Trello, Asana, or GanttProject.

## 2. Budget & Cost Estimates

### Hardware Costs (Per Unit)

| Component | Model/Description | Unit Cost (USD) | Quantity | Total Cost |
|-----------|-------------------|----------------|----------|------------|
| Raspberry Pi 5 | CanaKit Raspberry Pi 5 Starter Kit MAX - Turbine White (256 GB Edition) (16GB RAM) | $120 | 1 | $219 |
| AI Camera | Sony IMX500 (Raspberry Pi AI Camera) | $70 | 1 | $70 |
| AI Camera extended cable | Official CSI FPC Flexible Cable Compatible with Raspberry Pi 5, 22Pin to 15Pin, Suitable for CSI Camera Modules, 500MM/50CM/1.64 FT | $9.79 | 1 | $9.79 |
| Radar Sensor | OmniPreSense OPS243-C | $255 | 1 | $255 |
| Storage | Samsung T7 Shield 2TB, Portable SSD, up-to 1050MB/s, USB 3.2 Gen2, Rugged,IP65 Water & Dust Resistant, Extenal Solid State Drive (MU-PE2T0S/AM), Black | $149 | 1 | $149 |
| MicroSD Card Extender | LANMU Micro SD to Micro SD Card Extension Cable Adapter Flexible Extender Compatible with Ender 3 Pro/Ender 3/Ender 3 V2/Ender 5 Plus/Ender 5 Pro/CR-10S Pro/Raspberry Pi(5.9in/15cm) | $5.99 | 1 | $5.99 |
| Power Supply | DC 12V/24V to 5V 15A Step Down Converter - Voltage Regulator Buck Converter Power Supply Transformer | $10.99 | 1 | $10.99 |
| USB Power Supply | DC 12V/24V to 5V USB C Step Down Converter Type-C Interface 5A 25W Waterproof Buck Module Power Adapter Compatible with Raspberry Pi 4, Cell Phones 1-Pack | $9.99 | 1 | $9.99 |
| Main power adapter | 24V DC Power Adapter Doorbell Transformer for C WireThermostat,Heywell Nest,Ring Pro doorbell,Ring Wired doorbell,Wyze Video Doorbell,24V LED Strip Light,Comes with CH-2 Connector, Cord 19.6FT Black | $15.99 | 1 | $15.99 |
| Ethernet cable | adaol Cat 6 Ethernet Cable 100 ft, Outdoor & Indoor 10Gbps Support Cat8 Cat7 Network, Flat RJ45 Internet LAN Computer Patch Cable for Router, Modem, Switch, Gaming Consoles, Streaming Devices, White | $16.14 | 1 | $16.14 |
| Enclosure | Junction Box, IP67 Waterproof Plastic Enclosure for Electrical Project, Hinged Grey Cover, Includes Mounting Plate and Wall Bracket 290×190×140mm (11.4"×7.5"×5.5") | $24.99 | 1 | $24.99 |
| Mounting Hardware | Pole/wall mount and assorted hardware | $50 | 1 | $50 |
| **Hardware Subtotal** | | | | **$804.89** |

### Software & Development Costs

| Category | Description | Cost (USD) |
|----------|-------------|------------|
| Software Licenses | Open source (PostgreSQL, Python, TensorFlow) | $0 |
| Cloud Services | Optional cloud hosting (monthly) | $20-50 |
| Development Tools | VS Code, Git, testing tools | $0 |
| **Software Subtotal** | | **$0-50** |

### Implementation & Deployment Costs

| Activity | Description | Hours | Rate | Total Cost |
|----------|-------------|-------|------|------------|
| System Integration | Hardware assembly and configuration | 8 | $75 | $600 |
| Software Deployment | OS setup, application installation | 4 | $75 | $300 |
| Testing & Validation | Field testing and calibration | 6 | $75 | $450 |
| Documentation | User training and documentation | 4 | $75 | $300 |
| **Implementation Subtotal** | | | | **$1,650** |

### Total Project Cost

- **Per Unit Hardware:** $804.89
- **Implementation (One-time):** $1,650
- **Monthly Operating:** $20-50 (if using cloud services)
- **Total First Unit:** $2,454.89 + monthly costs

*Note: Costs may vary based on supplier, location, and bulk purchasing agreements.*

## 3. Risk Management Matrix & Contingency Planning

| Risk | Impact | Likelihood | Mitigation Strategy | Monitoring/Alerting | Contingency Plan |
|------|--------|------------|---------------------|---------------------|------------------|
| Hardware failure (Pi, camera, radar) | High | Medium | Use quality components, keep spares | Health indicators, system logs | Allocate buffer time, keep spare parts, simulate data if needed |
| Data loss (storage failure) | High | Low | Regular backups, use SSD, monitor storage | Storage usage alerts, backup logs | Restore from backup, rollback to last known good state |
| ML model inaccuracy | Medium | Medium | Diverse training data, real-world validation | Model performance metrics | Retrain model, fallback to previous version |
| Network outage | Medium | Medium | Offline-first design, local storage | Network status monitoring | Operate in offline mode, auto-reconnect logic |
| Power loss | High | Low | UPS or PoE with backup, monitor power | Power status alerts | Resume on power restore, buffer for downtime |
| Security breach (API, dashboard) | High | Low | Auth, HTTPS, updates, firewall | Security logs, intrusion detection | Revoke credentials, patch vulnerabilities |
| Integration bugs (sensor fusion, API) | Medium | Medium | Incremental testing, code reviews | Automated test results, error logs | Isolate faulty module, use simulated data |
| Regulatory/compliance issues | Medium | Low | Review laws, anonymize data | Compliance checklist | Remove/modify non-compliant features |

**Contingency Planning:**

- Prioritize core MVP features to ensure essential delivery if time is tight
- Allocate buffer time in each milestone for unforeseen issues
- Plan regular backups and use version control for rollback
- Use simulated data if live sensor data is unavailable
- Monitor for hardware, network, and security risks with alerts

---

## 4. Quality Assurance & Testing Protocols

### Testing Protocols

- Break down development into small, testable sub-tasks for each milestone
- Perform frequent, incremental testing during development (unit, integration, system)
- Use automated tests and code reviews to catch issues early
- Track blockers and issues in a project management tool
- Validate MVP features first, then expand to additional features

### ML/AI Evaluation Metrics

- Track model accuracy, precision, recall, and real-world performance
- Use field testing feedback to improve models

### Documentation & Review

- Update documentation iteratively as features evolve
- Schedule regular documentation reviews before each milestone

---

## 5. Raspberry Pi Headless Setup Script

The following script automates the headless setup of a Raspberry Pi 5 for this project. It configures external SSD storage, camera, and UART for the radar sensor.  
**Tested on Raspberry Pi 5 with Raspberry Pi OS Bookworm.**

> **Usage:**  
> Save the script as `setup_headless.sh`, make it executable (`chmod +x setup_headless.sh`), and run as a regular user with sudo privileges:  
> `./setup_headless.sh`

```bash
# filepath: setup_headless.sh
#!/bin/bash

# Raspberry Pi Headless Setup Script
# Sets up external SSD storage, camera, and UART for radar sensor
# Tested on Raspberry Pi 5 with Raspberry Pi OS Bookworm

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   error "This script should not be run as root. Run as regular user with sudo privileges."
   exit 1
fi

log "Starting Raspberry Pi Headless Setup..."

# Update system packages
log "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required packages
log "Installing camera and utility packages..."
sudo apt install -y \
    libcamera-tools \
    libcamera-apps \
    rpicam-apps \
    usbutils \
    lsof

success "Packages installed successfully"

# Detect external SSD
log "Detecting external SSD..."
if ! lsblk | grep -q "sda"; then
    error "No external SSD detected on /dev/sda. Please connect your SSD and try again."
    exit 1
fi

SSD_SIZE=$(lsblk /dev/sda -n -o SIZE | head -n1 | tr -d ' ')
SSD_MODEL=$(sudo fdisk -l /dev/sda | grep "Disk model:" | cut -d: -f2 | tr -d ' ')

log "Found SSD: $SSD_MODEL ($SSD_SIZE)"

# Check if SSD is already properly formatted and mounted
if mount | grep -q "/dev/sda1.*ext4.*storage"; then
    success "SSD already mounted at /mnt/storage with ext4"
    SKIP_FORMAT=true
else
    SKIP_FORMAT=false
    warning "SSD needs to be set up"
fi

# Setup external SSD storage
if [[ "$SKIP_FORMAT" == "false" ]]; then
    log "Setting up external SSD storage..."
    
    # Check if partition exists and has data
    if lsblk | grep -q "sda1"; then
        warning "Existing partition found on /dev/sda1"
        echo "Current partition table:"
        sudo fdisk -l /dev/sda
        echo ""
        
        read -p "Do you want to format /dev/sda1? This will ERASE ALL DATA! (y/N): " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            error "Aborted by user. Cannot continue without formatting."
            exit 1
        fi
    fi
    
    # Unmount any existing mounts
    log "Unmounting any existing mounts..."
    sudo umount /dev/sda* 2>/dev/null || true
    sudo umount /media/*/T7Shield 2>/dev/null || true
    sudo umount /media/*/* 2>/dev/null || true
    
    # Create mount point
    log "Creating mount point..."
    sudo mkdir -p /mnt/storage
    
    # If no partition exists, create one
    if ! lsblk | grep -q "sda1"; then
        log "Creating partition on /dev/sda..."
        sudo fdisk /dev/sda << EOF
n
p
1


w
EOF
        sleep 2  # Wait for partition to be recognized
    fi
    
    # Format partition
    log "Formatting /dev/sda1 with ext4..."
    sudo mkfs.ext4 -F /dev/sda1
    
    # Mount the partition
    log "Mounting /dev/sda1 to /mnt/storage..."
    sudo mount /dev/sda1 /mnt/storage
    
    # Set up automatic mounting
    log "Configuring automatic mounting..."
    # Remove any existing entries for this device
    sudo sed -i '/\/dev\/sda1/d' /etc/fstab
    # Add new entry
    echo "/dev/sda1 /mnt/storage ext4 defaults 0 2" | sudo tee -a /etc/fstab
    
    success "External SSD formatted and mounted"
else
    log "Cleaning up duplicate mounts..."
    # Remove duplicate mounts but keep /mnt/storage
    sudo umount /media/*/T7Shield 2>/dev/null || true
fi

# Set proper permissions
log "Setting up storage permissions..."
sudo chown $USER:$USER /mnt/storage
sudo chmod 775 /mnt/storage

# Create user data directory
sudo -u $USER mkdir -p /mnt/storage/user_data
sudo -u $USER mkdir -p /mnt/storage/backups
sudo -u $USER mkdir -p /mnt/storage/media
sudo -u $USER mkdir -p /mnt/storage/projects

success "Storage directories created"

# Test storage
log "Testing storage write access..."
echo "Headless setup test - $(date)" | sudo -u $USER tee /mnt/storage/setup_test.txt > /dev/null
if [[ -f /mnt/storage/setup_test.txt ]]; then
    success "Storage write test passed"
else
    error "Storage write test failed"
    exit 1
fi

# Enable camera
log "Configuring camera..."
if ! grep -q "camera_auto_detect=1" /boot/firmware/config.txt; then
    echo "camera_auto_detect=1" | sudo tee -a /boot/firmware/config.txt
    REBOOT_REQUIRED=true
fi

# Enable UART for radar sensor
log "Configuring UART for radar sensor..."
if ! grep -q "enable_uart=1" /boot/firmware/config.txt; then
    echo "enable_uart=1" | sudo tee -a /boot/firmware/config.txt
    REBOOT_REQUIRED=true
fi

if ! grep -q "dtparam=uart0=on" /boot/firmware/config.txt; then
    echo "dtparam=uart0=on" | sudo tee -a /boot/firmware/config.txt
    REBOOT_REQUIRED=true
fi

# Disable serial console to free up UART for radar
if sudo systemctl is-enabled serial-getty@ttyAMA0.service &>/dev/null; then
    sudo systemctl disable serial-getty@ttyAMA0.service
    success "Serial console disabled for UART use"
fi

# Test camera (if no reboot required)
if [[ -z "$REBOOT_REQUIRED" ]]; then
    log "Testing camera..."
    if rpicam-hello --list-cameras 2>/dev/null | grep -q "Available cameras"; then
        success "Camera detected and working"
        
        # Take test photo
        log "Taking test photo..."
        if sudo -u $USER rpicam-jpeg -o /mnt/storage/setup_camera_test.jpg --nopreview --width 640 --height 480 --timeout 3000; then
            success "Test photo saved to /mnt/storage/setup_camera_test.jpg"
        else
            warning "Camera test photo failed, but camera was detected"
        fi
    else
        warning "Camera not detected (may require reboot)"
    fi
else
    warning "Camera test skipped - reboot required"
fi

# Create helpful aliases and functions
log "Creating helpful aliases..."
cat << 'EOF' | sudo -u $USER tee -a /home/$USER/.bashrc

# Raspberry Pi Setup Aliases
alias camera-photo='rpicam-jpeg --nopreview'
alias camera-video='rpicam-vid --nopreview'
alias camera-list='rpicam-hello --list-cameras'
alias storage-info='df -h | grep sda1'
alias radar-monitor='sudo cat /dev/serial0'
alias setup-test='bash /home/$USER/test_setup.sh'

EOF

# Create test script
log "Creating system test script..."
cat << 'EOF' > /home/$USER/test_setup.sh
#!/bin/bash

echo "=== Raspberry Pi Headless Setup Test ==="
echo ""

echo "1. Testing USB devices..."
lsusb | grep -E "(Samsung|T7)" && echo "✅ External SSD detected" || echo "❌ External SSD not found"

echo ""
echo "2. Testing storage mount..."
if df -h | grep -q "/mnt/storage"; then
    echo "✅ Storage mounted:"
    df -h | grep sda1
    echo "✅ Storage writable:" 
    echo "Test $(date)" > /mnt/storage/test_$(date +%s).txt && echo "Write test passed" || echo "❌ Write test failed"
else
    echo "❌ Storage not mounted"
fi

echo ""
echo "3. Testing camera..."
if rpicam-hello --list-cameras 2>/dev/null | grep -q "Available cameras"; then
    echo "✅ Camera detected"
    rpicam-hello --list-cameras 2>/dev/null
else
    echo "❌ Camera not detected"
fi

echo ""
echo "4. Testing UART..."
if ls /dev/serial0 &>/dev/null; then
    echo "✅ UART device available at /dev/serial0"
else
    echo "❌ UART device not found"
fi

echo ""
echo "5. Storage directory structure:"
ls -la /mnt/storage/ 2>/dev/null || echo "❌ Cannot access storage"

echo ""
echo "=== Test Complete ==="
EOF

chmod +x /home/$USER/test_setup.sh
success "Test script created at ~/test_setup.sh"

# Final system information
log "System setup complete! Summary:"
echo ""
echo "📁 Storage: $(df -h | grep sda1 | awk '{print $2}') available at /mnt/storage"
echo "📷 Camera: $(rpicam-hello --list-cameras 2>/dev/null | grep -o 'imx[0-9]*' | head -1 || echo 'Detection pending')"
echo "📡 UART: Available at /dev/serial0 for radar sensor"
echo "🔧 Config: Headless mode optimized"
echo ""

# Check if reboot is required
if [[ -n "$REBOOT_REQUIRED" ]]; then
    warning "REBOOT REQUIRED to activate camera and UART settings"
    echo ""
    echo "After reboot, run: ~/test_setup.sh"
    echo ""
    read -p "Reboot now? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log "Rebooting system..."
        sudo reboot
    else
        warning "Remember to reboot before using camera and UART!"
    fi
else
    success "No reboot required - all systems ready!"
    echo ""
    echo "Test your setup with: ~/test_setup.sh"
fi

echo ""
success "Raspberry Pi Headless Setup Complete!"

# Usage examples
cat << 'EOF'

📋 USAGE EXAMPLES:
=================

Camera:
  rpicam-jpeg -o photo.jpg --nopreview
  rpicam-vid -t 10000 -o video.h264 --nopreview
  rpicam-hello --list-cameras

Storage:
  /mnt/storage/user_data/     # Your files
  /mnt/storage/backups/       # System backups  
  /mnt/storage/media/         # Photos/videos
  /mnt/storage/projects/      # Project files

Radar Sensor:
  sudo cat /dev/serial0       # Monitor radar data
  timeout 10s sudo cat /dev/serial0  # Monitor for 10 seconds

System Test:
  ~/test_setup.sh             # Run comprehensive test

EOF
```

---

## Architectural Design Comparison

| **Aspect**                     | **Technical Design Document**                                                                 | **Traffic Monitoring System Design Document**                                                                 |
|--------------------------------|---------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------|
| **Physical Sensing Layer**     | Raspberry Pi AI Camera (Sony IMX500), OPS243-C Radar, Raspberry Pi 5, External SSD          | Same components, but includes IP65/IP66 weatherproof enclosure (-40°C to +71°C) as shown in Figure 1 physical layer                             |
| **Edge Processing Layer**      | TensorFlow + OpenCV, Radar data processing, SORT algorithm, Flask-SocketIO server           | Adds Kalman filtering for data fusion, anomaly detection, and weather integration (detailed in Figure 2 processing pipeline)                           |
| **Network Layer**              | WebSocket Server, REST API, Data Compression, Network Resilience                            | Same features, but explicitly mentions TLS/SSL encryption and API authentication (see Figure 1 network layer)                            |
| **Cloud Services Layer**       | Optional: Data Aggregation, Analytics Engine, Cloud UI, Alert Service                       | Same features, but adds ML model versioning and updates (illustrated in Figure 1 cloud layer)                                                     |
| **Data Flow Architecture**     | Sensors → Edge Processing → Local Dashboard → Cloud Services                                | Adds explicit flow for Local Storage → Data Queue → Cloud Storage → Analytics/Alerts (see Figure 1 and Figure 2 below)                       |
| **Hardware Specification**     | Raspberry Pi 5 (16GB RAM), Samsung T7 SSD, PoE, WiFi/Ethernet                               | Same components, but specifies 2TB SSD and UPS for continuous operation                                     |
| **Sensor Hardware**            | AI Camera (Sony IMX500), OPS243-C Radar                                                     | Same components, but includes detailed specs like resolution, frequency, and power consumption              |
| **Power and Connectivity**     | PoE, WiFi/Ethernet, optional cellular backup                                                | Same features, but adds UPS and official Raspberry Pi PSU                                                   |

### Figure 1: High-Level System Architecture Overview

![System Architecture Diagram - Four-layer architecture showing Physical Sensing Layer with AI Camera and Radar, Edge Processing Layer with Raspberry Pi 5, Network Layer with WiFi/Ethernet connectivity, and Cloud Services Layer with analytics and dashboards. Data flows from bottom sensors up through processing to cloud services, with bidirectional communication paths and optional cloud components.](../archive/Traffic%20Monitoring%20System%20-%20Data%20Flow%20Architecture.png)
*Figure 1: Comprehensive system architecture showing the complete data flow from physical sensors through edge processing to cloud analytics and user interfaces.*

**Figure 1 Description:**
This high-level system architecture diagram illustrates the complete end-to-end data flow and component relationships in the Raspberry Pi 5 Edge ML Traffic Monitoring System. The diagram shows four primary layers:

1. **Physical Sensing Layer** (Bottom): Features the Sony IMX500 AI Camera and OPS243-C Radar sensor mounted in weatherproof enclosures, connected to the Raspberry Pi 5 edge processing unit.

2. **Edge Processing Layer** (Center): The Raspberry Pi 5 performs real-time data fusion, running TensorFlow/OpenCV for computer vision, radar data processing algorithms, and the SORT tracking algorithm. This layer includes local storage on external SSD and the Flask-SocketIO web server.

3. **Network Layer** (Communication): Handles data transmission via WiFi/Ethernet with optional cellular backup, implementing WebSocket and REST API protocols with TLS/SSL encryption for secure data transfer.

4. **Cloud Services Layer** (Top): Optional cloud components including data aggregation services, analytics engines, cloud-based dashboards, and alert management systems for historical analysis and remote monitoring.

The architecture emphasizes edge-first processing to minimize latency and ensure system operation even during network outages, with cloud services providing enhanced analytics and multi-site management capabilities.

### Figure 2: Detailed Algorithmic Data Flow and Processing Pipeline

![Data Flow Diagram - Detailed algorithmic pipeline showing sensor data acquisition from camera and radar, preprocessing with noise reduction and temporal alignment, detection and tracking with YOLO and SORT algorithms, data fusion using Kalman filtering, analytics generation for traffic statistics, and output distribution to local dashboard and cloud storage with branching paths and processing modules connected by directional arrows.](../archive/traffic_algorithms_data_diagram.png)
*Figure 2: Detailed algorithmic data flow showing specific processing steps, data fusion algorithms, and output generation from sensor inputs to dashboard analytics.*

**Figure 2 Description:**
This detailed data flow diagram drills down into the algorithmic processing pipeline shown at a high level in Figure 1. It specifically illustrates how raw sensor data is transformed into actionable traffic analytics through multiple processing stages:

1. **Sensor Data Acquisition**: Raw video frames from the AI camera (1080p at 30fps) and velocity/range data from the radar sensor (24GHz FMCW) are captured simultaneously with synchronized timestamps.

2. **Preprocessing Stage**: Video frames undergo noise reduction and normalization while radar data is filtered and calibrated. Both data streams are temporally aligned for fusion processing.

3. **Detection and Tracking**: The AI camera runs YOLO-based vehicle detection with bounding box generation, while radar provides precise speed measurements. The SORT algorithm maintains vehicle tracking across frames.

4. **Data Fusion Algorithm**: Kalman filtering combines camera detections with radar measurements to produce high-confidence vehicle events with accurate position, speed, and classification data.

5. **Analytics Generation**: Processed events feed into traffic analytics engines that calculate volume counts, speed statistics, violation detection, and anomaly identification.

6. **Output Distribution**: Results are simultaneously sent to the local dashboard for real-time monitoring, stored in local databases, and queued for cloud synchronization when network connectivity is available.

**Integration Analysis:**
Figure 2 provides the detailed algorithmic implementation of the "Edge Processing" layer shown in Figure 1. While Figure 1 shows the overall system architecture and component relationships, Figure 2 focuses specifically on the data transformation pipeline that occurs within the Raspberry Pi 5 processing unit. Together, these diagrams provide both strategic (Figure 1) and tactical (Figure 2) views of the system design.

**Component Legend:**

- **Rectangular Boxes**: Processing modules and algorithms
- **Circular Nodes**: Data storage and queuing points  
- **Diamond Shapes**: Decision points and conditional logic
- **Arrows**: Data flow direction and dependencies
- **Dashed Lines**: Optional or fallback data paths
- **Bold Borders**: Real-time processing components
- **Color Coding**: Blue (sensor input), Green (processing), Orange (storage), Red (output/alerts)
