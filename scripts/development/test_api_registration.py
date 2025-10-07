#!/usr/bin/env python3
"""
Specific Swagger Model Registration Diagnostic
Tests the exact same model registration used by the running API server
"""

import sys
import traceback

def test_actual_api_registration():
    """Test the exact model registration used by the running API"""
    print("🔍 Testing actual API server model registration...")
    
    try:
        # Import the exact same modules as the running API
        sys.path.insert(0, '/app')
        from flask import Flask
        from flask_restx import Api
        from edge_api.swagger_config import API_CONFIG
        from edge_api.api_models import get_model_registry
        
        # Create app and API exactly like the running server
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'traffic_monitoring_edge_api'
        app.config['RESTX_MASK_SWAGGER'] = False
        
        api = Api(
            app,
            version=API_CONFIG['version'],
            title=API_CONFIG['title'],
            description=API_CONFIG['description'],
            doc=API_CONFIG['doc'],
            contact=API_CONFIG['contact'],
            license_name=API_CONFIG['license']['name'],
            license_url=API_CONFIG['license']['url'],
            validate=True
        )
        
        # Register models exactly like the running server
        models = get_model_registry()
        print(f"📦 Attempting to register {len(models)} models...")
        
        for name, model in models.items():
            try:
                api.models[name] = model
                print(f"✅ Registered model: {name}")
            except Exception as e:
                print(f"❌ Failed to register model {name}: {e}")
                return False
        
        print("✅ All models registered successfully")
        
        # Test swagger.json generation with all models registered
        with app.test_client() as client:
            print("🔍 Testing swagger.json generation...")
            response = client.get('/swagger.json')
            
            if response.status_code == 200:
                swagger_data = response.get_json()
                definitions = swagger_data.get('definitions', {})
                print(f"✅ Swagger JSON generated successfully with {len(definitions)} definitions")
                
                # List all definitions
                print("📋 Model definitions found:")
                for def_name in sorted(definitions.keys()):
                    print(f"  - {def_name}")
                
                return True
            else:
                print(f"❌ Swagger JSON generation failed: {response.status_code}")
                error_text = response.get_data(as_text=True)
                print(f"Error: {error_text}")
                
                # Try to extract the specific error
                if "error" in error_text:
                    import json
                    try:
                        error_data = json.loads(error_text)
                        print(f"Specific error: {error_data.get('error', 'Unknown')}")
                    except (json.JSONDecodeError, ValueError) as e:
                        pass
                
                return False
                
    except Exception as e:
        print(f"❌ API registration test failed: {e}")
        traceback.print_exc()
        return False

def test_model_validation():
    """Test individual model validation"""
    print("\n🔍 Testing individual model validation...")
    
    try:
        from edge_api.api_models import get_model_registry
        from flask_restx import fields, Model
        
        models = get_model_registry()
        
        for name, model in models.items():
            try:
                # Check if it's a proper Model instance
                if not isinstance(model, Model):
                    print(f"❌ {name} is not a Model instance: {type(model)}")
                    continue
                
                # Check if it has required attributes
                if not hasattr(model, '__schema__'):
                    print(f"⚠️  {name} missing __schema__ attribute")
                    continue
                
                # Try to access the schema
                schema = model.__schema__
                print(f"✅ {name} - valid schema with {len(schema)} fields")
                
            except Exception as e:
                print(f"❌ {name} validation failed: {e}")
                
    except Exception as e:
        print(f"❌ Model validation test failed: {e}")
        traceback.print_exc()

def main():
    """Main diagnostic function"""
    print("🚨 Specific API Registration Diagnostic")
    print("=" * 50)
    
    # Test model validation first
    test_model_validation()
    
    # Test actual API registration
    success = test_actual_api_registration()
    
    if success:
        print("\n🎉 All tests passed! The API should work correctly.")
        print("🤔 If the live API still fails, there may be a runtime issue.")
    else:
        print("\n⚠️  Registration test failed. This explains the live API failure.")

if __name__ == "__main__":
    main()