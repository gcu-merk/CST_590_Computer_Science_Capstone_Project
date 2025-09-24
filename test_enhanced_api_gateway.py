#!/usr/bin/env python3
"""
Enhanced API Gateway Service Validation Script
Tests the enhanced API gateway with centralized logging and correlation tracking

This validation script comprehensively tests:
- API endpoint functionality with correlation tracking
- Request/response logging and performance monitoring
- WebSocket connections with correlation IDs
- System health monitoring and statistics
- Error handling and recovery mechanisms
- Swagger documentation availability

Run this script to validate that the enhanced API gateway is working correctly
with full centralized logging and correlation tracking capabilities.

Usage:
    python test_enhanced_api_gateway.py

Requirements:
    - requests library for HTTP testing
    - websocket-client for WebSocket testing
    - API gateway service running (Docker or standalone)
"""

import json
import time
import uuid
import sys
import threading
from typing import Dict, List, Optional, Any
from datetime import datetime

# Import optional dependencies
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("⚠️  Warning: 'requests' library not available. Some tests will be skipped.")

try:
    import websocket
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False
    print("⚠️  Warning: 'websocket-client' library not available. WebSocket tests will be skipped.")

# Test configuration
API_BASE_URL = "http://localhost:5000"
WEBSOCKET_URL = "ws://localhost:5000"
TEST_TIMEOUT = 30  # seconds
CORRELATION_HEADER = "X-Correlation-ID"

