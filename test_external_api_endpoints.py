#!/usr/bin/env python3
"""
Comprehensive External API Endpoint Testing
Tests all available endpoints at edge-traffic-monitoring.taild46447.ts.net
"""

import requests
import json
import sys
from datetime import datetime
import urllib3
from urllib.parse import urljoin

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ExternalAPITester:
    def __init__(self):
        self.base_url = "https://edge-traffic-monitoring.taild46447.ts.net"
        self.timeout = 10
        self.session = requests.Session()
        # Configure session for potential SSL issues
        self.session.verify = False
        self.results = []
        
    def test_endpoint(self, path, description, method='GET', data=None, headers=None):
        """Test a single endpoint"""
        url = urljoin(self.base_url, path)
        print(f"\n🔍 Testing: {description}")
        print(f"   URL: {url}")
        print(f"   Method: {method}")
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, timeout=self.timeout, headers=headers)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, timeout=self.timeout, headers=headers)
            elif method.upper() == 'OPTIONS':
                response = self.session.options(url, timeout=self.timeout, headers=headers)
            else:
                response = self.session.request(method, url, timeout=self.timeout, headers=headers)
            
            status = response.status_code
            
            if status == 200:
                print(f"   ✅ Status: {status} (Success)")
                content = response.text
                if len(content) < 500:
                    print(f"   📄 Response: {content}")
                else:
                    print(f"   📄 Response: {content[:200]}... (truncated)")
                
                # Try to parse as JSON
                try:
                    json_data = response.json()
                    print(f"   📊 JSON Keys: {list(json_data.keys()) if isinstance(json_data, dict) else 'Array'}")
                except:
                    pass
                    
            elif status == 404:
                print(f"   ❌ Status: {status} (Not Found)")
            elif status == 500:
                print(f"   💥 Status: {status} (Server Error)")
                print(f"   📄 Error: {response.text[:200]}")
            elif status == 301 or status == 302:
                print(f"   🔄 Status: {status} (Redirect)")
                print(f"   📍 Location: {response.headers.get('Location', 'Not specified')}")
            elif status == 403:
                print(f"   🚫 Status: {status} (Forbidden)")
            else:
                print(f"   ⚠️  Status: {status}")
                if response.text:
                    print(f"   📄 Response: {response.text[:200]}")
            
            self.results.append({
                'url': url,
                'description': description,
                'method': method,
                'status': status,
                'success': status == 200,
                'response_size': len(response.text),
                'headers': dict(response.headers)
            })
            
            return status, response.text
            
        except requests.exceptions.Timeout:
            print(f"   ⏰ Timeout after {self.timeout} seconds")
            self.results.append({'url': url, 'description': description, 'status': 'timeout', 'success': False})
            return 0, "Timeout"
        except requests.exceptions.ConnectionError as e:
            print(f"   💀 Connection Failed: {str(e)}")
            self.results.append({'url': url, 'description': description, 'status': 'connection_error', 'success': False})
            return 0, "Connection Error"
        except requests.exceptions.SSLError as e:
            print(f"   🔒 SSL Error: {str(e)}")
            self.results.append({'url': url, 'description': description, 'status': 'ssl_error', 'success': False})
            return 0, "SSL Error"
        except Exception as e:
            print(f"   💥 Unexpected Error: {str(e)}")
            self.results.append({'url': url, 'description': description, 'status': 'error', 'success': False})
            return 0, str(e)

