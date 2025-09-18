#!/bin/bash
"""
Raspberry Pi 5 Traffic Monitoring System - Docker Deployment Script
Integrates with GitHub Actions workflow and Docker Compose
"""

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DEPLOY_DIR="/mnt/storage/deployment-staging"
SERVICE_USER="merk"
STORAGE_ROOT="/mnt/storage"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Raspberry Pi 5 Traffic Monitoring Deploy${NC}"
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

# Verify Docker and Docker Compose
check_docker() {
    echo -e "${YELLOW}Checking Docker installation...${NC}"
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Docker not found. Installing...${NC}"
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        sudo usermod -aG docker $USER
        rm get-docker.sh
        echo -e "${GREEN}✓ Docker installed${NC}"
    else
        echo -e "${GREEN}✓ Docker found${NC}"
    fi
    
    # Verify Docker Compose
    if ! docker compose version &> /dev/null; then
        echo -e "${RED}Docker Compose not available${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Docker Compose found${NC}"
}

# Enable hardware interfaces for Pi
enable_hardware_interfaces() {
    echo -e "${YELLOW}Enabling hardware interfaces...${NC}"
    
    # Enable camera, SPI, I2C
    sudo raspi-config nonint do_camera 0 || true
    sudo raspi-config nonint do_spi 0 || true
    sudo raspi-config nonint do_i2c 0 || true
    
    # Configure boot options for hardware access
    CONFIG_FILE="/boot/firmware/config.txt"
    if [ -f "$CONFIG_FILE" ]; then
        # Enable UART
        if ! grep -q "enable_uart=1" $CONFIG_FILE; then
            echo "enable_uart=1" | sudo tee -a $CONFIG_FILE
        fi
        
        # Enable SPI
        if ! grep -q "dtparam=spi=on" $CONFIG_FILE; then
            echo "dtparam=spi=on" | sudo tee -a $CONFIG_FILE
        fi
        
        # GPU memory for AI processing
        if ! grep -q "gpu_mem=" $CONFIG_FILE; then
            echo "gpu_mem=128" | sudo tee -a $CONFIG_FILE
        fi
    fi
    
    echo -e "${GREEN}✓ Hardware interfaces configured${NC}"
}

# Verify required files exist
verify_deployment_files() {
    echo -e "${YELLOW}Verifying deployment files...${NC}"
    
    required_files=(
        "docker-compose.yml"
        "docker-compose.pi.yml" 
        ".env"
    )
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            echo -e "${RED}✗ Missing required file: $file${NC}"
            exit 1
        fi
    done
    
    # Check Docker image availability
    echo "Checking Docker image availability..."
    DOCKER_IMAGE_NAME=$(grep -E "DOCKER_IMAGE=" .env | cut -d'=' -f2 | head -1)
    if [ -z "$DOCKER_IMAGE_NAME" ]; then
        DOCKER_IMAGE_NAME="gcumerk/cst590-capstone-public:latest"
    fi
    
    echo "Checking image: $DOCKER_IMAGE_NAME"
    if ! docker pull "$DOCKER_IMAGE_NAME"; then
        echo -e "${RED}✗ Failed to pull Docker image: $DOCKER_IMAGE_NAME${NC}"
        echo "This could cause service startup failures"
        # Don't exit here, let's continue and see what happens
    else
        echo -e "${GREEN}✓ Docker image available: $DOCKER_IMAGE_NAME${NC}"
    fi
    
    echo -e "${GREEN}✓ All required files present${NC}"
}

# Stop existing services
stop_existing_services() {
    echo -e "${YELLOW}Stopping existing services...${NC}"
    
    # Stop Docker containers if running
    if [ -f "$DEPLOY_DIR/docker-compose.yml" ]; then
        cd "$DEPLOY_DIR"
        docker compose -f docker-compose.yml -f docker-compose.pi.yml down || true
    fi
    
    # Stop any legacy systemd services
    sudo systemctl stop traffic-monitor.service 2>/dev/null || true
    sudo systemctl disable traffic-monitor.service 2>/dev/null || true
    
    echo -e "${GREEN}✓ Existing services stopped${NC}"
}

# Deploy application files
deploy_application() {
    echo -e "${YELLOW}Deploying application to $DEPLOY_DIR...${NC}"
    
    # Check if we're already in the deployment directory
    if [ "$(pwd)" = "$DEPLOY_DIR" ]; then
        echo "Already running from deployment directory, skipping file copy"
        echo -e "${GREEN}✓ Application files already in place${NC}"
        
        # Ensure proper permissions
        sudo chown -R $SERVICE_USER:$SERVICE_USER "$DEPLOY_DIR"
        
        # Make scripts executable
        find "$DEPLOY_DIR" -name "*.sh" -exec chmod +x {} \;
        
        echo -e "${GREEN}✓ Application deployed${NC}"
        return
    fi
    
    # Create deployment directory
    sudo mkdir -p "$DEPLOY_DIR"
    sudo chown -R $SERVICE_USER:$SERVICE_USER "$DEPLOY_DIR"
    
    # Copy application files (we're already in the staging directory from GitHub Actions)
    cp -r . "$DEPLOY_DIR/"
    
    # Ensure proper permissions
    sudo chown -R $SERVICE_USER:$SERVICE_USER "$DEPLOY_DIR"
    
    # Make scripts executable
    find "$DEPLOY_DIR" -name "*.sh" -exec chmod +x {} \;
    
    echo -e "${GREEN}✓ Application deployed${NC}"
}

