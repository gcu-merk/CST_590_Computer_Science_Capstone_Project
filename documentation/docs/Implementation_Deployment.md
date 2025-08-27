# Implementation & Deployment

## Secure Remote HTTPS Access via Tailscale Funnel

If you have enabled Tailscale Funnel, your API is also accessible securely over HTTPS from anywhere using your Tailscale Funnel public URL. With your device hostname set to `edge-traffic-monitoring`, your Funnel URL will look like:
   <https://edge-traffic-monitoring.ts.net/api/health>
or (if your tailnet uses a unique suffix):
   <https://edge-traffic-monitoring.tailXXXXXX.ts.net/api/health>
Replace `XXXXXX` with your actual tailnet suffix if shown in your Funnel output.
**Benefits:**

- End-to-end encrypted HTTPS access to your API
- No need to expose ports or manage certificates manually
- Works from anywhere on the internet (if Funnel is enabled)
**Note:**
If you want to restrict access to only HTTPS via Funnel, ensure your Docker Compose configuration binds the API to `127.0.0.1` only (see above for details).

## Implementation & Deployment Guide

## 🚀 Modern Automated Deployment (2025+)

**This section documents the current, fully automated deployment process using GitHub Actions, Docker, and Tailscale for secure remote access.**

### Overview

The system now uses a CI/CD pipeline for seamless, zero-touch deployment to the Raspberry Pi. All code changes pushed to the `main` branch are automatically built, containerized, and deployed to the Pi. Tailscale enables secure remote access to the dashboard and API from anywhere.

---

### 1. Prerequisites

- Raspberry Pi 4/5 with Raspberry Pi OS 64-bit
- Camera module and (optionally) radar sensor connected
- Docker installed (`curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh`)
- Tailscale installed and authenticated (`curl -fsSL https://tailscale.com/install.sh | sh && sudo tailscale up`)
- Self-hosted GitHub Actions runner registered on the Pi
- Project repository cloned and configured

---

### 2. How Automated Deployment Works

1. **Push code to `main` branch**
2. **GitHub Actions builds and pushes a new Docker image** for ARM64 to Docker Hub
3. **Self-hosted runner on the Pi pulls the new image** and restarts the container using Docker Compose
4. **Container uses `network_mode: host`** so the app is accessible on all Pi interfaces, including Tailscale
5. **Health checks and logs** are reported in the Actions workflow summary

#### CI/CD Branching & Deployment Process (ASCII Diagram)

```text
Feature Branches:           develop:          main:          GitHub Actions:             Raspberry Pi (Edge):

feature/A ──●──┐
               │─▶●───┐
feature/B ──●──┘       │
                       ●───▶●───▶●───▶●──▶ [CI/CD] ──▶ Build & Push Docker Image ──▶ Pull & Deploy ──▶ App Live
                       ^    ^    ^    ^
                       │    │    │    │
                       (merge PRs)

Legend:
● = Commit/Merge Point
[CI/CD] = Automated pipeline triggers on push to main

Process:
1. Develop features in feature branches (feature/A, feature/B, ...)
2. Merge feature branches into develop for integration/testing
3. When ready, merge develop into main for production
4. Push to main triggers CI/CD pipeline:
   - Build & push Docker image
   - Deploy to Raspberry Pi
   - App is live on the edge device
```

---

### 3. Initial Setup (One-Time)

```bash
# On the Raspberry Pi:
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up

# Register the GitHub Actions runner (see repo Settings > Actions > Runners)
# Clone the project repo if not already present
```

---

### 4. Ongoing Deployment (Fully Automated)

1. **Edit code and push to `main` branch**
2. **Wait for GitHub Actions to complete** (see Actions tab for status)
3. **The Pi automatically pulls and runs the new container**
4. **Access the dashboard/API:**
    - Local: `http://<pi-lan-ip>:5000`
    - Remote (Tailscale): `http://<pi-tailscale-ip>:5000`

---

### 5. Docker Compose Configuration (Key Change)

The service now uses host networking for Tailscale access:

