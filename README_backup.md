# CST_590_Computer_Science_Capstone_Project

Raspberry Pi 5 Edge ML Traffic Monitoring System with automated CI/CD pipeline and intelligent development tools.

## Raspberry Pi 5 Edge ML Traffic Monitoring System

## Overview

This project is a comprehensive, edge-based traffic monitoring solution that leverages a Raspberry Pi 5, AI-enabled camera, and radar sensor for real-time vehicle detection, speed measurement, and traffic analytics. The system processes data locally to reduce bandwidth, enhance privacy, and enable rapid response to traffic events.

**Key Features:**

* **Real-time AI-powered vehicle detection** using Raspberry Pi AI Camera (Sony IMX500)
* **Accurate speed measurement** with OmniPreSense OPS243-C radar sensor
* **Data fusion algorithms** for enhanced detection accuracy
* **Local web dashboard** for live monitoring and configuration
* **REST and WebSocket APIs** for integration and automation
* **Automated CI/CD pipeline** with Docker containerization
* **Intelligent development tools** for streamlined workflow

## 🚀 Quick Start

### For End Users

```bash
# Access the dashboard (replace with your Pi's IP)
http://192.168.1.100:5000
```

### For Developers

```bash
# Clone repository
git clone https://github.com/gcu-merk/CST_590_Computer_Science_Capstone_Project.git
cd CST_590_Computer_Science_Capstone_Project

# Deploy to Raspberry Pi
bash scripts/deploy-to-pi.sh

# Use intelligent Git workflow
smart-push -b "feature/new-enhancement"
```

## 🛠️ Development Tools

### Smart Push Tool

Intelligent Git workflow automation with automatic branch creation and commit message generation:

```bash
smart-push                           # Auto-commit with intelligent message
smart-push -dry                      # Preview changes
smart-push -b "feature/new-feature"  # Create custom branch
smart-push -m "feat: add new API"    # Custom commit message
```

### Branch Cleanup Tool

Automated cleanup of merged Git branches:

```bash
branch-cleanup      # Interactive cleanup
branch-cleanup -dry # Preview cleanup
```

### Deployment Automation

```bash
# Raspberry Pi deployment
bash scripts/deploy-to-pi.sh

# Troubleshooting and diagnostics
bash scripts/pi-troubleshoot.sh
```

## 🏗️ Technical Implementation

### Architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│                    SYSTEM ARCHITECTURE                         │
└─────────────────────────────────────────────────────────────────┘

Edge Device (Raspberry Pi 5)
┌─────────────────────────────┐
│  ┌─────────────────────────┐│
│  │     ML Models           ││  ┌─────────────────────┐
│  │  - Vehicle Detection    ││  │   Sensors           │
│  │  - Speed Calculation    ││  │  - AI Camera        │
│  │  - Data Fusion          ││  │  - Radar Sensor     │
│  └─────────────────────────┘│  │  - GPIO Interface   │
│  ┌─────────────────────────┐│  └─────────────────────┘
│  │     APIs & UI           ││
│  │  - REST API             ││  ┌─────────────────────┐
│  │  - WebSocket API        ││  │   Storage           │
│  │  - Web Dashboard        ││  │  - Local Database   │
│  │  - Real-time Streams    ││  │  - Event Logs       │
│  └─────────────────────────┘│  │  - Configuration    │
└─────────────────────────────┘  └─────────────────────┘
```

### Hardware Components

* **Raspberry Pi 5** (16GB RAM recommended)
* **Raspberry Pi AI Camera** (Sony IMX500) for ML-powered detection
* **OmniPreSense OPS243-C Radar Sensor** for precise speed measurement
* **Samsung T7 SSD** for fast data storage
* **Power and Network** connectivity

### Software Stack

* **Edge Processing**: Python 3.10+, TensorFlow, OpenCV
* **APIs**: Flask, Flask-SocketIO for real-time communication
* **Database**: PostgreSQL for data persistence
* **Containerization**: Docker with ARM64 support
* **CI/CD**: GitHub Actions with automated deployment

## 📦 Installation & Deployment

### Automated Deployment (Recommended)

```bash
# 1. Clone repository
git clone https://github.com/gcu-merk/CST_590_Computer_Science_Capstone_Project.git
cd CST_590_Computer_Science_Capstone_Project