def main():
    """Test all external API endpoints"""
    print("=" * 90)
    print("🌐 EXTERNAL API ENDPOINT TESTING")
    print("🎯 Target: edge-traffic-monitoring.taild46447.ts.net")
    print(f"📅 Timestamp: {datetime.now().isoformat()}")
    print("=" * 90)
    
    tester = ExternalAPITester()
    
    # Test endpoints based on our analysis of the API gateway
    endpoints_to_test = [
        # Basic connectivity
        ("/", "Root/Home Page", "GET"),
        
        # Health checks
        ("/health", "Basic Health Check", "GET"),
        
        # Swagger/Documentation  
        ("/docs", "Swagger UI Documentation", "GET"),
        ("/docs/", "Swagger UI Documentation (trailing slash)", "GET"),
        ("/swagger.json", "OpenAPI/Swagger Specification", "GET"),
        ("/openapi.json", "Alternative OpenAPI Spec", "GET"),
        
        # API endpoints (based on source code analysis)
        ("/api", "API Root", "GET"),
        ("/api/", "API Root (trailing slash)", "GET"),
        
        # Health/System endpoints
        ("/api/health/system", "Enhanced System Health", "GET"),
        ("/api/health/stats", "System Statistics", "GET"),
        
        # Vehicle detection endpoints
        ("/api/vehicles/detections", "Vehicle Detections", "GET"),
        ("/api/vehicles/detections?seconds=30", "Vehicle Detections (30s)", "GET"),
        
        # Weather endpoints
        ("/api/weather/current", "Current Weather", "GET"),
        ("/api/weather", "Weather Data", "GET"),
        
        # Event endpoints
        ("/api/events/recent", "Recent Events", "GET"),
        ("/api/events/broadcast", "Event Broadcast", "POST"),
        
        # Analytics endpoints
        ("/api/analytics", "Traffic Analytics", "GET"),
        
        # Direct endpoints (legacy patterns)
        ("/detections", "Direct Vehicle Detections", "GET"),
        ("/weather", "Direct Weather", "GET"),
        ("/tracks", "Vehicle Tracks", "GET"),
        ("/speeds", "Speed Detections", "GET"),
        ("/hello", "Hello Endpoint", "GET"),
        
        # CORS preflight test
        ("/api/health/system", "CORS Preflight Test", "OPTIONS"),
    ]
    
    for path, description, method in endpoints_to_test:
        data = None
        headers = None
        
        # Add special handling for POST requests
        if method == "POST" and "broadcast" in path:
            data = {"message": "Test event", "source": "external_test"}
            headers = {"Content-Type": "application/json"}
        
        # Add CORS headers for OPTIONS
        if method == "OPTIONS":
            headers = {
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Content-Type",
                "Origin": "https://gcu-merk.github.io"
            }
        
        tester.test_endpoint(path, description, method, data, headers)
    
    # Summary
    print("\n" + "=" * 90)
    print("📊 EXTERNAL API TEST SUMMARY")
    print("=" * 90)
    
    working_endpoints = [r for r in tester.results if r.get('success', False)]
    failed_endpoints = [r for r in tester.results if not r.get('success', False)]
    
    print(f"\n✅ WORKING ENDPOINTS ({len(working_endpoints)}):")
    for result in working_endpoints:
        print(f"   • {result['description']}: {result['url']} (Status: {result['status']})")
    
    print(f"\n❌ FAILED/UNAVAILABLE ENDPOINTS ({len(failed_endpoints)}):")
    for result in failed_endpoints:
        status = result.get('status', 'unknown')
        print(f"   • {result['description']}: {result['url']} (Status: {status})")
    
    # Additional analysis
    if working_endpoints:
        print(f"\n📈 EXTERNAL ACCESS ANALYSIS:")
        print(f"   • Total endpoints tested: {len(tester.results)}")
        print(f"   • Success rate: {len(working_endpoints)}/{len(tester.results)} ({len(working_endpoints)/len(tester.results)*100:.1f}%)")
        
        # Check for common patterns in working endpoints
        working_paths = [r['url'] for r in working_endpoints]
        if any('/health' in path for path in working_paths):
            print(f"   • ✅ Health monitoring accessible externally")
        if any('/api/' in path for path in working_paths):
            print(f"   • ✅ REST API endpoints accessible externally")
        if any('/docs' in path for path in working_paths):
            print(f"   • ✅ API documentation accessible externally")
        if any('swagger' in path for path in working_paths):
            print(f"   • ✅ Swagger specification accessible externally")
    
    print(f"\n🔐 SECURITY CONSIDERATIONS:")
    print(f"   • Using HTTPS with Tailscale SSL certificates")
    print(f"   • CORS configured for https://gcu-merk.github.io")
    print(f"   • External access via Tailscale network (100.121.231.16)")
    
    print("\n" + "=" * 90)
    print(f"🏁 External API testing completed.")
    print(f"🌐 Domain: edge-traffic-monitoring.taild46447.ts.net")
    print(f"📡 Results: {len(working_endpoints)} working, {len(failed_endpoints)} failed/unavailable")
    print("=" * 90)
    
    # Save results to file
    results_file = "external_api_test_results.json"
    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'base_url': tester.base_url,
            'total_tests': len(tester.results),
            'successful_tests': len(working_endpoints),
            'results': tester.results
        }, f, indent=2)
    
    print(f"\n💾 Results saved to: {results_file}")

if __name__ == "__main__":
    main()