```yaml
services:
   traffic-monitor:
      image: gcumerk/cst590-capstone-public:latest
      container_name: traffic-monitoring-edge
      network_mode: host  # Enables Tailscale and LAN access
      privileged: true
      devices:
         - /dev/video0:/dev/video0
         - /dev/ttyACM0:/dev/ttyACM0
         - /dev/gpiomem:/dev/gpiomem
      environment:
         - PYTHONPATH=/app
         - PYTHONUNBUFFERED=1
         - DISPLAY=:0
      volumes:
         - ./data:/app/data
         - ./logs:/app/logs
         - ./config:/app/config
         - /opt/vc:/opt/vc
      healthcheck:
         test: ["CMD", "curl", "-f", "http://localhost:5000/api/health"]
         interval: 30s
         timeout: 10s
         retries: 3
         start_period: 60s
```

---

### 6. Remote Access via Tailscale

- Find your Pi's Tailscale IP: `tailscale ip`
- Access the dashboard from any device on your Tailscale network:
  - `http://<tailscale-ip>:5000`
- No port forwarding or VPN required!

---

### 7. Troubleshooting

- **Check deployment logs:** GitHub Actions > deploy-to-pi workflow
- **Check container status:** `docker ps` and `docker logs traffic-monitoring-edge`
- **Check Tailscale status:** `tailscale status`
- **Health endpoint:** `curl http://localhost:5000/api/health` (on Pi)

---

**Legacy/manual deployment and advanced configuration details are preserved below for reference.**

