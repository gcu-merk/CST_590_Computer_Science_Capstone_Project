# Raspberry Pi Deployment Guide

This guide provides tools and instructions for deploying the traffic monitoring system to a Raspberry Pi.

## 🛠️ Available Tools

### 1. Automated GitHub Actions Deployment

- **File**: `.github/workflows/deploy-to-pi.yml`
- **Trigger**: Automatic after successful Docker build on main branch
- **Requirements**: Self-hosted GitHub runner on the Pi

### 2. Manual Deployment Script

- **File**: `scripts/deploy-to-pi.sh`
- **Usage**: Manual deployment and testing
- **Command**: `bash scripts/deploy-to-pi.sh`

### 3. Troubleshooting Script

- **File**: `scripts/pi-troubleshoot.sh`
- **Usage**: Diagnose deployment issues
- **Command**: `bash scripts/pi-troubleshoot.sh`

## 🚀 Quick Start

### Prerequisites

1. Raspberry Pi 4 or 5 with Raspberry Pi OS
2. Docker and Docker Compose installed
3. Internet connection
4. Camera and sensors connected (optional for testing)

### Option 1: Manual Deployment

```bash
# Clone the repository
git clone https://github.com/gcu-merk/CST_590_Computer_Science_Capstone_Project.git
cd CST_590_Computer_Science_Capstone_Project

# Make scripts executable
chmod +x scripts/deploy-to-pi.sh scripts/pi-troubleshoot.sh

# Run deployment
bash scripts/deploy-to-pi.sh
```

### Option 2: Direct Docker Compose

```bash
# Create deployment directory
mkdir -p ~/traffic-monitor-deploy
cd ~/traffic-monitor-deploy

# Download docker-compose.yml
wget https://raw.githubusercontent.com/gcu-merk/CST_590_Computer_Science_Capstone_Project/main/docker-compose.yml

# Create required directories
mkdir -p data logs config

# Deploy
docker-compose up -d
```

## 🔧 Configuration

### Environment Setup

The deployment creates the following structure:

```text
~/traffic-monitor-deploy/
├── docker-compose.yml
├── data/               # Persistent data storage
├── logs/               # Application logs
└── config/             # Configuration files
```

### Hardware Requirements

- **Camera**: USB camera or Pi Camera module
- **GPIO Access**: For sensor connections
- **UART Devices**: For radar sensor communication
- **Storage**: Minimum 8GB SD card (16GB+ recommended)

## 📊 Monitoring and Management

### Check Deployment Status

```bash
# View container status
cd ~/traffic-monitor-deploy
docker-compose ps

# View logs
docker-compose logs -f

# Check API health
curl http://localhost:5000/api/health
```

### Troubleshooting

```bash
# Run diagnostics
bash scripts/pi-troubleshoot.sh

# View detailed logs
cd ~/traffic-monitor-deploy
docker-compose logs traffic-monitor

# Restart services
docker-compose restart

# Clean deployment
docker-compose down
docker-compose up -d
```

## 🔄 Updates and Maintenance

### Update to Latest Version
```bash
cd ~/traffic-monitor-deploy

# Pull latest image
docker-compose pull

# Restart with new image
docker-compose up -d
```

### Cleanup Old Resources
```bash
# Remove unused Docker resources
docker system prune -f

# Remove old images
docker image prune -f
```

## 🚨 Troubleshooting Common Issues

### Issue 1: Container Won't Start
```bash
# Check logs
docker-compose logs traffic-monitor

# Verify image
docker images | grep cst590-capstone

# Try pulling image manually
docker pull gcumerk/cst590-capstone:latest
```

### Issue 2: Hardware Access Problems
```bash
# Check device permissions
ls -la /dev/video* /dev/ttyACM* /dev/gpiomem

# Run container with privileged mode (already configured)
# Verify devices are mounted in docker-compose.yml
```

### Issue 3: API Not Responding
```bash
# Check port binding
netstat -tlnp | grep 5000

# Test container networking
docker exec -it traffic-monitoring-edge curl localhost:5000/api/health

# Check firewall
sudo ufw status
```

### Issue 4: Permission Denied
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Log out and back in, then test
docker ps
```

## 📋 Deployment Script Options

### deploy-to-pi.sh Options
```bash
# Normal deployment
bash scripts/deploy-to-pi.sh

# Skip environment verification
bash scripts/deploy-to-pi.sh --skip-verification

# Dry run (show what would be done)
bash scripts/deploy-to-pi.sh --dry-run

# Show help
bash scripts/deploy-to-pi.sh --help
```

## 🔐 Security Considerations

1. **Network Security**: Configure firewall rules appropriately
2. **Container Security**: Containers run in privileged mode for hardware access
3. **SSH Access**: Secure SSH configuration for remote management
4. **API Security**: Consider adding authentication for production use

## 📞 Support

If you encounter issues:

1. **Run Diagnostics**: `bash scripts/pi-troubleshoot.sh`
2. **Check Logs**: `docker-compose logs -f`
3. **GitHub Issues**: Report issues on the GitHub repository
4. **Documentation**: Refer to Docker and Raspberry Pi documentation

## 📄 Files Reference

| File | Purpose | Location |
|------|---------|----------|
| `deploy-to-pi.yml` | GitHub Actions workflow | `.github/workflows/` |
| `deploy-to-pi.sh` | Manual deployment script | `scripts/` |
| `pi-troubleshoot.sh` | Troubleshooting tool | `scripts/` |
| `docker-compose.yml` | Container configuration | Project root |
| `Dockerfile` | Image build instructions | Project root |

## 🎯 Next Steps

After successful deployment:

1. **Verify API**: Test endpoints at `http://your-pi-ip:5000/api/health`
2. **Configure Sensors**: Set up camera and radar sensor connections
3. **Monitor Performance**: Check resource usage and logs
4. **Set Up Automation**: Configure GitHub Actions for automatic updates
5. **Test Features**: Verify all traffic monitoring features work correctly
