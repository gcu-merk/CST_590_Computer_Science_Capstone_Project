#!/bin/bash

echo "🧪 Testing API Server Startup"
echo "============================="

echo "📦 Testing SwaggerAPIGateway import:"
docker exec traffic-monitor python -c "
import sys
sys.path.append('/app/edge_api')
try:
    from swagger_api_gateway import SwaggerAPIGateway
    print('✅ SwaggerAPIGateway import successful')
except Exception as e:
    print(f'❌ Import failed: {e}')
"

echo ""
echo "🔍 Testing Flask-RESTX import:"
docker exec traffic-monitor python -c "
try:
    from flask_restx import Api, Resource, fields
    print('✅ Flask-RESTX import successful')
except Exception as e:
    print(f'❌ Flask-RESTX import failed: {e}')
"

echo ""
echo "🔍 Testing Marshmallow import:"
docker exec traffic-monitor python -c "
try:
    from marshmallow import Schema, fields as ma_fields, validate
    print('✅ Marshmallow import successful')
except Exception as e:
    print(f'❌ Marshmallow import failed: {e}')
"

echo ""
echo "🔍 Testing api_models import:"
docker exec traffic-monitor python -c "
import sys
sys.path.append('/app/edge_api')
try:
    from api_models import get_model_registry
    print('✅ API models import successful')
except Exception as e:
    print(f'❌ API models import failed: {e}')
"

echo ""
echo "🚀 Testing minimal API server startup:"
docker exec traffic-monitor python -c "
import sys
sys.path.append('/app/edge_api')
try:
    from swagger_api_gateway import SwaggerAPIGateway
    gateway = SwaggerAPIGateway(host='0.0.0.0', port=5000)
    print('✅ SwaggerAPIGateway instance created successfully')
except Exception as e:
    print(f'❌ API Gateway creation failed: {e}')
    import traceback
    traceback.print_exc()
"

echo ""
echo "✅ Testing complete!"