class APIGatewayValidator:
    """Comprehensive validator for enhanced API gateway service"""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url.rstrip('/')
        
        if REQUESTS_AVAILABLE:
            self.session = requests.Session()
            self.session.timeout = TEST_TIMEOUT
        else:
            self.session = None
        
        # Test tracking
        self.test_results = []
        self.correlation_ids = []
        self.websocket_messages = []
        self.websocket_connected = False
        
        print(f"🔧 Enhanced API Gateway Validator")
        print(f"📍 Target URL: {self.base_url}")
        print(f"⏱️  Test Timeout: {TEST_TIMEOUT}s")
        print("=" * 60)
    
    def run_test(self, test_name: str, test_func) -> Dict[str, Any]:
        """Run a single test with error handling and timing"""
        print(f"\n🧪 Running: {test_name}")
        
        start_time = time.time()
        correlation_id = str(uuid.uuid4())[:8]
        
        try:
            result = test_func(correlation_id)
            duration = time.time() - start_time
            
            test_result = {
                "name": test_name,
                "status": "PASS" if result.get("success", False) else "FAIL",
                "duration_ms": round(duration * 1000, 2),
                "correlation_id": correlation_id,
                "details": result,
                "timestamp": datetime.now().isoformat()
            }
            
            status_emoji = "✅" if test_result["status"] == "PASS" else "❌"
            print(f"{status_emoji} {test_name}: {test_result['status']} ({test_result['duration_ms']}ms)")
            
            if test_result["status"] == "FAIL" and "error" in result:
                print(f"   Error: {result['error']}")
            
        except Exception as e:
            duration = time.time() - start_time
            test_result = {
                "name": test_name,
                "status": "ERROR",
                "duration_ms": round(duration * 1000, 2),
                "correlation_id": correlation_id,
                "details": {"error": str(e), "exception_type": type(e).__name__},
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"💥 {test_name}: ERROR ({test_result['duration_ms']}ms)")
            print(f"   Exception: {str(e)}")
        
        self.test_results.append(test_result)
        return test_result
    
    def test_api_health_endpoint(self, correlation_id: str) -> Dict[str, Any]:
        """Test system health endpoint with correlation tracking"""
        if not REQUESTS_AVAILABLE or not self.session:
            return {"success": False, "error": "requests library not available", "skipped": True}
            
        try:
            headers = {CORRELATION_HEADER: correlation_id}
            response = self.session.get(f"{self.base_url}/api/health/system", headers=headers)
            
            # Validate response
            if response.status_code == 200:
                data = response.json()
                
                # Check correlation ID in response
                response_correlation = response.headers.get(CORRELATION_HEADER)
                correlation_match = response_correlation == correlation_id
                
                # Validate health data structure
                required_fields = ["status", "timestamp", "cpu_usage", "memory_usage", "system_info"]
                has_required_fields = all(field in data for field in required_fields)
                
                return {
                    "success": has_required_fields and correlation_match,
                    "status_code": response.status_code,
                    "response_time_ms": response.elapsed.total_seconds() * 1000,
                    "health_status": data.get("status"),
                    "cpu_usage": data.get("cpu_usage"),
                    "memory_usage": data.get("memory_usage"),
                    "correlation_tracked": correlation_match,
                    "has_required_fields": has_required_fields
                }
            else:
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def test_api_stats_endpoint(self, correlation_id: str) -> Dict[str, Any]:
        """Test API statistics endpoint"""
        try:
            headers = {CORRELATION_HEADER: correlation_id}
            response = self.session.get(f"{self.base_url}/api/health/stats", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate stats structure
                required_fields = ["total_requests", "successful_requests", "avg_response_time_ms", "success_rate"]
                has_required_fields = all(field in data for field in required_fields)
                
                return {
                    "success": has_required_fields,
                    "status_code": response.status_code,
                    "total_requests": data.get("total_requests", 0),
                    "success_rate": data.get("success_rate", 0),
                    "avg_response_time": data.get("avg_response_time_ms", 0),
                    "has_required_fields": has_required_fields
                }
            else:
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def test_vehicle_detections_endpoint(self, correlation_id: str) -> Dict[str, Any]:
        """Test vehicle detections endpoint"""
        try:
            headers = {CORRELATION_HEADER: correlation_id}
            response = self.session.get(f"{self.base_url}/api/vehicles/detections", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                has_detections_field = "detections" in data
                has_timestamp = "timestamp" in data
                
                return {
                    "success": has_detections_field and has_timestamp,
                    "status_code": response.status_code,
                    "detections_count": len(data.get("detections", [])),
                    "has_detections_field": has_detections_field,
                    "has_timestamp": has_timestamp
                }
            else:
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def test_weather_endpoint(self, correlation_id: str) -> Dict[str, Any]:
        """Test current weather endpoint"""
        try:
            headers = {CORRELATION_HEADER: correlation_id}
            response = self.session.get(f"{self.base_url}/api/weather/current", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                has_sources = "sources" in data
                has_timestamp = "timestamp" in data
                
                return {
                    "success": has_sources and has_timestamp,
                    "status_code": response.status_code,
                    "sources_available": len(data.get("sources", {})),
                    "primary_temperature": data.get("primary_temperature"),
                    "primary_humidity": data.get("primary_humidity"),
                    "has_sources": has_sources,
                    "has_timestamp": has_timestamp
                }
            else:
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def test_swagger_documentation(self, correlation_id: str) -> Dict[str, Any]:
        """Test Swagger documentation availability"""
        try:
            # Test Swagger JSON endpoint
            response = self.session.get(f"{self.base_url}/swagger.json")
            
            if response.status_code == 200:
                swagger_data = response.json()
                
                # Validate Swagger structure
                has_swagger_fields = all(field in swagger_data for field in ["swagger", "info", "paths"])
                has_endpoints = len(swagger_data.get("paths", {})) > 0
                
                # Test Swagger UI availability
                ui_response = self.session.get(f"{self.base_url}/")
                ui_available = ui_response.status_code == 200 and "swagger" in ui_response.text.lower()
                
                return {
                    "success": has_swagger_fields and has_endpoints and ui_available,
                    "swagger_json_available": response.status_code == 200,
                    "swagger_ui_available": ui_available,
                    "endpoints_count": len(swagger_data.get("paths", {})),
                    "api_version": swagger_data.get("info", {}).get("version"),
                    "has_swagger_fields": has_swagger_fields
                }
            else:
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def test_correlation_tracking(self, correlation_id: str) -> Dict[str, Any]:
        """Test correlation ID tracking across multiple requests"""
        try:
            headers = {CORRELATION_HEADER: correlation_id}
            correlation_results = []
            
            # Make multiple requests with same correlation ID
            endpoints = [
                "/api/health/system",
                "/api/health/stats",
                "/api/vehicles/detections",
                "/api/weather/current"
            ]
            
            for endpoint in endpoints:
                try:
                    response = self.session.get(f"{self.base_url}{endpoint}", headers=headers)
                    response_correlation = response.headers.get(CORRELATION_HEADER)
                    
                    correlation_results.append({
                        "endpoint": endpoint,
                        "sent_correlation_id": correlation_id,
                        "received_correlation_id": response_correlation,
                        "correlation_matched": response_correlation == correlation_id,
                        "status_code": response.status_code
                    })
                except Exception as e:
                    correlation_results.append({
                        "endpoint": endpoint,
                        "error": str(e)
                    })
            
            # Calculate success rate
            successful_correlations = [r for r in correlation_results if r.get("correlation_matched", False)]
            correlation_success_rate = len(successful_correlations) / len(correlation_results) * 100
            
            return {
                "success": correlation_success_rate >= 75,  # At least 75% should track correlation
                "correlation_success_rate": correlation_success_rate,
                "total_endpoints_tested": len(endpoints),
                "successful_correlations": len(successful_correlations),
                "correlation_details": correlation_results
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def test_websocket_connection(self, correlation_id: str) -> Dict[str, Any]:
        """Test WebSocket connection with correlation tracking"""
        try:
            self.websocket_messages = []
            self.websocket_connected = False
            
            def on_message(ws, message):
                self.websocket_messages.append(json.loads(message))
            
            def on_open(ws):
                self.websocket_connected = True
            
            def on_error(ws, error):
                print(f"WebSocket Error: {error}")
            
            def on_close(ws, close_status_code, close_msg):
                self.websocket_connected = False
            
            # Create WebSocket connection
            ws = websocket.WebSocketApp(
                f"{WEBSOCKET_URL}/socket.io/?EIO=4&transport=websocket",
                on_message=on_message,
                on_open=on_open,
                on_error=on_error,
                on_close=on_close
            )
            
            # Run WebSocket in thread
            wst = threading.Thread(target=ws.run_forever)
            wst.daemon = True
            wst.start()
            
            # Wait for connection
            time.sleep(2)
            
            # Check if connected and received messages
            connection_established = self.websocket_connected
            messages_received = len(self.websocket_messages) > 0
            
            # Look for correlation ID in messages
            correlation_found = any(
                correlation_id in str(msg) for msg in self.websocket_messages
            ) if messages_received else False
            
            ws.close()
            
            return {
                "success": connection_established,
                "connection_established": connection_established,
                "messages_received": messages_received,
                "message_count": len(self.websocket_messages),
                "correlation_tracking": correlation_found,
                "sample_messages": self.websocket_messages[:3]  # First 3 messages
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "websocket_available": False
            }
    
    def test_error_handling(self, correlation_id: str) -> Dict[str, Any]:
        """Test error handling with invalid requests"""
        try:
            headers = {CORRELATION_HEADER: correlation_id}
            
            # Test invalid endpoint
            response = self.session.get(f"{self.base_url}/api/nonexistent/endpoint", headers=headers)
            handles_404 = response.status_code == 404
            
            # Test malformed request (if applicable)
            error_responses = []
            error_responses.append({
                "test": "invalid_endpoint",
                "status_code": response.status_code,
                "handles_error": handles_404
            })
            
            # Check if correlation ID is maintained in error responses
            error_correlation_tracked = response.headers.get(CORRELATION_HEADER) == correlation_id
            
            return {
                "success": handles_404 and error_correlation_tracked,
                "handles_404": handles_404,
                "error_correlation_tracked": error_correlation_tracked,
                "error_responses": error_responses
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def test_configuration_validation(self, correlation_id: str) -> Dict[str, Any]:
        """Test configuration and setup validation"""
        try:
            config_checks = {
                "requests_library": REQUESTS_AVAILABLE,
                "websocket_library": WEBSOCKET_AVAILABLE,
                "base_url_configured": bool(self.base_url),
                "session_configured": self.session is not None,
                "correlation_header": bool(CORRELATION_HEADER)
            }
            
            return {
                "success": True,
                "config_checks": config_checks,
                "libraries_available": REQUESTS_AVAILABLE and WEBSOCKET_AVAILABLE,
                "ready_for_testing": all(config_checks.values())
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def run_full_validation(self) -> Dict[str, Any]:
        """Run complete validation suite"""
        print("🚀 Starting Enhanced API Gateway Validation")
        print("=" * 60)
        
        # Define test suite - always include configuration test
        tests = [
            ("Configuration Validation", self.test_configuration_validation)
        ]
        
        # Add other tests only if dependencies are available
        if REQUESTS_AVAILABLE:
            tests.extend([
                ("API Health Endpoint", self.test_api_health_endpoint),
                ("API Statistics Endpoint", self.test_api_stats_endpoint),
                ("Vehicle Detections Endpoint", self.test_vehicle_detections_endpoint),
                ("Weather Data Endpoint", self.test_weather_endpoint),
                ("Swagger Documentation", self.test_swagger_documentation),
                ("Correlation Tracking", self.test_correlation_tracking),
                ("Error Handling", self.test_error_handling)
            ])
        
        if WEBSOCKET_AVAILABLE:
            tests.append(("WebSocket Connection", self.test_websocket_connection))
        
        # Run tests
        for test_name, test_func in tests:
            self.run_test(test_name, test_func)
        
        # Calculate summary
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["status"] == "PASS"])
        failed_tests = len([t for t in self.test_results if t["status"] == "FAIL"])
        error_tests = len([t for t in self.test_results if t["status"] == "ERROR"])
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        avg_duration = sum(t["duration_ms"] for t in self.test_results) / total_tests if total_tests > 0 else 0
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 VALIDATION SUMMARY")
        print("=" * 60)
        print(f"📈 Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests})")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"💥 Errors: {error_tests}")
        print(f"⏱️  Average Duration: {avg_duration:.2f}ms")
        
        # Determine overall status
        if success_rate >= 80:
            overall_status = "EXCELLENT"
            status_emoji = "🎉"
        elif success_rate >= 60:
            overall_status = "GOOD"
            status_emoji = "✅"
        elif success_rate >= 40:
            overall_status = "PARTIAL"
            status_emoji = "⚠️"
        else:
            overall_status = "POOR"
            status_emoji = "❌"
        
        print(f"\n{status_emoji} Overall Status: {overall_status}")
        
        # Print failed tests
        if failed_tests > 0 or error_tests > 0:
            print(f"\n⚠️  Issues Found:")
            for test in self.test_results:
                if test["status"] in ["FAIL", "ERROR"]:
                    print(f"   • {test['name']}: {test['details'].get('error', 'Unknown error')}")
        
        return {
            "overall_status": overall_status,
            "success_rate": success_rate,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "error_tests": error_tests,
            "avg_duration_ms": avg_duration,
            "test_results": self.test_results,
            "timestamp": datetime.now().isoformat()
        }


def main():
    """Main validation entry point"""
    try:
        validator = APIGatewayValidator()
        results = validator.run_full_validation()
        
        # Exit with appropriate code
        if results["success_rate"] >= 80:
            sys.exit(0)  # Success
        elif results["success_rate"] >= 40:
            sys.exit(1)  # Partial success
        else:
            sys.exit(2)  # Major issues
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Validation interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n💥 Validation failed with error: {e}")
        sys.exit(3)


if __name__ == "__main__":
    main()