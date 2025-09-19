#!/bin/bash

echo "🚀 Deploying Camera-Free Swagger API"
echo "======================================="

cd /mnt/storage/traffic-monitor-deploy

# Stop all containers first
echo "🛑 Stopping existing containers..."
docker compose down 2>/dev/null || true

# Pull latest code if available
echo "📥 Pulling latest code..."
git pull 2>/dev/null || echo "Note: Git pull not available in this directory"

# Check if camera-free compose file exists
if [ ! -f "docker-compose.quick-api.yml" ]; then
    echo "⚠️  Camera-free compose file not found, creating minimal version..."
    
    cat > docker-compose.quick-api.yml << 'EOF'
services:
  traffic-monitor:
    environment:
      - CAMERA_ENABLED=false
      - IMX500_AVAILABLE=false
      - PI_CAMERA_AVAILABLE=false
      - GPIO_ENABLED=false
EOF
fi

# Start with camera-free configuration
echo "🚀 Starting camera-free API..."
docker compose -f docker-compose.yml -f docker-compose.quick-api.yml up -d traffic-monitor redis postgres

echo "⏳ Waiting for services to start..."
sleep 15

echo "🧪 Testing API..."
for i in {1..5}; do
    echo "Attempt $i:"
    if curl -s http://localhost:5000/api/status; then
        echo "✅ API is responding!"
        break
    else
        echo "⏳ Waiting..."
        sleep 5
    fi
done

echo ""
echo "📊 Container status:"
docker compose -f docker-compose.yml -f docker-compose.quick-api.yml ps

echo ""
echo "🎉 Swagger UI should now be available at:"
echo "   http://100.121.231.16:5000/docs/"
echo ""
echo "📋 If still not working, check logs:"
echo "   docker logs traffic-monitor"