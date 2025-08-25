#!/bin/bash

echo "================================================================="
echo "🔍 RASPBERRY PI DEPLOYMENT SETUP VERIFICATION"
echo "================================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "✅ ${GREEN}$2${NC}"
    else
        echo -e "❌ ${RED}$2${NC}"
    fi
}

print_warning() {
    echo -e "⚠️  ${YELLOW}$1${NC}"
}

print_info() {
    echo -e "ℹ️  ${BLUE}$1${NC}"
}

echo ""
echo "================================================================="
echo "📋 SYSTEM INFORMATION"
echo "================================================================="

# Basic system info
echo "🖥️  System Information:"
echo "   Hostname: $(hostname)"
echo "   User: $(whoami)"
echo "   OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
echo "   Kernel: $(uname -r)"
echo "   Architecture: $(uname -m)"
echo "   Uptime: $(uptime -p)"

# Network info
echo ""
echo "🌐 Network Information:"
LOCAL_IP=$(hostname -I | awk '{print $1}')
echo "   Local IP: $LOCAL_IP"
echo "   External IP: $(curl -s ifconfig.me || echo "Unable to get external IP")"

# Memory and disk
echo ""
echo "💾 Resources:"
echo "   Memory Usage:"
free -h | grep -E "Mem|Swap"
echo "   Disk Usage:"
df -h / | tail -1

echo ""
echo "================================================================="
echo "🐳 DOCKER VERIFICATION"
echo "================================================================="

# Check if Docker is installed
if command -v docker &> /dev/null; then
    print_status 0 "Docker is installed"
    echo "   Version: $(docker --version)"
    
    # Check if Docker service is running
    if systemctl is-active --quiet docker; then
        print_status 0 "Docker service is running"
    else
        print_status 1 "Docker service is NOT running"
        echo "   Try: sudo systemctl start docker"
    fi
    
    # Check if user is in docker group
    if groups $USER | grep -q docker; then
        print_status 0 "User '$USER' is in docker group"
    else
        print_status 1 "User '$USER' is NOT in docker group"
        echo "   Try: sudo usermod -aG docker $USER && newgrp docker"
    fi
    
    # Test Docker command
    if docker ps &> /dev/null; then
        print_status 0 "Docker commands work without sudo"
        echo "   Running containers: $(docker ps --format 'table {{.Names}}\t{{.Status}}' | wc -l) containers"
    else
        print_status 1 "Docker commands require sudo or have permission issues"
    fi
    
else
    print_status 1 "Docker is NOT installed"
    echo "   Install with: curl -fsSL https://get.docker.com | sh"
fi

echo ""
echo "🐙 Docker Compose Verification:"

# Check Docker Compose
if command -v docker-compose &> /dev/null; then
    print_status 0 "Docker Compose (standalone) is installed"
    echo "   Version: $(docker-compose --version)"
elif docker compose version &> /dev/null; then
    print_status 0 "Docker Compose (plugin) is installed"
    echo "   Version: $(docker compose version)"
else
    print_status 1 "Docker Compose is NOT installed"
    echo "   Install with: sudo apt install docker-compose-plugin"
fi

echo ""
echo "================================================================="
echo "🔑 SSH CONFIGURATION"
echo "================================================================="

# SSH service
if systemctl is-active --quiet ssh; then
    print_status 0 "SSH service is running"
    echo "   SSH Port: $(sudo netstat -tlnp | grep :22 | awk '{print $4}' | cut -d: -f2 || echo 22)"
else
    print_status 1 "SSH service is NOT running"
fi

# SSH authorized keys
if [ -f ~/.ssh/authorized_keys ]; then
    KEY_COUNT=$(wc -l < ~/.ssh/authorized_keys)
    print_status 0 "SSH authorized_keys file exists"
    echo "   Number of authorized keys: $KEY_COUNT"
    
    # Show key fingerprints
    if [ $KEY_COUNT -gt 0 ]; then
        echo "   Key fingerprints:"
        ssh-keygen -lf ~/.ssh/authorized_keys | while read line; do
            echo "     $line"
        done
    fi
else
    print_status 1 "SSH authorized_keys file does NOT exist"
    echo "   Create with: mkdir -p ~/.ssh && touch ~/.ssh/authorized_keys"
    echo "   Set permissions with: chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys"
fi

echo ""
echo "================================================================="
echo "📂 DEPLOYMENT DIRECTORY"
echo "================================================================="

DEPLOY_DIR="$HOME/traffic-monitor-deploy"
if [ -d "$DEPLOY_DIR" ]; then
    print_status 0 "Deployment directory exists: $DEPLOY_DIR"
    
    # Check for docker-compose.yml
    if [ -f "$DEPLOY_DIR/docker-compose.yml" ]; then
        print_status 0 "docker-compose.yml exists"
        echo "   File size: $(du -h "$DEPLOY_DIR/docker-compose.yml" | cut -f1)"
        echo "   Last modified: $(stat -c %y "$DEPLOY_DIR/docker-compose.yml")"
    else
        print_status 1 "docker-compose.yml does NOT exist"
    fi
    
    # List directory contents
    echo "   Directory contents:"
    ls -la "$DEPLOY_DIR"
