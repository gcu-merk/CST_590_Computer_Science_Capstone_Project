#!/usr/bin/env python3
"""
Comprehensive API endpoint testing script
Tests all available endpoints across the traffic monitoring system
"""

import subprocess
import json
import sys
from datetime import datetime

def run_ssh_command(command):
    """Run SSH command and return result"""
    try:
        full_cmd = f'ssh merk@100.121.231.16 "{command}"'
        result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, timeout=10)
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)

def test_endpoint(url, description):
    """Test a single endpoint"""
    print(f"\n🔍 Testing: {description}")
    print(f"   URL: {url}")
    
    # Test HTTP status
    status_cmd = f"curl -s -o /dev/null -w '%{{http_code}}' {url}"
    status_code, status_output, _ = run_ssh_command(status_cmd)
    
    # Get response content
    content_cmd = f"curl -s {url}"
    content_code, content_output, _ = run_ssh_command(content_cmd)
    
    if status_code == 0 and status_output:
        status_num = int(status_output) if status_output.isdigit() else 0
        
        if status_num == 200:
            print(f"   ✅ Status: {status_num} (Success)")
            if content_output and len(content_output) < 500:
                print(f"   📄 Response: {content_output}")
            elif content_output:
                print(f"   📄 Response: {content_output[:200]}... (truncated)")
        elif status_num == 404:
            print(f"   ❌ Status: {status_num} (Not Found)")
        elif status_num == 500:
            print(f"   💥 Status: {status_num} (Server Error)")
        else:
            print(f"   ⚠️  Status: {status_num}")
            
        return status_num, content_output
    else:
        print(f"   💀 Connection Failed")
        return 0, ""

def main():
    """Test all known API endpoints"""
    print("=" * 80)
    print("🚦 COMPREHENSIVE API ENDPOINT TESTING")
    print(f"📅 Timestamp: {datetime.now().isoformat()}")
    print("=" * 80)
    
    endpoints_to_test = [
        # Basic health checks
        ("http://localhost:5000/health", "Traffic Monitor Health Check"),
        ("http://localhost/", "Nginx Root"),
        ("http://localhost:80/", "Nginx Port 80"),
        ("http://localhost:6379/", "Redis (should fail - not HTTP)"),
        
        # Swagger/Docs
        ("http://localhost:5000/docs", "Swagger UI"),
        ("http://localhost:5000/swagger.json", "Swagger JSON Spec"),
        ("http://localhost:5000/api", "API Root"),
        
        # API endpoints based on source analysis
        ("http://localhost:5000/api/health/system", "Enhanced API System Health"),
        ("http://localhost:5000/api/health/stats", "Enhanced API Stats"),
        ("http://localhost:5000/api/vehicles/detections", "Vehicle Detections"),
        ("http://localhost:5000/api/weather/current", "Current Weather"),
        ("http://localhost:5000/api/events/recent", "Recent Events"),
        ("http://localhost:5000/api/analytics", "Traffic Analytics"),
        
        # Legacy endpoint patterns
        ("http://localhost:5000/detections", "Direct Detections"),
        ("http://localhost:5000/weather", "Direct Weather"),
        ("http://localhost:5000/tracks", "Direct Tracks"),
        ("http://localhost:5000/speeds", "Direct Speeds"),
        ("http://localhost:5000/hello", "Hello Endpoint"),
        
        # Alternative ports/paths
        ("http://localhost:8080/", "Alternative Port 8080"),
        ("http://localhost:3000/", "Alternative Port 3000"),
        ("http://localhost:8443/", "HTTPS Alternative"),
    ]
    
    working_endpoints = []
    failed_endpoints = []
    
    for url, description in endpoints_to_test:
        status, response = test_endpoint(url, description)
        
        if status == 200:
            working_endpoints.append((url, description, response))
        else:
            failed_endpoints.append((url, description, status))
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    
    print(f"\n✅ WORKING ENDPOINTS ({len(working_endpoints)}):")
    for url, desc, _ in working_endpoints:
        print(f"   • {desc}: {url}")
    
    print(f"\n❌ FAILED ENDPOINTS ({len(failed_endpoints)}):")
    for url, desc, status in failed_endpoints:
        print(f"   • {desc}: {url} (Status: {status})")
    
    # Container status
    print(f"\n🐳 CONTAINER STATUS:")
    _, container_output, _ = run_ssh_command("docker ps --format 'table {{.Names}}\\t{{.Status}}'")
    print(container_output)
    
    print("\n" + "=" * 80)
    print(f"🏁 Testing completed. {len(working_endpoints)} working, {len(failed_endpoints)} failed")
    print("=" * 80)

if __name__ == "__main__":
    main()