# 2. Deploy to Raspberry Pi
bash scripts/deploy-to-pi.sh

# 3. Verify deployment
bash scripts/pi-troubleshoot.sh
```

### Manual Docker Deployment

```bash
# Create deployment directory
mkdir -p ~/traffic-monitor-deploy
cd ~/traffic-monitor-deploy

# Download configuration
wget https://raw.githubusercontent.com/gcu-merk/CST_590_Computer_Science_Capstone_Project/main/docker-compose.yml

# Start services
docker-compose up -d
```

### Development Setup

```bash
# Install development tools
pip install -r requirements.txt

# Set up pre-commit hooks
pre-commit install

# Start development server
python main_edge_app.py
```

## 🔧 CI/CD Pipeline

### Automated Workflows

The project includes a comprehensive CI/CD pipeline with GitHub Actions:

#### Feature Branch Workflow

```yaml
# Triggers on pull requests and feature branches
- Build validation
- Unit tests
- Docker image building
- Integration testing
```

#### Main Branch Deployment

```yaml
# Triggers on main branch commits
- Production build
- ARM64 Docker images
- Automated deployment to Pi
- Health checks
```

### Pipeline Features

* **Multi-architecture builds** (AMD64, ARM64)
* **Automatic Docker Hub publishing**
* **Branch-based deployment strategies**
* **Comprehensive testing and validation**

## 📊 API Documentation

### REST API Endpoints

```bash
# Vehicle Detection
GET /api/vehicles          # List detected vehicles
POST /api/vehicles/search  # Search with filters

# Speed Monitoring
GET /api/speed/current     # Current speed readings
GET /api/speed/history     # Historical speed data

# System Health
GET /api/health           # System status
GET /api/metrics          # Performance metrics
```

### WebSocket Events

```javascript
// Real-time vehicle detection
socket.on('vehicle_detected', (data) => {
  console.log('Vehicle:', data.vehicle_id, 'Speed:', data.speed);
});

// Speed violations
socket.on('speed_violation', (data) => {
  console.log('Violation detected:', data);
});
```

## 🏃‍♂️ Performance & Monitoring

### System Capabilities

* **Detection Rate**: 95%+ accuracy at 30 FPS
* **Speed Accuracy**: ±2 mph precision
* **Latency**: <100ms detection to alert
* **Storage**: Configurable data retention
* **Throughput**: 1000+ events per hour

### Monitoring Dashboard

Access the web dashboard at `http://[pi-ip]:5000`:

* **Live Video Feed** with detection overlay
* **Real-time Metrics** and statistics
* **Historical Data** visualization
* **System Configuration** interface
* **Alert Management** and notifications

## 🔍 Troubleshooting

### Common Issues

#### Deployment Problems

```bash
# Check system status
bash scripts/pi-troubleshoot.sh

# Restart services
docker-compose down && docker-compose up -d

# Check logs
docker-compose logs -f
```

#### Performance Issues

```bash
# Monitor resources
htop
docker stats

# Check disk space
df -h

# GPU memory (if using)
vcgencmd get_mem gpu
```

#### Camera/Sensor Issues

```bash
# Test camera
libcamera-hello --timeout 5000

# Check GPIO connections
gpio readall

# Verify sensor communication
python -c "import serial; print('UART OK')"
```

## 📚 Documentation

### Complete Documentation

* **[Implementation & Deployment Guide](documentation/docs/Implementation_Deployment.md)** - Comprehensive technical implementation
* **[User Guide](documentation/docs/User_Guide.md)** - End-user documentation
* **[Automation Tools Guide](documentation/docs/Automation_Tools.md)** - Development workflow tools
* **[API Documentation](documentation/docs/)** - Complete API reference

### Development Resources

* **Architecture Diagrams** - System design and data flow
* **Hardware Setup** - Component integration guides
* **Configuration Examples** - Sample configurations
* **Troubleshooting Guides** - Common issues and solutions

## 🤝 Contributing

### Development Workflow

