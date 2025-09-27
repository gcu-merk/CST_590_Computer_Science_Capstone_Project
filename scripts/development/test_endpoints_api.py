#!/usr/bin/env python3
"""
Test script for the new /api/endpoints endpoint
"""

import json
import sys
import os

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'edge_api'))

def test_endpoints_endpoint():
    """Test the /api/endpoints endpoint functionality"""
    
    print("Testing /api/endpoints endpoint...")
    
    try:
        # Mock Flask app for testing
        from unittest.mock import MagicMock
        
        # Create a mock request object
        mock_request = MagicMock()
        mock_request.url_root = "http://100.121.231.16:5000/"
        
        # Import the EdgeAPIGateway
        from edge_api_gateway import EdgeAPIGateway
        
        # Create instance
        gateway = EdgeAPIGateway()
        
        # Set up mock request context
        with gateway.app.test_request_context('/', base_url='http://100.121.231.16:5000'):
            # Get the endpoints route function
            with gateway.app.test_client() as client:
                response = client.get('/api/endpoints')
                
                if response.status_code == 200:
                    data = json.loads(response.data)
                    
                    print("✅ Endpoint response successful!")
                    print(f"📋 API Title: {data['api_info']['title']}")
                    print(f"🔗 Base URL: {data['api_info']['base_url']}")
                    
                    # Count endpoints by category
                    endpoint_counts = {}
                    for category, info in data['endpoints'].items():
                        count = len(info['endpoints'])
                        endpoint_counts[category] = count
                        print(f"📂 {category}: {count} endpoints")
                    
                    total_endpoints = sum(endpoint_counts.values())
                    print(f"📊 Total endpoints: {total_endpoints}")
                    
                    # Show some example URLs
                    print("\n🌐 Example URLs:")
                    for example in data['usage_examples']['curl_examples'][:3]:
                        print(f"   {example}")
                    
                    print("\n✅ All tests passed!")
                    return True
                else:
                    print(f"❌ Endpoint returned status code: {response.status_code}")
                    return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_endpoints_endpoint()
    exit(0 if success else 1)