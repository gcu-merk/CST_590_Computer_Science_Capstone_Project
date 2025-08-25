#!/bin/bash
"""
Raspberry Pi Deployment Troubleshooting Script
Diagnoses common deployment issues and provides solutions
"""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
DEPLOY_DIR="${HOME}/traffic-monitor-deploy"
DOCKER_IMAGE="gcumerk/cst590-capstone:latest"

print_header() {
    echo -e "${BLUE}=================================================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}=================================================================${NC}"
    echo ""
}

print_check() {
    echo -e "${PURPLE}🔍 $1${NC}"
}

print_ok() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# System information
check_system_info() {
    print_header "SYSTEM INFORMATION"
    
    print_check "Checking system information..."
    echo "Hostname: $(hostname)"
    echo "OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
    echo "Kernel: $(uname -r)"
    echo "Architecture: $(uname -m)"
    
    if grep -q "BCM" /proc/cpuinfo; then
        PI_MODEL=$(grep "Model" /proc/cpuinfo | cut -d':' -f2 | xargs)
        print_ok "Raspberry Pi detected: $PI_MODEL"
    else
        print_warning "Not running on Raspberry Pi hardware"
    fi
    
    echo "Uptime: $(uptime)"
    echo ""
}

# Docker checks
check_docker() {
    print_header "DOCKER DIAGNOSTICS"
    
    print_check "Checking Docker installation..."
    
    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version)
        print_ok "Docker installed: $DOCKER_VERSION"
        
        # Check Docker daemon
        if docker info &> /dev/null; then
            print_ok "Docker daemon is running"
        else
            print_error "Docker daemon is not running"
            print_info "Try: sudo systemctl start docker"
            return 1
        fi
        
        # Check Docker Compose
        if command -v docker-compose &> /dev/null; then
            COMPOSE_VERSION=$(docker-compose --version)
            print_ok "Docker Compose installed: $COMPOSE_VERSION"
            COMPOSE_CMD="docker-compose"
        elif docker compose version &> /dev/null 2>&1; then
            COMPOSE_VERSION=$(docker compose version)
            print_ok "Docker Compose plugin installed: $COMPOSE_VERSION"
            COMPOSE_CMD="docker compose"
        else
            print_error "Docker Compose not available"
            print_info "Install with: sudo apt-get install docker-compose"
            return 1
        fi
        
        # Check user permissions
        if groups | grep -q docker; then
            print_ok "User is in docker group"
        else
            print_warning "User is not in docker group"
            print_info "Add user to group: sudo usermod -aG docker $USER"
            print_info "Then log out and back in"
        fi
        
    else
        print_error "Docker is not installed"
        print_info "Install with: curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh"
        return 1
    fi
    echo ""
}

# Check deployment directory
check_deployment_dir() {
    print_header "DEPLOYMENT DIRECTORY"
    
    print_check "Checking deployment directory: $DEPLOY_DIR"
    
    if [ -d "$DEPLOY_DIR" ]; then
        print_ok "Deployment directory exists"
        
        cd "$DEPLOY_DIR"
        
        # Check for docker-compose.yml
        if [ -f "docker-compose.yml" ]; then
            print_ok "docker-compose.yml found"
        else
            print_error "docker-compose.yml not found"
            print_info "Copy from project root or run deployment script"
        fi
        
        # Check required directories
        for dir in data logs config; do
            if [ -d "$dir" ]; then
                print_ok "Directory exists: $dir"
            else
                print_warning "Directory missing: $dir"
                print_info "Create with: mkdir -p $dir"
            fi
        done
        
        # Check permissions
        echo "Directory permissions:"
        ls -la
        
    else
        print_error "Deployment directory does not exist"
        print_info "Create with: mkdir -p $DEPLOY_DIR"
    fi
    echo ""
}

# Check Docker image
check_docker_image() {
    print_header "DOCKER IMAGE"
    
    print_check "Checking Docker image: $DOCKER_IMAGE"
    
    if docker images | grep -q "gcumerk/cst590-capstone"; then
        print_ok "Docker image found locally"
        echo "Local images:"
        docker images | grep "gcumerk/cst590-capstone"
    else
        print_warning "Docker image not found locally"
        print_info "Pull with: docker pull $DOCKER_IMAGE"
    fi
    
    # Test pulling image
    print_check "Testing image pull..."
    if docker pull "$DOCKER_IMAGE" --quiet; then
        print_ok "Image pull successful"
    else
        print_error "Failed to pull image"
        print_info "Check internet connection and Docker Hub access"
    fi
    echo ""
}

# Check running containers
check_containers() {
    print_header "CONTAINER STATUS"
    
    print_check "Checking running containers..."
    
    if [ -d "$DEPLOY_DIR" ] && [ -f "$DEPLOY_DIR/docker-compose.yml" ]; then
        cd "$DEPLOY_DIR"
        
        echo "Container status:"
        $COMPOSE_CMD ps
        echo ""
        
        # Check for traffic-monitor container
        CONTAINER_NAME=$($COMPOSE_CMD ps -q traffic-monitor 2>/dev/null || echo "")
        
        if [ -n "$CONTAINER_NAME" ]; then
            print_ok "Traffic monitor container found: $CONTAINER_NAME"
            
            # Check container health
            STATUS=$(docker inspect "$CONTAINER_NAME" --format='{{.State.Status}}')
            case $STATUS in
                "running")
                    print_ok "Container is running"
                    ;;
                "exited")
                    print_error "Container has exited"
                    print_info "Check logs: docker logs $CONTAINER_NAME"
                    ;;
                *)
                    print_warning "Container status: $STATUS"
                    ;;
            esac
            
            # Show container details
            echo "Container details:"
            docker inspect "$CONTAINER_NAME" --format='