**Document Version:** 1.0  
**Last Updated:** August 7, 2025  
**Project:** Raspberry Pi 5 Edge ML Traffic Monitoring System  
**Authors:** Implementation Team  

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Installation Steps](#2-installation-steps)
3. [Automated CI/CD Deployment](#3-automated-cicd-deployment)
   - [Pipeline Overview](#31-pipeline-overview)
   - [Branching Strategy](#32-branching-strategy)
   - [Prerequisites for Automated Deployment](#34-prerequisites-for-automated-deployment)
   - [How the Pipeline Works](#35-how-the-pipeline-works)
   - [Manual Deployment Commands](#36-manual-deployment-commands)
   - [Monitoring Deployments](#37-monitoring-deployments)
4. [Integration](#4-integration)
5. [Troubleshooting & Maintenance](#4-troubleshooting--maintenance)

**See also:**

- [Technical Design Document](./Technical_Design.md)
- [User Guide](./User_Guide.md)
- [Project Management Summary](./Project_Management.md)
- [References & Appendices](./References_Appendices.md)

## 1. System Prerequisites

### Hardware Requirements

- Raspberry Pi 5 (16GB RAM recommended)
- Raspberry Pi AI Camera (Sony IMX500)
- OmniPreSense OPS243-C Radar Sensor
- Samsung T7 SSD (or similar), 256GB MicroSD card
- Power supply (PoE or USB-C)
- Ethernet or WiFi network access

### Software Requirements

- Raspberry Pi OS (64-bit, latest)
- Python 3.10+
- Docker (recommended for deployment)
- PostgreSQL (local or remote)
- Required Python packages: TensorFlow, OpenCV, Flask, Flask-SocketIO, NumPy, SQLAlchemy, etc.

### Network & Power Setup

- Ensure stable power and network connectivity at the deployment site
- (Optional) Configure PoE or cellular backup for remote locations

---

## 2. Installation Steps

### 2.1. Raspberry Pi & OS Setup

1. **Flash Raspberry Pi OS (64-bit) to the MicroSD card**

   ```bash
   # Using Raspberry Pi Imager or manual dd command
   sudo dd if=raspios-lite-arm64.img of=/dev/sdX bs=4M status=progress
   ```bash

2. **Boot the Pi and complete initial OS setup**

   ```bash
   # Enable SSH before first boot (optional)
   ```bash
   # Enable SSH before first boot (optional)
   sudo touch /boot/ssh

   # Configure WiFi before first boot (optional)
   sudo nano /boot/wpa_supplicant.conf

   ```bash

   - Use the provided script to disable password-based SSH logins and require SSH keys:
   - [disable_ssh_password.sh](../archive/disable_ssh_password.sh)
   - See the script for instructions and safety notes. Ensure you have SSH key access before running.

3. **Update system packages**

   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install -y git python3-pip python3-venv postgresql postgresql-contrib
   ```bash

4. **Enable required interfaces**

   ```bash
   # Enable Camera, SPI, I2C, and UART
   sudo raspi-config nonint do_camera 0
   sudo raspi-config nonint do_spi 0
   sudo raspi-config nonint do_i2c 0
   sudo raspi-config nonint do_serial 1
   
   # Edit boot config for UART
   echo "enable_uart=1" | sudo tee -a /boot/firmware/config.txt
   echo "dtparam=spi=on" | sudo tee -a /boot/firmware/config.txt
   
   # Reboot to apply changes
   sudo reboot
   ```bash

### 2.2. Hardware Assembly

1. **Connect the AI Camera to the Pi camera port**
   - Use the CSI-2 ribbon cable (included with camera)
   - Ensure proper orientation (blue side toward Ethernet port)

2. **Wire the OPS243-C radar sensor to the Pi GPIO header**

   ```bash
   OPS243-C Pin 9 (5V)    → Pi Pin 2 (5V)
   OPS243-C Pin 10 (GND)  → Pi Pin 6 (GND)
   OPS243-C Pin 6 (RxD)   → Pi Pin 8 (TXD/GPIO14)
   OPS243-C Pin 7 (TxD)   → Pi Pin 10 (RXD/GPIO15)
   ```

3. **Connect SSD for local storage**

   ```bash
   # Format and mount external SSD
   sudo fdisk /dev/sda  # Create partition
   sudo mkfs.ext4 /dev/sda1
   sudo mkdir /mnt/storage
   sudo mount /dev/sda1 /mnt/storage
   
   # Add to fstab for automatic mounting
   echo "/dev/sda1 /mnt/storage ext4 defaults 0 2" | sudo tee -a /etc/fstab
   ```

4. **Verify hardware connections**

   ```bash
   # Test camera
   libcamera-hello --preview=none --timeout=5000
   
   # Test UART (should show radar sensor data)
   sudo cat /dev/serial0
   
   # Check USB devices
   lsusb
   ```

### 2.3. Python Environment & Dependencies

1. **Create virtual environment**

   ```bash
   python3 -m venv /opt/traffic-monitor
   source /opt/traffic-monitor/bin/activate
   ```

2. **Install required packages**

   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   
   # Core dependencies
   pip install tensorflow opencv-python flask flask-socketio
   pip install psycopg2-binary sqlalchemy numpy pandas
   pip install pyserial RPi.GPIO picamera2
   ```

3. **PostgreSQL Database Setup**

   ```bash
   # Create database user and database
   sudo -u postgres createuser --interactive traffic_user
   sudo -u postgres createdb traffic_monitor
   
   # Set password for database user
   sudo -u postgres psql -c "ALTER USER traffic_user PASSWORD 'your_secure_password';"
   
   # Grant privileges
   sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE traffic_monitor TO traffic_user;"
   ```

### 2.4. Configuration Templates

#### Database Configuration (`config/database.conf`)

```ini
[database]
host = localhost
port = 5432
database = traffic_monitor
username = traffic_user
password = your_secure_password
pool_size = 10

```

---

## Security Hardening

System security is critical for any edge device deployment. Follow these best practices to reduce risk and ensure only authorized access:

- **Disable SSH password authentication:**
  - Use SSH keys for all remote access. Run the provided script to disable password logins: [disable_ssh_password.sh](../archive/disable_ssh_password.sh)
  - See the script for instructions and safety notes. Always test SSH key access before logging out.
- **Change all default passwords** (OS, database, dashboard, etc.) immediately after setup.
- **Keep the system updated:**
  - Regularly run `sudo apt update && sudo apt upgrade -y` to patch vulnerabilities.
- **Enable the firewall:**
  - Use `sudo ufw enable` and allow only required ports (e.g., 22 for SSH, 5000 for API/dashboard).
- **Limit user accounts:**
  - Only create accounts for necessary users. Remove or disable unused accounts.
- **Monitor logs and enable audit tools:**
  - Regularly check `/var/log/auth.log`, `/var/log/syslog`, and use tools like `fail2ban` for intrusion prevention.
- **Backup configuration and data regularly.**
- **Review and follow additional security recommendations** in the Technical Design and Project Management documents.

For more details on SSH hardening, see the [OpenSSH Manual](https://man.openbsd.org/sshd_config).

## 5. Future Work & Clarifications

### Future Work

- **Automated Deployment Scripts:** Expand and refine scripts for one-click setup, including cloud and edge deployments.
- **Containerization Enhancements:** Improve Docker Compose and multi-architecture support for easier deployment on various edge devices.
- **Remote Update Mechanisms:** Add secure, over-the-air update capabilities for field devices.
- **Monitoring & Logging:** Integrate advanced monitoring, alerting, and log aggregation tools.
- **Configuration UI:** Develop a user-friendly web interface for system configuration and diagnostics.

### Contradictions & Clarifications

- The GitHub repository may reference additional deployment automation or CI/CD features not fully implemented in the current scripts. Document and clarify any differences in future updates.
- Some troubleshooting and maintenance steps are described as manual; automation is a future goal.

### Repository Reference

- For deployment scripts, Dockerfiles, and configuration templates, see: [CST_590_Computer_Science_Capstone_Project GitHub](https://github.com/gcu-merk/CST_590_Computer_Science_Capstone_Project)

#### API Configuration (`config/api.conf`)

```ini
[api]
host = 0.0.0.0
port = 5000
debug = false
secret_key = your_secret_key_here
jwt_secret = your_jwt_secret_here

[security]
api_rate_limit = 100
enable_cors = true
allowed_origins = http://localhost:3000,https://yourdomain.com
```

#### Radar Sensor Configuration (`config/radar.conf`)

```ini
[radar]
port = /dev/serial0
baudrate = 9600
timeout = 1.0
buffer_size = 1024

[detection]
min_speed_threshold = 5.0
max_speed_threshold = 100.0
range_filter_min = 1.0
range_filter_max = 200.0
```

---

## 3. Automated CI/CD Deployment

The system includes an automated CI/CD pipeline using GitHub Actions for containerized deployment with Docker. This provides consistent, reliable deployments to your Raspberry Pi.

### 3.1. Pipeline Overview

The CI/CD pipeline consists of two GitHub Actions workflows:

1. **Build and Push Docker Image** - Builds a Docker image and pushes it to Docker Hub
2. **Deploy to Raspberry Pi** - Pulls the latest image and updates the running container on the Pi

### 3.2. Branching Strategy

The project uses a **Feature Branch + Main Strategy** for organized development and safe production deployments:

#### Branch Structure

```text
┌─────────────────────────────────────────────────────────────────┐
│                     BRANCHING STRATEGY                         │
└─────────────────────────────────────────────────────────────────┘

main        ──●────●────────●────────●──► 🚀 DEPLOY TO PI
              │    │        │        │
              │    │        │        │
develop    ───┼────●────●───●────────┼──► 🔨 BUILD ONLY
              │    │    │   │        │
              │    │    │   │        │
feature/A  ───●────●────●───┘        │    🧪 BUILD & TEST
              │                      │
feature/B  ───●──────────────────────●    🧪 BUILD & TEST

Legend:
● = Commit/Merge Point
🚀 = Automatic Deployment to Raspberry Pi
🔨 = Build & Test (No Deployment)
🧪 = Feature Development & Testing
```

- **`main`** - Production-ready code that automatically deploys to the Raspberry Pi
- **`develop`** - Integration branch for testing features together
- **Feature branches** - Individual features (e.g., `feature/camera-integration`, `feature/speed-detection`)

#### Workflow Process

```text
┌─────────────────────────────────────────────────────────────────┐
│                    DEVELOPMENT WORKFLOW                        │
└─────────────────────────────────────────────────────────────────┘

1. Feature Development:
   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
   │   develop   │───►│ feature/new │───►│    P.R.     │
   │   (start)   │    │ (create)    │    │ (develop)   │
   └─────────────┘    └─────────────┘    └─────────────┘

2. Integration Testing:
   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
   │   feature   │───►│   develop   │───►│   🔨 BUILD  │
   │  (merge)    │    │ (integrate) │    │ (no deploy) │
   └─────────────┘    └─────────────┘    └─────────────┘

3. Production Release:
   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
   │   develop   │───►│    main     │───►│ 🚀 DEPLOY   │
   │  (merge)    │    │ (production)│    │ (to Pi)     │
   └─────────────┘    └─────────────┘    └─────────────┘
```

1. **Feature Development**:

   ```bash
   # Create feature branch from develop
   git checkout develop
   git checkout -b feature/new-feature
   # Make changes and commit
   git push -u origin feature/new-feature
   # Create Pull Request: feature/new-feature → develop
   ```

2. **Integration Testing**:
   - Features are merged into `develop` via Pull Requests
   - `develop` branch triggers builds but **does not deploy** to production
   - Multiple features can be tested together in `develop`

3. **Production Release**:

   ```bash
   # When ready for production
   git checkout main
   git merge develop
   git push  # This triggers deployment to Raspberry Pi
   ```

#### CI/CD Pipeline Architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│                    CI/CD PIPELINE FLOW                         │
└─────────────────────────────────────────────────────────────────┘

GitHub Repository                 Docker Hub              Raspberry Pi
┌─────────────────┐               ┌─────────────┐         ┌─────────────┐
│                 │               │             │         │             │
│  git push main  │──────────────►│             │         │             │
│                 │               │             │         │             │
└─────────────────┘               └─────────────┘         └─────────────┘
         │                                │                       ▲
         ▼                                │                       │
┌─────────────────┐               ┌─────────────┐         ┌─────────────┐
│  GitHub Actions │               │             │         │ Self-hosted │
│                 │               │  Container  │         │   Runner    │
│ 1. Build ARM64  │──────────────►│   Image     │────────►│             │
│ 2. Push Image   │               │  (latest)   │         │             │
│                 │               │             │         │             │
└─────────────────┘               └─────────────┘         └─────────────┘
                                                                   │
                                                                   ▼
                                                          ┌─────────────┐
                                                          │             │
                                                          │docker pull  │
                                                          │docker up -d │
                                                          │             │
                                                          └─────────────┘

Flow:
1. Developer pushes to 'main' branch
2. GitHub Actions triggers build workflow
3. ARM64 Docker image built and pushed to Docker Hub  
4. Deploy workflow triggers on self-hosted runner (Pi)
5. Pi pulls latest image and restarts container
```

#### CI/CD Behavior by Branch

| Branch | Build | Test | Deploy to Pi |
|--------|-------|------|--------------|
| `main` | ✅ | ✅ | ✅ |
| `develop` | ✅ | ✅ | ❌ |
| Feature branches | ✅ | ✅ | ❌ |

**Safety Features**:

- Only `main` branch deploys to production hardware
- Failed builds prevent deployment
- Self-hosted runner ensures secure, local deployment

#### Quick Reference Commands

```bash
# Current branch status
git branch -a

# Switch between branches
git checkout main        # Production branch
git checkout develop     # Integration branch

# Create new feature branch
git checkout develop
git checkout -b feature/your-feature-name

# Merge workflow for production release
git checkout main
git merge develop
git push  # Triggers deployment to Pi

# Check deployment status
# Visit: https://github.com/gcu-merk/CST_590_Computer_Science_Capstone_Project/actions
```

### 3.3. Prerequisites for Automated Deployment

### 3.4. Prerequisites for Automated Deployment

#### Self-Hosted Runner Architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│                 SELF-HOSTED RUNNER SETUP                       │
└─────────────────────────────────────────────────────────────────┘

GitHub Cloud                              Raspberry Pi (Local Network)
┌─────────────────┐                      ┌─────────────────────────────┐
│                 │                      │                             │
│ GitHub Actions  │                      │     📱 Self-hosted Runner   │
│                 │                      │                             │
│  Workflow:      │       HTTPS          │  ┌─────────────────────────┐ │
│  Deploy to Pi   │◄────Secure Tunnel───►│  │  ./run.sh               │ │
│                 │                      │  │  Listening for Jobs...  │ │
│  Status: ✅     │                      │  └─────────────────────────┘ │
└─────────────────┘                      │              │              │
                                         │              ▼              │
                                         │  ┌─────────────────────────┐ │
                                         │  │  Docker Engine          │ │
                                         │  │                         │ │
         Internet/Cloud                  │  │  docker compose pull    │ │
    ┌─────────────────────┐             │  │  docker compose up -d   │ │
    │                     │             │  │                         │ │
    │     Docker Hub      │◄────────────┤  └─────────────────────────┘ │
    │                     │             │                             │
    │ gcumerk/cst590-     │             │  🏠 Home Network           │
    │ capstone:latest     │             │  IP: 100.121.231.16        │
    └─────────────────────┘             └─────────────────────────────┘

Benefits:
✅ No SSH connectivity issues
✅ Runs locally on target hardware  
✅ Secure GitHub authentication
✅ Direct hardware access
```

#### Docker Hub Setup

1. Create a Docker Hub account at <https://hub.docker.com>
2. Create a new repository: `<your-username>/cst-590-computer-science-capstone-project`
3. Generate an access token with "Read, Write, Delete" permissions:
   - Go to Account Settings → Security → New Access Token
   - Save the token securely

#### GitHub Secrets Configuration

Add the following secrets to your GitHub repository (Settings → Secrets and variables → Actions):

- `DOCKERHUB_USERNAME`: Your Docker Hub username
- `DOCKERHUB_TOKEN`: Your Docker Hub access token
- `PI_SSH_KEY`: Your SSH private key for connecting to the Raspberry Pi

#### Raspberry Pi Preparation

1. Install Docker on your Raspberry Pi:

   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker $USER
   newgrp docker
   ```

2. Create the project directory:

   ```bash
   mkdir -p /mnt/storage/cst_590_computer_science_capstone_project
   cd /mnt/storage/cst_590_computer_science_capstone_project
   ```

3. Create a `docker-compose.yml` file:

   ```yaml
   services:
     app:
       image: <your-dockerhub-username>/cst-590-computer-science-capstone-project:latest
       restart: unless-stopped
       ports:
         - "5000:5000"
       volumes:
         - /dev:/dev
         - ./data:/app/data
         - ./logs:/app/logs
       privileged: true
       environment:
         - PYTHONUNBUFFERED=1
   ```

### 3.5. How the Pipeline Works

#### Automatic Deployment Process

1. **Code Changes**: Push code changes to the `main` branch
2. **Build Stage**: GitHub Actions builds a Docker image for ARM64 architecture
3. **Push Stage**: The image is tagged and pushed to your Docker Hub repository
4. **Deploy Stage**: Upon successful build, the deploy workflow:
   - SSHs into your Raspberry Pi
   - Pulls the latest Docker image
   - Restarts the container with the new image
   - Installs Pi-specific packages (picamera2, gpiozero, RPi.GPIO) in the running container

#### Package Management Strategy

The pipeline uses a two-stage package installation approach:

- **Cloud Build**: Installs general packages compatible with cloud build environments
- **Pi Runtime**: Installs Pi-specific hardware packages directly on the running container

### 3.6. Manual Deployment Commands

If you need to manually deploy or troubleshoot:

```bash
# On your Raspberry Pi
cd /mnt/storage/cst_590_computer_science_capstone_project

# Pull latest image and restart
docker compose pull
docker compose up -d

# Install Pi-specific packages (if needed)
docker exec <container_name> pip install picamera2 gpiozero RPi.GPIO gpustat

# Check container status
docker ps
docker logs <container_name>
```

### 3.7. Monitoring Deployments

- **GitHub Actions**: Monitor workflow runs in your repository's Actions tab
- **Docker Hub**: Check image push status and download counts
- **Raspberry Pi**: Use `docker ps` and `docker logs` to monitor container health

---

## 4. Integration

1. **Clone project repository**

   ```bash
   cd /opt
   git clone https://github.com/your-org/traffic-monitor.git
   cd traffic-monitor
   ```

2. **Configure systemd services**

   ```bash
   # Copy service files
   sudo cp scripts/traffic-monitor-api.service /etc/systemd/system/
   sudo cp scripts/traffic-monitor-processor.service /etc/systemd/system/
   
   # Enable and start services
   sudo systemctl daemon-reload
   sudo systemctl enable traffic-monitor-api
   sudo systemctl enable traffic-monitor-processor
   sudo systemctl start traffic-monitor-api
   sudo systemctl start traffic-monitor-processor
   ```

3. **Verify deployment**

   ```bash
   # Check service status
   sudo systemctl status traffic-monitor-api
   sudo systemctl status traffic-monitor-processor
   
   # Test API endpoint
   curl http://localhost:5000/api/health
   
   # View logs
   sudo journalctl -u traffic-monitor-api -f
   ```

4. Install Python 3.10+ if not already present
5. Create and activate a virtual environment:

   ```bash
   python3 -m venv ~/traffic-monitor/venv
   source ~/traffic-monitor/venv/bin/activate
   ```

6. Install required Python packages:

   ```bash
   pip install tensorflow opencv-python flask flask-socketio numpy sqlalchemy psycopg2-binary
   ```

7. Install PostgreSQL (if local):

   ```bash
   sudo apt install postgresql postgresql-contrib
   ```

8. Create database and user:

   ```sql
   CREATE DATABASE traffic_monitor;
   CREATE USER tm_user WITH PASSWORD 'yourpassword';
   GRANT ALL PRIVILEGES ON DATABASE traffic_monitor TO tm_user;
   ```

9. Update backend configuration with database credentials

### 2.6. Manual Application Deployment

1. Clone or copy the project code to the Pi
2. (Recommended) Build and run services using Docker Compose
3. Alternatively, run backend and dashboard manually from the virtual environment
4. Start the Flask API and dashboard services

---

## 3. Integration

### 3.1. Hardware-Software Integration

- Ensure all hardware is connected as per the GPIO pin mapping in the Technical Design Document.
- Enable UART on the Raspberry Pi (see radar sensor setup instructions).
- Verify camera functionality using `libcamera` or `picamera2` test commands.

### 3.2. Database & API Configuration

- Update backend configuration files with correct PostgreSQL credentials and host.
- Run database migration scripts (if provided) to create tables.
- Test database connectivity from the backend using a simple script or API call.

### 3.3. Service Startup & Verification

- Start backend services (Flask API, WebSocket server, ML pipeline).
- Access the Edge UI dashboard in a browser (default: http://[PI_IP]:5000 or similar).
- Confirm real-time data is displayed and events are logged in the database.

---

## 4. Troubleshooting & Maintenance

### 4.1. Common Issues & Solutions

#### Camera Issues

- **No camera detected:**

  ```bash
  # Check camera detection
  libcamera-hello --list-cameras
  
  # Verify ribbon cable connection and enable camera
  sudo raspi-config nonint do_camera 0
  
  # Check boot config
  grep camera /boot/firmware/config.txt
  ```

- **Poor image quality:**

  ```bash
  # Test different camera settings
  libcamera-still -o test.jpg --width 1920 --height 1080
  
  # Check lens focus and clean lens
  # Verify adequate lighting conditions
  ```

#### Radar Sensor Issues

- **No radar data:**

  ```bash
  # Verify UART is enabled
  sudo raspi-config nonint do_serial 1
  
  # Check UART communication
  sudo cat /dev/serial0
  
  # Test with minicom
  sudo apt install minicom
  sudo minicom -D /dev/serial0 -b 9600
  
  # Check power and connections
  gpio readall  # Verify GPIO states
  ```

#### Database Issues

- **Database connection errors:**

  ```bash
  # Check PostgreSQL status
  sudo systemctl status postgresql
  
  # Test connection
  psql -h localhost -U traffic_user -d traffic_monitor
  
  # Check logs
  sudo tail -f /var/log/postgresql/postgresql-*.log
  ```

- **Database performance issues:**

  ```sql
  -- Check database size and table statistics
  SELECT schemaname,tablename,attname,n_distinct,correlation 
  FROM pg_stats WHERE tablename = 'vehicleevent';
  
  -- Vacuum and analyze tables
  VACUUM ANALYZE vehicleevent;
  VACUUM ANALYZE radarreading;
  ```

#### Network and API Issues

- **API not responding:**

  ```bash
  # Check service status
  sudo systemctl status traffic-monitor-api
  
  # Check port binding
  sudo netstat -tlnp | grep :5000
  
  # Test local connectivity
  curl -v http://localhost:5000/api/health
  ```

- **Dashboard not loading:**

  ```bash
  # Check firewall rules
  sudo ufw status
  
  # Verify CORS settings
  grep cors config/api.conf
  
  # Check browser console for JavaScript errors
  ```

### 4.2. Backup & Recovery Procedures

#### Database Backup

```bash
#!/bin/bash
# Create automated backup script: /opt/scripts/backup_database.sh

BACKUP_DIR="/mnt/storage/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="traffic_monitor_backup_${DATE}.sql"

# Create backup directory
mkdir -p $BACKUP_DIR

# Perform database backup
pg_dump -h localhost -U traffic_user traffic_monitor > $BACKUP_DIR/$BACKUP_FILE

# Compress backup
gzip $BACKUP_DIR/$BACKUP_FILE

# Remove backups older than 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE.gz"
```

#### System Configuration Backup

```bash
#!/bin/bash
# System backup script: /opt/scripts/backup_system.sh

BACKUP_DIR="/mnt/storage/backups"
DATE=$(date +%Y%m%d_%H%M%S)
CONFIG_BACKUP="system_config_${DATE}.tar.gz"

# Backup important configuration files
tar -czf $BACKUP_DIR/$CONFIG_BACKUP \
    /opt/traffic-monitor/config/ \
    /etc/systemd/system/traffic-monitor*.service \
    /boot/firmware/config.txt \
    /etc/fstab

echo "Configuration backup completed: $CONFIG_BACKUP"
```

#### Recovery Procedures

```bash
# Database recovery
gunzip -c /mnt/storage/backups/traffic_monitor_backup_YYYYMMDD_HHMMSS.sql.gz | \
    psql -h localhost -U traffic_user traffic_monitor

# Configuration recovery
tar -xzf /mnt/storage/backups/system_config_YYYYMMDD_HHMMSS.tar.gz -C /

# Service restart after recovery
sudo systemctl daemon-reload
sudo systemctl restart traffic-monitor-api
sudo systemctl restart traffic-monitor-processor
```

### 4.3. Maintenance Schedule

#### Daily Tasks (Automated)

- Database backup
- Log rotation
- System health monitoring
- Storage usage check

#### Weekly Tasks

```bash
# System updates (can be automated with caution)
sudo apt update && sudo apt list --upgradable
sudo apt upgrade -y

# Log analysis
sudo journalctl --since "1 week ago" | grep ERROR
sudo logrotate /etc/logrotate.conf

# Performance monitoring
iostat -x 1 5  # Check disk I/O
top -b -n 1 | head -20  # Check CPU/memory usage
```

#### Monthly Tasks

- Full system backup
- Security audit
- Performance optimization
- Hardware inspection

### 4.4. Monitoring & Alerting

#### System Health Scripts

```bash
#!/bin/bash
# Health check script: /opt/scripts/health_check.sh

# Check services
systemctl is-active --quiet traffic-monitor-api || echo "API service down"
systemctl is-active --quiet traffic-monitor-processor || echo "Processor service down"

# Check disk space
DISK_USAGE=$(df /mnt/storage | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "Warning: Disk usage at ${DISK_USAGE}%"
fi

# Check temperature
TEMP=$(vcgencmd measure_temp | cut -d= -f2 | cut -d\' -f1)
if [ ${TEMP%.*} -gt 70 ]; then
    echo "Warning: CPU temperature at ${TEMP}°C"
fi
```

### 4.5. Performance Tuning

#### Database Optimization

```sql
-- PostgreSQL performance tuning
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
SELECT pg_reload_conf();
```

#### System Optimization

```bash
# Increase file descriptor limits
echo "* soft nofile 65535" | sudo tee -a /etc/security/limits.conf
echo "* hard nofile 65535" | sudo tee -a /etc/security/limits.conf

# Optimize network settings
echo "net.core.rmem_max = 16777216" | sudo tee -a /etc/sysctl.conf
echo "net.core.wmem_max = 16777216" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```
