#!/bin/bash

# Quick test script for camera-free Swagger API
# Run this on your Raspberry Pi

echo "🔄 Stopping existing containers..."
docker-compose down

echo "🔄 Pulling latest changes..."
git pull

echo "🚀 Starting camera-free API..."
docker-compose -f docker-compose.quick-api.yml up -d

echo "⏳ Waiting for API to start..."
sleep 15

echo "🧪 Testing API accessibility..."
echo ""
echo "📝 Swagger UI should be available at:"
echo "   http://100.121.231.16:5000/docs/"
echo ""
echo "🔍 API Status endpoint:"
curl -v http://100.121.231.16:5000/api/status || echo "❌ Status endpoint failed"
echo ""
echo ""

echo "📊 Container status:"
docker-compose -f docker-compose.quick-api.yml ps

echo ""
echo "📋 Container logs (last 20 lines):"
docker-compose -f docker-compose.quick-api.yml logs --tail=20 traffic-monitor

echo ""
echo "✅ Test complete! Check the Swagger UI at: http://100.121.231.16:5000/docs/"