else
    print_status 1 "Deployment directory does NOT exist"
    echo "   Will be created during deployment: $DEPLOY_DIR"
fi

echo ""
echo "================================================================="
echo "🌐 NETWORK CONNECTIVITY"
echo "================================================================="

# Test internet connectivity
if ping -c 1 google.com &> /dev/null; then
    print_status 0 "Internet connectivity works"
else
    print_status 1 "Internet connectivity FAILED"
fi

# Test Docker Hub connectivity
if curl -s --connect-timeout 5 https://registry-1.docker.io &> /dev/null; then
    print_status 0 "Docker Hub connectivity works"
else
    print_status 1 "Docker Hub connectivity FAILED"
fi

# Test GitHub connectivity
if curl -s --connect-timeout 5 https://api.github.com &> /dev/null; then
    print_status 0 "GitHub connectivity works"
else
    print_status 1 "GitHub connectivity FAILED"
fi

echo ""
echo "================================================================="
echo "🐋 DOCKER IMAGES & CONTAINERS"
echo "================================================================="

if command -v docker &> /dev/null && docker ps &> /dev/null; then
    echo "📦 Current Docker Images:"
    if [ $(docker images -q | wc -l) -gt 0 ]; then
        docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
    else
        echo "   No Docker images found"
    fi
    
    echo ""
    echo "🏃 Running Containers:"
    if [ $(docker ps -q | wc -l) -gt 0 ]; then
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    else
        echo "   No running containers"
    fi
    
    echo ""
    echo "💾 Docker System Usage:"
    docker system df
else
    print_warning "Cannot check Docker images/containers (Docker not accessible)"
fi

echo ""
echo "================================================================="
echo "🔧 RASPBERRY PI SPECIFIC"
echo "================================================================="

# Check for Pi-specific hardware
if [ -d /sys/firmware/devicetree/base ]; then
    print_status 0 "Raspberry Pi hardware detected"
    
    # Check for camera
    if [ -e /dev/video0 ]; then
        print_status 0 "Camera device detected (/dev/video0)"
    else
        print_warning "Camera device not found - may need to enable camera in raspi-config"
    fi
    
    # Check GPIO
    if [ -d /sys/class/gpio ]; then
        print_status 0 "GPIO interface available"
    else
        print_warning "GPIO interface not found"
    fi
    
    # Check for I2C
    if [ -e /dev/i2c-1 ]; then
        print_status 0 "I2C interface available"
    else
        print_warning "I2C interface not found - may need to enable in raspi-config"
    fi
    
    # Temperature
    if [ -f /sys/class/thermal/thermal_zone0/temp ]; then
        TEMP=$(cat /sys/class/thermal/thermal_zone0/temp)
        TEMP_C=$((TEMP/1000))
        echo "   CPU Temperature: ${TEMP_C}°C"
        if [ $TEMP_C -gt 70 ]; then
            print_warning "CPU temperature is high (${TEMP_C}°C)"
        fi
    fi
else
    print_warning "Not running on Raspberry Pi hardware"
fi

echo ""
echo "================================================================="
echo "🧪 DEPLOYMENT TEST"
echo "================================================================="

echo "Testing deployment prerequisites..."

# Test docker-compose.yml download
print_info "Testing docker-compose.yml download..."
if curl -fsSL https://raw.githubusercontent.com/gcu-merk/CST_590_Computer_Science_Capstone_Project/main/docker-compose.yml -o /tmp/test-compose.yml; then
    print_status 0 "Can download docker-compose.yml from GitHub"
    echo "   File size: $(du -h /tmp/test-compose.yml | cut -f1)"
    rm -f /tmp/test-compose.yml
else
    print_status 1 "FAILED to download docker-compose.yml from GitHub"
fi

# Test Docker image pull (if Docker works)
if command -v docker &> /dev/null && docker ps &> /dev/null; then
    print_info "Testing Docker image pull..."
    if timeout 30 docker pull gcumerk/cst590-capstone:latest &> /dev/null; then
        print_status 0 "Can pull Docker image from Docker Hub"
    else
        print_warning "Could not pull Docker image (may be normal if image doesn't exist yet)"
    fi
fi

echo ""
echo "================================================================="
echo "📋 SUMMARY & RECOMMENDATIONS"
echo "================================================================="

echo ""
print_info "To prepare for GitHub Actions SSH deployment:"
echo ""
echo "1. 🔑 Add your SSH public key to ~/.ssh/authorized_keys"
echo "2. 🐳 Ensure Docker and Docker Compose are working"
echo "3. 🌐 Verify network connectivity to GitHub and Docker Hub"
echo "4. 📂 The deployment directory will be created automatically"
echo ""
print_info "Access your application after deployment:"
echo "   Dashboard: http://$LOCAL_IP:5000"
echo "   API Health: http://$LOCAL_IP:5000/api/health"
echo ""
print_info "Monitor deployment:"
echo "   Logs: cd ~/traffic-monitor-deploy && docker compose logs -f"
echo "   Status: docker compose ps"
echo ""

echo "================================================================="
echo "✅ VERIFICATION COMPLETE"
echo "================================================================="
