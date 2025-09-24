#!/usr/bin/env python3
"""
Swagger Issue Diagnostic Script
Runs on the Pi to identify the cause of "Unable to render schema" error
"""

import sys
import traceback
import json

def test_imports():
    """Test all necessary imports"""
    print("🔍 Testing imports...")
    
    try:
        from flask import Flask
        print("✅ Flask import successful")
    except Exception as e:
        print(f"❌ Flask import failed: {e}")
        return False
        
    try:
        from flask_restx import Api, Resource, fields, Model
        print("✅ Flask-RESTX import successful")
    except Exception as e:
        print(f"❌ Flask-RESTX import failed: {e}")
        return False
        
    try:
        from marshmallow import Schema, fields as ma_fields
        print("✅ Marshmallow import successful")
    except Exception as e:
        print(f"❌ Marshmallow import failed: {e}")
        return False
    
    return True

def test_api_models():
    """Test API model imports"""
    print("\n🔍 Testing API model imports...")
    
    try:
        sys.path.insert(0, '/app')
        from edge_api.api_models import get_model_registry
        print("✅ get_model_registry import successful")
        
        # Try to get the models
        models = get_model_registry()
        print(f"✅ Model registry contains {len(models)} models")
        
        # Check if models are valid
        for name, model in models.items():
            if hasattr(model, '__schema__'):
                print(f"✅ Model {name} has valid schema")
            else:
                print(f"⚠️  Model {name} missing schema attribute")
                
    except Exception as e:
        print(f"❌ API models test failed: {e}")
        traceback.print_exc()
        return False
    
    return True

def test_swagger_config():
    """Test swagger configuration"""
    print("\n🔍 Testing Swagger configuration...")
    
    try:
        from edge_api.swagger_config import API_CONFIG, create_api_models
        print("✅ Swagger config import successful")
        
        # Test API config
        print(f"✅ API title: {API_CONFIG.get('title', 'Not set')}")
        print(f"✅ API version: {API_CONFIG.get('version', 'Not set')}")
        
        # Try to create models
        models = create_api_models()
        print(f"✅ Created {len(models)} models from swagger_config")
        
    except Exception as e:
        print(f"❌ Swagger config test failed: {e}")
        traceback.print_exc()
        return False
    
    return True

def test_minimal_api():
    """Test creating a minimal Flask-RESTX API"""
    print("\n🔍 Testing minimal API creation...")
    
    try:
        from flask import Flask
        from flask_restx import Api, fields, Model
        
        app = Flask(__name__)
        api = Api(app, validate=False)  # Disable validation initially
        
        # Create a simple model
        test_model = api.model('TestModel', {
            'id': fields.String(required=True),
            'name': fields.String(required=True)
        })
        
        print("✅ Minimal API creation successful")
        
        # Test swagger.json generation
        with app.test_client() as client:
            response = client.get('/swagger.json')
            if response.status_code == 200:
                print("✅ Swagger JSON generation successful")
                return True
            else:
                print(f"❌ Swagger JSON failed: {response.status_code}")
                print(f"Response: {response.get_data(as_text=True)}")
                return False
                
    except Exception as e:
        print(f"❌ Minimal API test failed: {e}")
        traceback.print_exc()
        return False

def test_full_api_creation():
    """Test creating the full API with all models"""
    print("\n🔍 Testing full API creation...")
    
    try:
        from flask import Flask
        from flask_restx import Api
        from edge_api.swagger_config import API_CONFIG
        from edge_api.api_models import get_model_registry
        
        app = Flask(__name__)
        api = Api(
            app,
            version=API_CONFIG['version'],
            title=API_CONFIG['title'],
            description=API_CONFIG['description'],
            validate=True
        )
        
        # Register models
        models = get_model_registry()
        for name, model in models.items():
            api.models[name] = model
            
        print("✅ Full API creation successful")
        
        # Test swagger.json generation
        with app.test_client() as client:
            response = client.get('/swagger.json')
            if response.status_code == 200:
                print("✅ Full API Swagger JSON generation successful")
                swagger_data = response.get_json()
                print(f"✅ Swagger contains {len(swagger_data.get('definitions', {}))} definitions")
                return True
            else:
                print(f"❌ Full API Swagger JSON failed: {response.status_code}")
                print(f"Response: {response.get_data(as_text=True)}")
                return False
                
    except Exception as e:
        print(f"❌ Full API test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Main diagnostic function"""
    print("🚨 Swagger Issue Diagnostic Tool")
    print("=" * 40)
    
    # Run all tests
    tests = [
        ("Import Test", test_imports),
        ("API Models Test", test_api_models),
        ("Swagger Config Test", test_swagger_config),
        ("Minimal API Test", test_minimal_api),
        ("Full API Test", test_full_api_creation)
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name}...")
        results[test_name] = test_func()
    
    # Summary
    print("\n" + "=" * 40)
    print("📊 TEST RESULTS SUMMARY:")
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    if all(results.values()):
        print("\n🎉 All tests passed! The issue might be elsewhere.")
    else:
        print("\n⚠️  Some tests failed. Check the error details above.")

if __name__ == "__main__":
    main()