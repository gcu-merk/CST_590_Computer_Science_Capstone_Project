#!/bin/bash

echo "🔍 Swagger API Error Diagnosis"
echo "=============================="

echo "📊 Container Status:"
docker ps | grep traffic-monitor

echo ""
echo "🔍 Testing swagger.json endpoint:"
curl -v http://localhost:5000/swagger.json 2>&1 | head -15

echo ""
echo "🔍 Testing API health endpoint:"
curl -v http://localhost:5000/api/health 2>&1 | head -10

echo ""
echo "📋 Container logs for errors:"
docker logs traffic-monitor --tail=30 | grep -i -E "error|exception|traceback"

echo ""
echo "🧪 API models test:"
docker exec traffic-monitor python -c "
try:
    from edge_api.api_models import *
    print('✅ API models imported successfully')
except Exception as e:
    print(f'❌ API models error: {e}')
    import traceback
    traceback.print_exc()
" 2>&1

echo ""
echo "🧪 SwaggerAPIGateway test:"
docker exec traffic-monitor python -c "
try:
    from edge_api.swagger_api_gateway import SwaggerAPIGateway
    print('✅ SwaggerAPIGateway imported successfully')
    gateway = SwaggerAPIGateway()
    print('✅ SwaggerAPIGateway instantiated successfully')
except Exception as e:
    print(f'❌ SwaggerAPIGateway error: {e}')
    import traceback
    traceback.print_exc()
" 2>&1

echo ""
echo "✅ Swagger diagnosis complete!"