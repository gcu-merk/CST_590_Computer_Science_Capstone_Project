#!/bin/bash

echo "🚀 Simple Swagger API Deployment"
echo "================================="

# Stop and remove all existing containers
echo "🛑 Cleaning up existing containers..."
docker stop redis postgres traffic-monitor 2>/dev/null || true
docker rm redis postgres traffic-monitor 2>/dev/null || true

# Pull latest image
echo "📥 Pulling latest image..."
docker pull gcumerk/cst590-capstone-public:latest

# Create directories
echo "📁 Setting up directories..."
sudo mkdir -p /mnt/storage/camera_capture/live
sudo mkdir -p /mnt/storage/postgres_data
sudo mkdir -p /mnt/storage/redis_data
sudo chown -R merk:merk /mnt/storage/camera_capture

echo "🐳 Starting database containers..."

# Start Redis
docker run -d \
  --name redis \
  --restart unless-stopped \
  -p 6379:6379 \
  redis:7-alpine

# Start PostgreSQL  
docker run -d \
  --name postgres \
  --restart unless-stopped \
  -p 5433:5432 \
  -e POSTGRES_DB=traffic_monitoring \
  -e POSTGRES_USER=traffic_monitor \
  -e POSTGRES_PASSWORD=secure_password_123 \
  postgres:15-alpine

echo "⏳ Waiting for databases..."
sleep 10

echo "🚀 Starting Swagger API container..."

# Start Traffic Monitor with camera disabled
docker run -d \
  --name traffic-monitor \
  --restart unless-stopped \
  -p 5000:5000 \
  -e CAMERA_ENABLED=false \
  -e IMX500_AVAILABLE=false \
  -e PI_CAMERA_AVAILABLE=false \
  -e STORAGE_ROOT=/mnt/storage \
  -v /mnt/storage:/mnt/storage \
  --link redis:redis \
  --link postgres:postgres \
  gcumerk/cst590-capstone-public:latest

echo "⏳ Waiting for API to start..."
sleep 15

echo "🧪 Testing API connection..."
for i in {1..3}; do
  if curl -s http://localhost:5000/api/status; then
    echo "✅ API is responding!"
    break
  else
    echo "⏳ Attempt $i/3 - waiting..."
    sleep 5
  fi
done

echo ""
echo "📊 Container Status:"
docker ps

echo ""
echo "🎯 Swagger UI Available At:"
echo "   http://100.121.231.16:5000/docs/"
echo ""
echo "📋 Troubleshooting:"
echo "   docker logs traffic-monitor"
echo ""
echo "✅ Deployment Complete!"