Name: {{.Name}}
Status: {{.State.Status}}
Started: {{.State.StartedAt}}
Image: {{.Config.Image}}
Ports: {{range .NetworkSettings.Ports}}{{.}}{{end}}'
            
        else
            print_warning "Traffic monitor container not found"
        fi
        
    else
        print_warning "Cannot check containers - deployment directory or compose file missing"
    fi
    echo ""
}

# Check API endpoint
check_api() {
    print_header "API ENDPOINT"
    
    print_check "Testing API endpoint..."
    
    # Test health endpoint
    if curl -f -s --max-time 10 http://localhost:5000/api/health; then
        print_ok "API health endpoint responding"
    else
        print_error "API health endpoint not responding"
        print_info "Check if container is running and port 5000 is accessible"
    fi
    
    # Check port binding
    print_check "Checking port 5000..."
    if netstat -tlnp 2>/dev/null | grep -q ":5000"; then
        print_ok "Port 5000 is in use"
        netstat -tlnp 2>/dev/null | grep ":5000"
    else
        print_warning "Port 5000 is not in use"
        print_info "Container may not be running or port not mapped correctly"
    fi
    echo ""
}

# Check logs
check_logs() {
    print_header "CONTAINER LOGS"
    
    if [ -d "$DEPLOY_DIR" ] && [ -f "$DEPLOY_DIR/docker-compose.yml" ]; then
        cd "$DEPLOY_DIR"
        
        CONTAINER_NAME=$($COMPOSE_CMD ps -q traffic-monitor 2>/dev/null || echo "")
        
        if [ -n "$CONTAINER_NAME" ]; then
            print_check "Recent container logs (last 30 lines):"
            echo "================================================"
            docker logs --tail 30 "$CONTAINER_NAME"
            echo "================================================"
        else
            print_warning "No container found to check logs"
        fi
    else
        print_warning "Cannot check logs - deployment directory or compose file missing"
    fi
    echo ""
}

# Check hardware access
check_hardware() {
    print_header "HARDWARE ACCESS"
    
    print_check "Checking hardware devices..."
    
    # Check camera
    if [ -e "/dev/video0" ]; then
        print_ok "Camera device found: /dev/video0"
    else
        print_warning "Camera device not found: /dev/video0"
        print_info "Check if camera is connected and enabled"
    fi
    
    # Check GPIO
    if [ -e "/dev/gpiomem" ]; then
        print_ok "GPIO device found: /dev/gpiomem"
    else
        print_warning "GPIO device not found: /dev/gpiomem"
    fi
    
    # Check UART devices
    for device in /dev/ttyACM* /dev/ttyUSB*; do
        if [ -e "$device" ]; then
            print_ok "UART device found: $device"
        fi
    done
    
    echo ""
}

# Check disk space
check_disk_space() {
    print_header "DISK SPACE"
    
    print_check "Checking disk space..."
    df -h
    echo ""
    
    # Check Docker space usage
    print_check "Docker space usage..."
    docker system df
    echo ""
}

# Provide recommendations
provide_recommendations() {
    print_header "RECOMMENDATIONS"
    
    echo "Based on the diagnostics, here are some recommendations:"
    echo ""
    
    echo "1. 📝 View full logs:"
    echo "   cd $DEPLOY_DIR && $COMPOSE_CMD logs -f"
    echo ""
    
    echo "2. 🔄 Restart containers:"
    echo "   cd $DEPLOY_DIR && $COMPOSE_CMD restart"
    echo ""
    
    echo "3. 🧹 Clean up Docker resources:"
    echo "   docker system prune -f"
    echo ""
    
    echo "4. 🚀 Redeploy from scratch:"
    echo "   cd $DEPLOY_DIR && $COMPOSE_CMD down && $COMPOSE_CMD up -d"
    echo ""
    
    echo "5. 📖 Check documentation:"
    echo "   Refer to deployment guide for detailed troubleshooting"
    echo ""
}

# Main function
main() {
    print_header "RASPBERRY PI DEPLOYMENT TROUBLESHOOTING"
    echo "This script will diagnose common deployment issues"
    echo ""
    
    # Set Docker Compose command
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    else
        COMPOSE_CMD="docker compose"
    fi
    
    # Run all checks
    check_system_info
    check_docker
    check_deployment_dir
    check_docker_image
    check_containers
    check_api
    check_logs
    check_hardware
    check_disk_space
    provide_recommendations
    
    print_header "DIAGNOSTICS COMPLETE"
    echo "Review the output above to identify and resolve any issues."
}

# Allow script to be sourced or run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
