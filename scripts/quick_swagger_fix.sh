#!/bin/bash

echo "🔧 Quick fix for Swagger API access"
echo "Creating missing camera directories..."

# Create the missing camera capture directory
sudo mkdir -p /mnt/storage/camera_capture/live
sudo chown -R merk:merk /mnt/storage/camera_capture
sudo chmod -R 755 /mnt/storage/camera_capture

echo "✅ Camera directories created"

echo "🔄 Restarting traffic-monitor container..."
cd /mnt/storage/traffic-monitor-deploy
docker compose restart traffic-monitor

echo "⏳ Waiting for container to start..."
sleep 10

echo "🧪 Testing API accessibility..."
echo ""
echo "📝 Swagger UI should be available at:"
echo "   http://100.121.231.16:5000/docs/"
echo ""

echo "🔍 Testing API status endpoint:"
curl -v http://localhost:5000/api/status || echo "❌ Status endpoint failed"
echo ""

echo "📊 Container status:"
docker compose ps

echo ""
echo "📋 Container logs (last 10 lines):"
docker logs traffic-monitor --tail=10

echo ""
echo "✅ Fix complete! Try accessing: http://100.121.231.16:5000/docs/"