1. **Fork** the repository
2. **Create feature branch**: `smart-push -b "feature/new-feature"`
3. **Make changes** with intelligent commit messages
4. **Test thoroughly** using the CI/CD pipeline
5. **Submit pull request** with comprehensive description

### Code Standards

* **Python**: PEP 8 compliance with Black formatting
* **JavaScript**: ESLint configuration provided
* **Docker**: Multi-stage builds for optimization
* **Git**: Conventional commit messages

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

* **Michael Garcia** - Project Lead and Developer
* **Dr. Ahmed Alwakeel** - Faculty Advisor

## 🙏 Acknowledgments

* **OmniPreSense** for radar sensor documentation
* **Raspberry Pi Foundation** for AI camera support
* **Open Source Community** for libraries and tools
* **Gulf Coast University** Computer Science Department

---

**Project Status**: ✅ Production Ready | **Version**: 2.0 | **Last Updated**: December 2024

**Future Work:**

* Improve detection accuracy in challenging lighting conditions.
* Explore advanced deep learning techniques for better performance.
* Integrate with cloud-based platforms for remote monitoring and analysis.
* Develop a user-friendly interface for system configuration and data visualization.

**Contributing:**

We welcome contributions to this project after August 2025. Please feel free to fork the repository and submit pull requests.


## Repo Structure

```text
CST_590_Computer_Science_Capstone_Project/
├── .gitignore
├── .vs/
├── LICENSE
├── README.md
├── data-collection/
│   ├── data-consolidator/
│   │   ├── data_consolidator.py
│   │   ├── requirements.txt
│   │   └── tests/
│   │       └── test_data_consolidator.py
│   ├── data-persister/
│   │   ├── data_persister.py
│   │   ├── requirements.txt
│   │   └── tests/
│   │       └── test_data_persister.py
│   ├── license-plate-data-collection/
│   │   ├── license_plate_data_collection.py
│   │   ├── requirements.txt
│   │   └── tests/
│   │       └── test_license_plate_data_collection.py
│   ├── speed-data-collection/
│   │   ├── speed_data_collection.py
│   │   ├── requirements.txt
│   │   └── tests/
│   │       └── test_speed_data_collection.py
│   ├── stop-sign-data-collection/
│   │   ├── stop_sign_data_collection.py
│   │   ├── requirements.txt
│   │   └── tests/
│   │       └── test_stop_sign_data_collection.py
│   ├── utils/
│   │   ├── utils.py
│   │   ├── requirements.txt
│   │   └── tests/
│   │       └── test_utils.py
├── database/
│   ├── backups/
│   │   └── backup_20241203.sql
│   ├── init_db.sql/
│   ├── README.md/
│   ├── schema/
│   │   └── create_tables.sql
│   ├── scripts/
│   │   └── data_import.sh
├── documentation/
│   ├── archive/
│   ├── docs/
│   └── README.md
├── mobile/
│   ├── android/
│   ├── ios/
│   ├── lib/
│   │   ├── main.dart
│   │   ├── views/
│   │   │   ├── camera_view.dart
│   │   │   └── logs_view.dart
│   │   └── tests/
│   │       ├── test_main.dart
│   │       └── test_views.dart
│   ├── pubspec.yaml
│   └── README.md/
├── webserver/
│   ├── package.json/
│   ├── README.md/
│   └── src/
│       ├── app.module.ts
│       ├── controllers/
│       │   ├── camera.controller.ts
│       │   └── data.controller.ts
│       ├── database/
│       │   ├── database.module.ts
│       │   └── database.service.ts
│       ├── main.ts
│       ├── services/
│       │   ├── camera.service.ts
│       │   └── data.service.ts
│       └── tests/
│           └── test_app.module.ts
├── website/
│   ├── package.json/
│   ├── public/
│   │   └── index.html
│   ├── README.md/
│   └── src/
│       ├── App.js
│       ├── components/
│       │   ├── CameraView.js
│       │   └── LogsView.js
│       └── tests/
│           ├── test_app.js
│           └── test_components.js
```#   C I / C D   P i p e l i n e   T e s t   -   0 8 / 2 2 / 2 0 2 5   2 2 : 1 7 : 3 4 
 
 