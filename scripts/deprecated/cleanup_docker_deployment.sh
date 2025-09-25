#!/bin/bash

echo "=== Docker Deployment Cleanup Script ==="
echo "This script forcefully removes conflicting Docker containers and networks"
echo "Date: $(date)"
echo

# Function to safely remove container by name
remove_container_by_name() {
    local container_name=$1
    echo "Checking for container: $container_name"
    
    # Check if container exists (running or stopped)
    if docker ps -a --format "table {{.Names}}" | grep -q "^${container_name}$"; then
        echo "Found container: $container_name"
        
        # Stop if running
        if docker ps --format "table {{.Names}}" | grep -q "^${container_name}$"; then
            echo "Stopping running container: $container_name"
            docker stop "$container_name" || echo "Failed to stop $container_name"
        fi
        
        # Remove container
        echo "Removing container: $container_name"
        docker rm -f "$container_name" || echo "Failed to remove $container_name"
    else
        echo "Container $container_name not found"
    fi
}

# Function to remove network if it exists
remove_network() {
    local network_name=$1
    echo "Checking for network: $network_name"
    
    if docker network ls --format "table {{.Name}}" | grep -q "^${network_name}$"; then
        echo "Found network: $network_name"
        echo "Removing network: $network_name"
        docker network rm "$network_name" 2>/dev/null || echo "Network $network_name may still be in use"
    else
        echo "Network $network_name not found"
    fi
}

echo "1. Stopping and removing all traffic monitoring containers..."

# Remove all containers from the traffic monitoring stack
remove_container_by_name "traffic-monitor"
remove_container_by_name "redis"
remove_container_by_name "postgres"
remove_container_by_name "data-maintenance"
remove_container_by_name "airport-weather"
remove_container_by_name "dht22-weather"

echo
echo "2. Removing docker networks..."

# Remove networks that might be stuck
remove_network "traffic_monitoring_traffic-monitoring-network"
remove_network "traffic-monitoring-network"
remove_network "traffic_monitoring_default"

echo
echo "3. Pruning unused Docker resources..."

# Clean up unused resources
docker system prune -f

echo
echo "4. Current Docker status:"
echo "Running containers:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo
echo "All networks:"
docker network ls

echo
echo "=== Cleanup Complete ==="
echo "You can now run your deployment script again."
echo "Recommended next steps:"
echo "1. cd ~/CST_590_Computer_Science_Capstone_Project"
echo "2. git pull origin main"
echo "3. docker-compose -f docker-compose.yml up -d"
echo "   OR"
echo "3. ./deployment/deploy.sh"