# Start Docker services
start_services() {
    echo -e "${YELLOW}Starting Docker services...${NC}"
    
    cd "$DEPLOY_DIR"
    
    # Verify .env file has required variables
    if [ -f ".env" ]; then
        echo "Environment variables:"
        grep -E "HOST_UID|HOST_GID|STORAGE_ROOT" .env || echo "Warning: Some environment variables missing"
    else
        echo -e "${RED}✗ .env file missing${NC}"
        exit 1
    fi
    
    # Pull latest images
    echo "Pulling Docker images..."
    if ! docker compose -f docker-compose.yml -f docker-compose.pi.yml pull; then
        echo -e "${YELLOW}Warning: Failed to pull some images, continuing with existing images${NC}"
    fi
    
    # Stop any existing containers first
    echo "Stopping any existing containers..."
    docker compose -f docker-compose.yml -f docker-compose.pi.yml down || true
    
    # Start services
    echo "Starting containers..."
    if docker compose -f docker-compose.yml -f docker-compose.pi.yml up -d; then
        echo -e "${GREEN}✓ Docker services started${NC}"
        
        # Give containers time to start
        echo "Waiting for containers to initialize..."
        sleep 10
        
        # Show container status
        echo "Container status after startup:"
        docker compose -f docker-compose.yml -f docker-compose.pi.yml ps
    else
        echo -e "${RED}✗ Failed to start Docker services${NC}"
        echo "Checking for errors..."
        docker compose -f docker-compose.yml -f docker-compose.pi.yml logs
        exit 1
    fi
}

# Verify deployment
verify_deployment() {
    echo -e "${YELLOW}Verifying deployment...${NC}"
    
    cd "$DEPLOY_DIR"
    
    # Check container status
    echo "Container status:"
    docker compose -f docker-compose.yml -f docker-compose.pi.yml ps
    
    # Check if services are responding
    sleep 10
    
    # Test basic connectivity
    local containers=$(docker compose -f docker-compose.yml -f docker-compose.pi.yml ps --services)
    for container in $containers; do
        if docker compose -f docker-compose.yml -f docker-compose.pi.yml ps --status running | grep -q "$container"; then
            echo -e "${GREEN}✓ $container is running${NC}"
        else
            echo -e "${RED}✗ $container is not running${NC}"
            docker compose -f docker-compose.yml -f docker-compose.pi.yml logs "$container" | tail -20
        fi
    done
}

# Setup monitoring and logging
setup_monitoring() {
    echo -e "${YELLOW}Setting up monitoring...${NC}"
    
    # Create logrotate configuration for Docker logs
    sudo tee /etc/logrotate.d/traffic-monitor > /dev/null <<EOF
$STORAGE_ROOT/logs/docker/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
EOF

    # Create health check script
    sudo tee /usr/local/bin/traffic-monitor-health > /dev/null <<'EOF'
#!/bin/bash
cd /mnt/storage/deployment-staging
if ! docker compose -f docker-compose.yml -f docker-compose.pi.yml ps --status running | grep -q .; then
    echo "Containers not running, attempting restart..."
    docker compose -f docker-compose.yml -f docker-compose.pi.yml up -d
fi
EOF
    
    sudo chmod +x /usr/local/bin/traffic-monitor-health
    
    # Add cron job for health checks (every 5 minutes)
    (crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/traffic-monitor-health >> $STORAGE_ROOT/logs/health-check.log 2>&1") | crontab -
    
    echo -e "${GREEN}✓ Monitoring configured${NC}"
}

# Performance optimizations
optimize_system() {
    echo -e "${YELLOW}Applying system optimizations...${NC}"
    
    # Docker-specific optimizations
    if [ ! -f /etc/docker/daemon.json ]; then
        sudo mkdir -p /etc/docker
        sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "10m",
        "max-file": "3"
    },
    "storage-driver": "overlay2"
}
EOF
        sudo systemctl restart docker
    fi
    
    echo -e "${GREEN}✓ System optimized for Docker${NC}"
}

# Main deployment function
main() {
    echo -e "${BLUE}Starting Docker-based deployment...${NC}"
    
    check_raspberry_pi
    check_docker
    enable_hardware_interfaces
    verify_deployment_files
    stop_existing_services
    deploy_application
    start_services
    verify_deployment
    setup_monitoring
    optimize_system
    
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✓ Deployment completed successfully!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo
    echo -e "${YELLOW}Service Management:${NC}"
    echo "• View status: cd $DEPLOY_DIR && docker compose -f docker-compose.yml -f docker-compose.pi.yml ps"
    echo "• View logs: cd $DEPLOY_DIR && docker compose -f docker-compose.yml -f docker-compose.pi.yml logs -f"
    echo "• Restart: cd $DEPLOY_DIR && docker compose -f docker-compose.yml -f docker-compose.pi.yml restart"
    echo "• Stop: cd $DEPLOY_DIR && docker compose -f docker-compose.yml -f docker-compose.pi.yml down"
    echo
    echo -e "${YELLOW}Monitoring:${NC}"
    echo "• Health checks: tail -f $STORAGE_ROOT/logs/health-check.log"
    echo "• Docker logs: ls $STORAGE_ROOT/logs/docker/"
    echo
    echo -e "${YELLOW}Deployment location: $DEPLOY_DIR${NC}"
    
    # Show final container status
    echo -e "${BLUE}Current container status:${NC}"
    cd "$DEPLOY_DIR"
    docker compose -f docker-compose.yml -f docker-compose.pi.yml ps
}

# Run main function
main "$@"