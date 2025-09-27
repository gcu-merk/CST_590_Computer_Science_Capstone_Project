#!/bin/bash
# Quick Fix Script for Service Restart Issues
# Run this before deployment to ensure proper setup

set -e

echo "=== Quick Fix for Service Restart Issues ==="
echo ""

# Create storage directories with proper permissions
echo "📁 Creating storage directories..."
sudo mkdir -p /mnt/storage/data /mnt/storage/logs /mnt/storage/redis_data /mnt/storage/postgres_data
sudo chmod -R 777 /mnt/storage/data /mnt/storage/logs
sudo chown -R 1000:1000 /mnt/storage/data /mnt/storage/logs
echo "✅ Storage directories created with proper permissions"

# Create local data/logs directories for docker-compose
echo "📁 Creating local directories..."
mkdir -p data logs
chmod 755 data logs
echo "✅ Local directories created"

# Check if environment file exists
if [ ! -f ".env" ]; then
    echo "📝 Creating default environment file..."
    cat > .env << EOF
# Storage paths
STORAGE_ROOT=/mnt/storage
REDIS_DATA_PATH=/mnt/storage/redis_data
POSTGRES_DATA_PATH=/mnt/storage/postgres_data

# User IDs
HOST_UID=1000
HOST_GID=1000

# Docker image
DOCKER_IMAGE=gcumerk/cst590-capstone-public:latest
EOF
    echo "✅ Default environment file created"
else
    echo "✅ Environment file already exists"
fi

echo ""
echo "🎯 Pre-deployment fixes completed!"
echo "You can now run your deployment script safely."