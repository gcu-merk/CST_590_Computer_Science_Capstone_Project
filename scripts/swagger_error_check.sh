#!/bin/bash

echo "=== Swagger JSON Error Investigation ==="
echo "Date: $(date)"
echo

echo "1. Testing swagger.json with detailed error output..."
curl -v http://localhost:5000/swagger.json
echo

echo "2. Looking for Flask-RESTX specific errors in logs..."
docker logs traffic-monitor 2>&1 | grep -i -A10 -B5 "swagger\|restx\|traceback\|exception"
echo

echo "3. Testing if API models can be imported without errors..."
docker exec traffic-monitor python -c "
try:
    from edge_api.api_models import *
    print('✅ All API models imported successfully')
    
    # Test specific schema classes
    from edge_api.api_models import TimeRangeQuerySchema
    print('✅ TimeRangeQuerySchema imported')
    
    from edge_api.api_models import VehicleDetectionSchema  
    print('✅ VehicleDetectionSchema imported')
    
except Exception as e:
    print(f'❌ API models import error: {e}')
    import traceback
    traceback.print_exc()
"
echo

echo "4. Testing Flask-RESTX model registration..."
docker exec traffic-monitor python -c "
try:
    from flask import Flask
    from flask_restx import Api
    app = Flask(__name__)
    api = Api(app)
    
    # Try to import and register our models
    from edge_api.api_models import register_models
    register_models(api)
    print('✅ Model registration successful')
    
except Exception as e:
    print(f'❌ Model registration error: {e}')
    import traceback
    traceback.print_exc()
"
echo

echo "=== Investigation Complete ==="