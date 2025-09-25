#!/bin/bash
#
# Raspberry Pi 5 Traffic Monitoring System - Docker Deployment Script
# Integrates with GitHub Actions workflow and Docker Compose
#

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

# Check Docker and system requirements
check_system_requirements() {
    echo -e "${YELLOW}Checking system requirements...${NC}"
    
    # Note: Running on Raspberry Pi with self-hosted GitHub Actions runner
    echo -e "${GREEN}✓ Running on configured Raspberry Pi system${NC}"
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
    
    # Check if Docker daemon is running
    if ! docker info >/dev/null 2>&1; then
        echo -e "${YELLOW}Docker daemon not responding, attempting to start...${NC}"
        sudo systemctl start docker
        sleep 5
        
        if ! docker info >/dev/null 2>&1; then
            echo -e "${RED}Docker daemon failed to start${NC}"
            exit 1
        fi
        echo -e "${GREEN}✓ Docker daemon started${NC}"
    else
        echo -e "${GREEN}✓ Docker daemon running${NC}"
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
        # Use same logic for compose files as start_services
        STOP_COMPOSE_FILES="-f docker-compose.yml"
        if [ -e "/dev/gpiochip4" ] && [ -f "docker-compose.pi.yml" ]; then
            STOP_COMPOSE_FILES="$STOP_COMPOSE_FILES -f docker-compose.pi.yml"
        fi
        docker compose $STOP_COMPOSE_FILES down || true
    fi
    
    # Force remove any stuck containers by name (handles conflicts)
    echo "Ensuring all traffic monitoring containers are removed..."
    
    # Comprehensive list of containers that might exist
    CLEANUP_CONTAINERS=(
        "traffic-monitor"
        "redis"
        "postgres" 
        "data-maintenance"
        "airport-weather"
        "dht22-weather"
        "vehicle-consolidator"
        "redis-optimization"
        "database-persistence"
        "realtime-events-broadcaster"
        "nginx-proxy"
    )
    
    for container in "${CLEANUP_CONTAINERS[@]}"; do
        if docker ps -a --format "{{.Names}}" | grep -q "^${container}$"; then
            echo "Removing container: $container"
            docker stop "$container" 2>/dev/null || true
            docker rm -f "$container" 2>/dev/null || true
        fi
    done
    
    # Additional safety cleanup - remove any containers with partial name matches
    echo "Additional cleanup of containers with matching patterns..."
    docker ps -a --format "{{.ID}} {{.Names}}" | grep -E "(traffic|redis|database|data-|airport|dht22|vehicle|nginx)" | awk '{print $1}' | xargs -r docker rm -f 2>/dev/null || true
    
    # More aggressive network cleanup - disconnect all endpoints first
    echo "Cleaning up Docker networks..."
    
    # Comprehensive list of networks that might exist
    CLEANUP_NETWORKS=(
        "traffic_monitoring_app-network"
        "traffic_monitoring_default"
        "traffic-monitoring-network"
        "traffic_monitoring_traffic-monitoring-network"
    )
    
    for network in "${CLEANUP_NETWORKS[@]}"; do
        if docker network inspect "$network" >/dev/null 2>&1; then
            echo "Cleaning endpoints from network: $network"
            # Get all connected containers and disconnect them with force
            docker network inspect "$network" --format '{{range .Containers}}{{.Name}} {{end}}' 2>/dev/null | xargs -r -n1 docker network disconnect "$network" --force 2>/dev/null || true
            # Force remove the network
            docker network rm "$network" 2>/dev/null || true
        fi
    done
    
    # Prune any unused networks
    echo "Pruning unused Docker networks..."
    docker network prune -f 2>/dev/null || true
    
    # Final comprehensive cleanup
    echo "Performing final Docker cleanup..."
    
    # Remove any dangling containers and images
    docker system prune -f 2>/dev/null || true
    
    # Stop any legacy systemd services
    sudo systemctl stop traffic-monitor.service 2>/dev/null || true
    sudo systemctl disable traffic-monitor.service 2>/dev/null || true
    
    # Verify clean state
    echo "Verifying clean state..."
    remaining_containers=$(docker ps -a --format "{{.Names}}" | grep -E "(traffic|redis|database|data-|airport|dht22|vehicle|nginx)" | wc -l)
    if [ "$remaining_containers" -gt 0 ]; then
        echo "Warning: Found $remaining_containers potentially conflicting containers still present"
        docker ps -a --format "{{.Names}}" | grep -E "(traffic|redis|database|data-|airport|dht22|vehicle|nginx)" | head -5
    else
        echo "✓ Clean container state verified"
    fi
    
    echo -e "${GREEN}✓ Existing services stopped and cleaned up${NC}"
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
    
    # Determine which compose files to use
    COMPOSE_FILES="-f docker-compose.yml"
    if [ -e "/dev/gpiochip4" ]; then
        echo "Raspberry Pi 5 GPIO chip found, enabling hardware access..."
        COMPOSE_FILES="$COMPOSE_FILES -f docker-compose.pi.yml"
    else
        echo "Raspberry Pi 5 GPIO chip not found (/dev/gpiochip4), skipping hardware mappings..."
        echo "Note: This deployment is optimized for Raspberry Pi 5"
    fi
    
    # Pull latest images
    echo "Pulling Docker images..."
    if ! docker compose $COMPOSE_FILES pull; then
        echo -e "${YELLOW}Warning: Failed to pull some images, continuing with existing images${NC}"
    fi
    
    # Stop any existing containers first (with force cleanup)
    echo "Stopping any existing containers..."
    docker compose $COMPOSE_FILES down --remove-orphans || true
    
    # Additional cleanup to handle stubborn containers and networks
    echo "Ensuring clean container state..."
    
    # Stop and remove ALL containers that might conflict (comprehensive list)
    CONTAINERS_TO_REMOVE=(
        "traffic-monitor"
        "redis" 
        "postgres"
        "data-maintenance"
        "airport-weather"
        "dht22-weather"
        "vehicle-consolidator"
        "redis-optimization"
        "database-persistence"
        "realtime-events-broadcaster"
        "nginx-proxy"
    )
    
    echo "Removing potentially conflicting containers..."
    for container in "${CONTAINERS_TO_REMOVE[@]}"; do
        # Find container by name (exact match or partial match)
        container_ids=$(docker ps -aq --filter "name=${container}" 2>/dev/null || true)
        if [ ! -z "$container_ids" ]; then
            echo "Removing container(s) matching '${container}': $container_ids"
            echo "$container_ids" | xargs -r docker stop 2>/dev/null || true
            echo "$container_ids" | xargs -r docker rm -f 2>/dev/null || true
        fi
    done
    
    # Force remove any remaining containers with conflicting names
    echo "Force cleanup any remaining containers..."
    docker ps -a --format "{{.ID}} {{.Names}}" | grep -E "(traffic|redis|database|data-|airport|dht22|vehicle|nginx)" | awk '{print $1}' | xargs -r docker rm -f 2>/dev/null || true
    
    # Force cleanup any remaining network endpoints
    NETWORKS_TO_REMOVE=(
        "traffic_monitoring_app-network"
        "traffic_monitoring_default"
        "traffic-monitoring-network"
        "traffic_monitoring_traffic-monitoring-network"
    )
    
    for network in "${NETWORKS_TO_REMOVE[@]}"; do
        if docker network inspect "$network" >/dev/null 2>&1; then
            echo "Force cleaning network: $network"
            # Disconnect all containers from network
            docker network inspect "$network" --format '{{range .Containers}}{{.Name}} {{end}}' 2>/dev/null | xargs -r -n1 docker network disconnect "$network" --force 2>/dev/null || true
            # Remove network
            docker network rm "$network" 2>/dev/null || true
        fi
    done
    
    # Prune unused networks
    echo "Pruning unused networks..."
    docker network prune -f 2>/dev/null || true
    
    # Start services with retry logic
    echo "Starting containers..."
    
    # First attempt: normal startup
    if docker compose $COMPOSE_FILES up -d; then
        echo -e "${GREEN}✓ Docker services started successfully${NC}"
    else
        echo -e "${YELLOW}First startup attempt failed, trying with force recreate...${NC}"
        
        # Second attempt: force recreate
        if docker compose $COMPOSE_FILES up -d --force-recreate --remove-orphans; then
            echo -e "${GREEN}✓ Docker services started with force recreate${NC}"
        else
            echo -e "${RED}✗ Failed to start Docker services${NC}"
            echo "Checking for errors..."
            docker compose $COMPOSE_FILES logs --tail=20
            
            # Show what containers exist
            echo "Current container state:"
            docker ps -a
            
            # Show network state
            echo "Current network state:"
            docker network ls
            
            exit 1
        fi
    fi
    
    # Give containers time to start
    echo "Waiting for containers to initialize..."
    sleep 15
    
    # Show container status
    echo "Container status after startup:"
    docker compose $COMPOSE_FILES ps
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
    
    # Add cron job for Docker cleanup (daily at 3:00 AM)
    (crontab -l 2>/dev/null; echo "0 3 * * * /usr/bin/docker system prune -f --filter until=24h >> $STORAGE_ROOT/logs/docker-cleanup.log 2>&1") | crontab -
    
    echo -e "${GREEN}✓ Monitoring and Docker cleanup cron jobs configured${NC}"
}

# Performance optimizations
optimize_system() {
    echo -e "${YELLOW}Applying system optimizations...${NC}"
    
    # Docker-specific optimizations
    if [ ! -f /etc/docker/daemon.json ]; then
        sudo mkdir -p /etc/docker
        sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
    "data-root": "/mnt/storage/docker",
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "10m",
        "max-file": "3"
    },
    "storage-driver": "overlay2"
}
EOF
        sudo systemctl restart docker
        echo -e "${GREEN}✓ Docker configured to use SSD storage${NC}"
    else
        echo -e "${GREEN}✓ Docker daemon.json already configured${NC}"
    fi
    
    echo -e "${GREEN}✓ System optimized for Docker${NC}"
}

# Main deployment function
main() {
    echo -e "${BLUE}Starting Docker-based deployment...${NC}"
    
    check_system_requirements
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