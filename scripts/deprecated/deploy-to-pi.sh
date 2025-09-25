#!/bin/bash
"""
Raspberry Pi Deployment Script
Manual deployment tool for testing and troubleshooting
"""

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
DOCKER_IMAGE="gcumerk/cst590-capstone-public:latest"
DEPLOY_DIR="/mnt/storage/traffic-monitor-deploy"
COMPOSE_PROJECT_NAME="traffic-monitor"

# Helper functions
print_header() {
    echo -e "${BLUE}=================================================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}=================================================================${NC}"
    echo ""
}

print_step() {
    echo -e "${PURPLE}🔸 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if running with proper permissions
check_permissions() {
    print_step "Checking permissions..."
    
    if ! groups | grep -q docker; then
        print_warning "User is not in docker group. You may need to use sudo."
        echo "To add user to docker group: sudo usermod -aG docker $USER"
        echo "Then log out and back in."
    fi
    
    print_success "Permission check complete"
}

# Verify environment
verify_environment() {
    print_step "Verifying environment..."
    
    # Check if we're on a Raspberry Pi
    if grep -q "BCM" /proc/cpuinfo; then
        print_success "Running on Raspberry Pi"
    else
        print_warning "Not running on Raspberry Pi hardware"
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        echo "Install Docker: curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh"
        exit 1
    fi
    print_success "Docker is installed"
    
    # Check Docker Compose
    if command -v docker-compose &> /dev/null; then
        print_success "Docker Compose (standalone) is available"
        COMPOSE_CMD="docker-compose"
    elif docker compose version &> /dev/null 2>&1; then
        print_success "Docker Compose (plugin) is available"
        COMPOSE_CMD="docker compose"
    else
        print_error "Docker Compose is not available"
        echo "Install Docker Compose: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    # Check Docker daemon
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running"
        echo "Start Docker: sudo systemctl start docker"
        exit 1
    fi
    print_success "Docker daemon is running"
}

# Run docker-compose (simple wrapper — we target Raspberry Pi hosts only)
run_compose() {
    if [ "$COMPOSE_CMD" = "docker compose" ]; then
        docker compose "$@"
    else
        docker-compose "$@"
    fi
}

# Setup deployment directory
setup_deploy_dir() {
    print_step "Setting up deployment directory: $DEPLOY_DIR"
    
    # Create deployment directory
    mkdir -p "$DEPLOY_DIR"
    cd "$DEPLOY_DIR"
    
    # Create required subdirectories
    mkdir -p data logs config
    
    # Copy docker-compose.yml if it exists in the repo
    if [ -f "$(dirname "$0")/../docker-compose.yml" ]; then
        cp "$(dirname "$0")/../docker-compose.yml" .
        print_success "Docker Compose file copied"
    elif [ ! -f "docker-compose.yml" ]; then
        print_error "docker-compose.yml not found"
        echo "Please ensure docker-compose.yml is available in the deployment directory"
        exit 1
    fi
    
    print_success "Deployment directory setup complete"
}

# Stop existing containers
stop_containers() {
    print_step "Stopping existing containers..."
    
    cd "$DEPLOY_DIR"
    
    # Stop containers gracefully
    if [ -f "docker-compose.yml" ]; then
        # First, ensure nothing left bound to host port 5000 (API port)
            run_compose down --remove-orphans || echo "No existing containers to stop"
        # Try to stop any containers that map host port 5000
        conflicting=$(docker ps --format '{{.ID}} {{.Names}} {{.Ports}}' | grep -E '0.0.0.0:5000|:5000->' || true)
        if [ -n "$conflicting" ]; then
            echo "$conflicting" | while read -r line; do
                cid=$(echo "$line" | awk '{print $1}')
                name=$(echo "$line" | awk '{print $2}')
                print_step "Stopping container $name ($cid) that is binding host port 5000"
                docker stop "$cid" || print_warning "Failed to stop container $cid"
                docker rm "$cid" || print_warning "Failed to remove container $cid"
            done
        fi

        # If a non-container process binds port 5000, try to identify and kill it after user confirmation
        # Gracefully stop and remove all containers managed by docker-compose
        run_compose down --remove-orphans || echo "No existing containers to stop"
        else
        if run_compose up -d; then
        fi
        if [ -n "$port_owner" ]; then
            print_warning "A process appears to be listening on host port 5000:\n$port_owner"
            # Try to extract PID
            pid=$(echo "$port_owner" | sed -n 's/.*pid=\?\?\?\?\?\?\?\?\?\?//p' || true)
            # Fallback extraction using common formats
            pid=$(echo "$port_owner" | grep -oE "pid=[0-9]+" | grep -oE "[0-9]+" || true)
            if [ -n "$pid" ]; then
                print_step "Attempting to kill PID $pid to free port 5000..."
                sudo kill "$pid" || print_warning "Failed to kill PID $pid"
                sleep 1
            else
                print_warning "Could not determine PID automatically. Manual intervention may be required."
            fi
        fi

        $COMPOSE_CMD down --remove-orphans || echo "No existing containers to stop"
        print_success "Containers stopped"
        CONTAINER_NAME=$(run_compose ps -q traffic-monitor 2>/dev/null || echo "")
        print_warning "No docker-compose.yml found, skipping container stop"
    fi
    
    # Clean up orphaned containers
    docker container prune -f || true
}

# Pull latest image
pull_image() {
    print_step "Pulling latest Docker image: $DOCKER_IMAGE"
    
    if docker pull "$DOCKER_IMAGE"; then
        print_success "Image pulled successfully"
    else
        print_error "Failed to pull image"
        exit 1
    fi
    
    # Clean up old images
    docker image prune -f || true
}

# Deploy containers
deploy_containers() {
    print_step "Deploying containers..."
    cd "$DEPLOY_DIR"
    # Gracefully stop and remove all containers managed by docker-compose
    $COMPOSE_CMD down --remove-orphans || echo "No existing containers to stop"
    # Start containers
    if $COMPOSE_CMD up -d; then
        print_success "Containers deployed"
        run_compose ps
        print_error "Failed to deploy containers"
        exit 1
    fi
    
    # Wait for containers to be ready
    print_step "Waiting for containers to be ready..."
    sleep 10
}

# Install Pi-specific packages
install_pi_packages() {
    print_step "Installing Raspberry Pi specific packages..."
    
    cd "$DEPLOY_DIR"
    
    # Get container name
    CONTAINER_NAME=$($COMPOSE_CMD ps -q traffic-monitor 2>/dev/null || echo "")
    
    if [ -z "$CONTAINER_NAME" ]; then
        print_error "Container not found. Checking all containers..."
        $COMPOSE_CMD ps
        exit 1
    fi
    
    print_step "Installing packages in container: $CONTAINER_NAME"
    
    # Install packages with error handling
    PI_PACKAGES="picamera2 gpiozero RPi.GPIO gpustat"
    
    for package in $PI_PACKAGES; do
        if docker exec "$CONTAINER_NAME" pip install --no-cache-dir "$package"; then
            print_success "Installed $package"
        else
            print_warning "Failed to install $package (may not be available)"
        fi
    done
    
    print_success "Pi-specific package installation complete"
}

# Verify deployment
verify_deployment() {
    print_step "Verifying deployment..."
    
    cd "$DEPLOY_DIR"
    
    # Show container status
    echo "Container status:"
    $COMPOSE_CMD ps
    echo ""
    
    # Get container name
    CONTAINER_NAME=$($COMPOSE_CMD ps -q traffic-monitor 2>/dev/null || echo "")
    
    if [ -n "$CONTAINER_NAME" ]; then
        # Check container health
        STATUS=$(docker inspect "$CONTAINER_NAME" --format='{{.State.Status}}')
        echo "Container status: $STATUS"
        
        if [ "$STATUS" = "running" ]; then
            print_success "Container is running"
        else
            print_error "Container is not running properly"
        fi
        
        # Test API endpoint
        print_step "Testing API endpoint..."
        for i in {1..10}; do
            if curl -f -s --max-time 5 http://localhost:5000/api/health >/dev/null 2>&1; then
                print_success "API is responding"
                break
            else
                if [ $i -eq 10 ]; then
                    print_warning "API not responding after 10 attempts"
                else
                    echo "Waiting for API... (attempt $i/10)"
                    sleep 6
                fi
            fi
        done
        
        # Show recent logs
        echo ""
        echo "Recent container logs:"
        echo "====================="
        docker logs --tail 20 "$CONTAINER_NAME"
        
    else
        print_error "Container not found"
        exit 1
    fi
    
    print_success "Deployment verification complete"
}

# Cleanup function
cleanup() {
    print_step "Cleaning up Docker resources..."
    docker system prune -f --volumes || true
    print_success "Cleanup complete"
}

# Main deployment function
main() {
    print_header "RASPBERRY PI DEPLOYMENT SCRIPT"
    
    echo "This script will deploy the traffic monitoring system to your Raspberry Pi"
    echo "Deployment directory: $DEPLOY_DIR"
    echo "Docker image: $DOCKER_IMAGE"
    echo ""
    
    # Parse command line arguments
    SKIP_VERIFICATION=false
    DRY_RUN=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-verification)
                SKIP_VERIFICATION=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [options]"
                echo "Options:"
                echo "  --skip-verification    Skip environment verification"
                echo "  --dry-run             Show what would be done without executing"
                echo "  --help, -h            Show this help message"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    if [ "$DRY_RUN" = true ]; then
        print_header "DRY RUN MODE - No changes will be made"
        return 0
    fi
    
    # Run deployment steps
    check_permissions
    
    if [ "$SKIP_VERIFICATION" = false ]; then
        verify_environment
    fi
    
    setup_deploy_dir
    stop_containers
    pull_image
    deploy_containers
    install_pi_packages
    verify_deployment
    
    print_header "DEPLOYMENT COMPLETE"
    print_success "Traffic monitoring system deployed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Check the API at: http://localhost:5000/api/health"
    echo "2. View logs: cd $DEPLOY_DIR && $COMPOSE_CMD logs -f"
    echo "3. Monitor status: cd $DEPLOY_DIR && $COMPOSE_CMD ps"
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
