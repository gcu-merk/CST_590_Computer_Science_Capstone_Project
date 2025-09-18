#!/usr/bin/env python3
"""
Swagger API Test Suite
Comprehensive testing for the Swagger-enabled Traffic Monitoring API
"""

import sys
import json
import time
import requests
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from datetime import datetime

# Add edge_api directory to Python path
sys.path.append(str(Path(__file__).parent))

class SwaggerAPITestSuite(unittest.TestCase):
    """Test suite for Swagger-enabled API"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.base_url = "http://localhost:5000"
        cls.api_url = f"{cls.base_url}/api"
        cls.docs_url = f"{cls.base_url}/docs/"
        cls.swagger_json_url = f"{cls.api_url}/swagger.json"
    
    def test_swagger_imports(self):
        """Test that all Swagger modules can be imported"""
        try:
            from swagger_config import API_CONFIG, create_api_models
            from api_models import get_model_registry, system_health_schema
            from swagger_ui_config import get_swagger_config
            from swagger_api_gateway import SwaggerAPIGateway
            
            self.assertTrue(True, "All imports successful")
            
        except ImportError as e:
            self.fail(f"Import failed: {e}")
    
    def test_api_configuration(self):
        """Test API configuration validity"""
        from swagger_config import API_CONFIG
        
        # Check required fields
        required_fields = ['version', 'title', 'description', 'doc', 'tags']
        for field in required_fields:
            self.assertIn(field, API_CONFIG, f"Missing required field: {field}")
        
        # Check version format
        self.assertRegex(API_CONFIG['version'], r'^\d+\.\d+\.\d+$', "Invalid version format")
        
        # Check tags structure
        self.assertIsInstance(API_CONFIG['tags'], list, "Tags must be a list")
        for tag in API_CONFIG['tags']:
            self.assertIn('name', tag, "Tag missing name")
            self.assertIn('description', tag, "Tag missing description")
    
    def test_model_registry(self):
        """Test API model registry"""
        from api_models import get_model_registry
        
        models = get_model_registry()
        
        # Check that models exist
        self.assertIsInstance(models, dict, "Model registry must be a dictionary")
        self.assertGreater(len(models), 0, "No models found in registry")
        
        # Check required models
        required_models = [
            'SystemHealth', 'VehicleDetection', 'SpeedDetection',
            'WeatherData', 'TrafficAnalytics', 'ErrorResponse'
        ]
        
        for model_name in required_models:
            self.assertIn(model_name, models, f"Missing required model: {model_name}")
    
    def test_schema_validation(self):
        """Test schema validation functionality"""
        from api_models import (
            system_health_schema, vehicle_detection_schema,
            speed_detection_schema, error_response_schema
        )
        
        # Test valid data
        valid_health_data = {
            'status': 'healthy',
            'timestamp': datetime.now(),
            'uptime_seconds': 3600.5,
            'cpu_usage': 45.2,
            'memory_usage': 62.8,
            'services': {'redis': 'connected'}
        }
        
        try:
            result = system_health_schema.load(valid_health_data)
            self.assertIsInstance(result, dict, "Schema validation should return dict")
        except Exception as e:
            self.fail(f"Valid data failed validation: {e}")
        
        # Test invalid data
        invalid_health_data = {
            'status': 'invalid_status',  # Invalid enum value
            'cpu_usage': 150  # Out of range
        }
        
        with self.assertRaises(Exception, msg="Invalid data should raise exception"):
            system_health_schema.load(invalid_health_data)
    
    def test_swagger_gateway_initialization(self):
        """Test Swagger API Gateway initialization"""
        from swagger_api_gateway import SwaggerAPIGateway
        
        try:
            # Create gateway instance
            gateway = SwaggerAPIGateway(host='localhost', port=5001)
            
            # Check initialization
            self.assertIsNotNone(gateway.app, "Flask app not initialized")
            self.assertIsNotNone(gateway.api, "Flask-RESTX API not initialized")
            self.assertIsNotNone(gateway.socketio, "SocketIO not initialized")
            
            # Check configuration
            self.assertEqual(gateway.host, 'localhost')
            self.assertEqual(gateway.port, 5001)
            self.assertFalse(gateway.is_running)
            
        except Exception as e:
            self.fail(f"Gateway initialization failed: {e}")
    
    def test_namespace_setup(self):
        """Test API namespace configuration"""
        from swagger_api_gateway import SwaggerAPIGateway
        
        gateway = SwaggerAPIGateway()
        
        # Check that namespaces are registered
        namespaces = [ns.name for ns in gateway.api.namespaces]
        
        expected_namespaces = ['system', 'vehicle-detection', 'speed-analysis', 'weather', 'analytics']
        for ns_name in expected_namespaces:
            self.assertIn(ns_name, namespaces, f"Missing namespace: {ns_name}")
    
    def test_route_registration(self):
        """Test that routes are properly registered"""
        from swagger_api_gateway import SwaggerAPIGateway
        
        gateway = SwaggerAPIGateway()
        
        # Get all registered routes
        routes = [rule.rule for rule in gateway.app.url_map.iter_rules()]
        
        # Check critical routes
        expected_routes = [
            '/api/health',
            '/api/detections',
            '/api/speeds',
            '/api/weather',
            '/api/analytics',
            '/docs/',
            '/'
        ]
        
        for route in expected_routes:
            route_found = any(route in registered_route for registered_route in routes)
            self.assertTrue(route_found, f"Route not found: {route}")
    
    def test_swagger_ui_config(self):
        """Test Swagger UI configuration"""
        from swagger_ui_config import (
            get_swagger_config, get_swagger_ui_config,
            get_openapi_enhancements, get_response_examples
        )
        
        # Test configuration objects
        swagger_config = get_swagger_config()
        ui_config = get_swagger_ui_config()
        enhancements = get_openapi_enhancements()
        examples = get_response_examples()
        
        # Validate structure
        self.assertIsInstance(swagger_config, dict)
        self.assertIsInstance(ui_config, dict)
        self.assertIsInstance(enhancements, dict)
        self.assertIsInstance(examples, dict)
        
        # Check critical config values
        self.assertIn('title', swagger_config)
        self.assertIn('tryItOutEnabled', ui_config)
        self.assertIn('info', enhancements)
        self.assertTrue(len(examples) > 0)
    
    def test_error_handling(self):
        """Test error handling in API endpoints"""
        from swagger_api_gateway import SwaggerAPIGateway
        
        gateway = SwaggerAPIGateway()
        
        with gateway.app.test_client() as client:
            # Test invalid parameter
            response = client.get('/api/detections?seconds=invalid')
            self.assertIn(response.status_code, [400, 422], "Should return validation error")
            
            # Test out-of-range parameter
            response = client.get('/api/detections?seconds=999999')
            self.assertIn(response.status_code, [400, 422], "Should return range validation error")
    
    def test_legacy_compatibility(self):
        """Test backward compatibility with legacy endpoints"""
        from swagger_api_gateway import SwaggerAPIGateway
        
        gateway = SwaggerAPIGateway()
        
        with gateway.app.test_client() as client:
            # Test legacy hello endpoint
            response = client.get('/')
            self.assertEqual(response.status_code, 200)
            
            data = json.loads(response.data)
            self.assertIn('message', data)
            self.assertIn('documentation', data)
            
            # Test alternative hello endpoint
            response = client.get('/hello')
            self.assertEqual(response.status_code, 200)
    
    def test_cors_configuration(self):
        """Test CORS configuration"""
        from swagger_api_gateway import SwaggerAPIGateway
        
        gateway = SwaggerAPIGateway()
        
        with gateway.app.test_client() as client:
            # Test OPTIONS request
            response = client.options('/api/health')
            
            # Should not return error (CORS should be enabled)
            self.assertNotEqual(response.status_code, 405)
    
    def test_response_schemas(self):
        """Test response schema consistency"""
        from swagger_api_gateway import SwaggerAPIGateway
        
        gateway = SwaggerAPIGateway()
        
        with gateway.app.test_client() as client:
            # Test health endpoint response structure
            response = client.get('/api/health')
            self.assertEqual(response.status_code, 200)
            
            data = json.loads(response.data)
            
            # Check required fields
            self.assertIn('status', data)
            self.assertIn('timestamp', data)
            self.assertIn('services', data)
            
            # Check data types
            self.assertIsInstance(data['status'], str)
            self.assertIsInstance(data['services'], dict)

class SwaggerIntegrationTest(unittest.TestCase):
    """Integration tests for Swagger API with live server"""
    
    @classmethod
    def setUpClass(cls):
        """Set up integration test environment"""
        cls.base_url = "http://localhost:5000"
        cls.timeout = 5
    
    @unittest.skip("Requires running server")
    def test_swagger_ui_accessibility(self):
        """Test that Swagger UI is accessible"""
        try:
            response = requests.get(f"{self.base_url}/docs/", timeout=self.timeout)
            self.assertEqual(response.status_code, 200)
            self.assertIn('swagger', response.text.lower())
        except requests.exceptions.RequestException:
            self.skipTest("Server not running for integration test")
    
    @unittest.skip("Requires running server")
    def test_openapi_spec_validity(self):
        """Test that OpenAPI specification is valid"""
        try:
            response = requests.get(f"{self.base_url}/api/swagger.json", timeout=self.timeout)
            self.assertEqual(response.status_code, 200)
            
            spec = response.json()
            
            # Check OpenAPI structure
            self.assertIn('openapi', spec)
            self.assertIn('info', spec)
            self.assertIn('paths', spec)
            
            # Check version
            self.assertTrue(spec['openapi'].startswith('3.'))
            
        except requests.exceptions.RequestException:
            self.skipTest("Server not running for integration test")
    
    @unittest.skip("Requires running server")
    def test_endpoint_functionality(self):
        """Test actual endpoint functionality"""
        endpoints = [
            '/api/health',
            '/api/detections',
            '/api/speeds',
            '/api/weather',
            '/api/analytics'
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=self.timeout)
                self.assertIn(response.status_code, [200, 404, 500], 
                            f"Unexpected status for {endpoint}: {response.status_code}")
            except requests.exceptions.RequestException:
                self.skipTest("Server not running for integration test")

def run_swagger_tests():
    """Run all Swagger API tests"""
    print("🧪 Running Swagger API Test Suite")
    print("=" * 50)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add unit tests
    test_suite.addTest(unittest.makeSuite(SwaggerAPITestSuite))
    
    # Add integration tests (will be skipped if server not running)
    test_suite.addTest(unittest.makeSuite(SwaggerIntegrationTest))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("✅ All tests passed!")
        print(f"📊 Tests run: {result.testsRun}")
        print(f"🚀 Swagger API implementation is ready for deployment")
    else:
        print(f"❌ Tests failed: {len(result.failures)} failures, {len(result.errors)} errors")
        print(f"📊 Tests run: {result.testsRun}")
        
        if result.failures:
            print("\n🔍 Failures:")
            for test, traceback in result.failures:
                print(f"   - {test}: {traceback.split('AssertionError:')[-1].strip()}")
        
        if result.errors:
            print("\n💥 Errors:")
            for test, traceback in result.errors:
                print(f"   - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    try:
        success = run_swagger_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Tests cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test execution failed: {e}")
        sys.exit(1)