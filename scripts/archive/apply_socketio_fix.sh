#!/bin/bash

echo "🔄 Quick API Fix - Apply Flask-SocketIO Update"
echo "=============================================="

# Stop and remove current container
docker stop traffic-monitor && docker rm traffic-monitor

# Wait for CI/CD to build the updated image
echo "⏳ Waiting 30 seconds for updated Docker image..."
sleep 30

# Pull the latest image with Flask-SocketIO fix
echo "📥 Pulling updated image..."
docker pull gcumerk/cst590-capstone-public:latest

# Restart the API container
echo "🚀 Starting fixed API container..."
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

echo "⏳ Waiting for API startup..."
sleep 15

echo "🧪 Testing API endpoint..."
curl -s http://localhost:5000/api/status && echo "✅ API responding!" || echo "⏳ Still starting..."

echo ""
echo "🎯 Swagger UI: http://100.121.231.16:5000/docs/"
echo "✅ Update complete!"