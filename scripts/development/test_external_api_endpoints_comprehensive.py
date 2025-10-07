#!/usr/bin/env python3
"""
Comprehensive External API endpoint testing script
Tests all API endpoints that the dashboard will actually use
"""

import requests
import json
import sys
from datetime import datetime
import subprocess

def test_endpoint_direct(url, description):
    """Test a single endpoint directly (for external access)"""
    print(f"\n🔍 Testing: {description}")
    print(f"   URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        status_code = response.status_code
        
        if status_code == 200:
            print(f"   ✅ Status: {status_code} (Success)")
            try:
                json_data = response.json()
                print(f"   📄 Response: {json.dumps(json_data, indent=2)[:200]}...")
            except (json.JSONDecodeError, ValueError) as e:
                text_data = response.text
                if text_data and len(text_data) < 500:
                    print(f"   📄 Response: {text_data}")
                elif text_data:
                    print(f"   📄 Response: {text_data[:200]}... (truncated)")
        elif status_code == 404:
            print(f"   ❌ Status: {status_code} (Not Found)")
        elif status_code == 500:
            print(f"   💥 Status: {status_code} (Server Error)")
        else:
            print(f"   ⚠️  Status: {status_code}")
            
        return status_code, response.text
        
    except requests.exceptions.ConnectionError:
        print(f"   💀 Connection Failed - Cannot reach server")
        return 0, ""
    except requests.exceptions.Timeout:
        print(f"   ⏰ Request Timeout")
        return 0, ""
    except Exception as e:
        print(f"   💀 Error: {str(e)}")
        return 0, ""

def test_ssh_endpoint(url, description):
    """Test endpoint via SSH (for internal Pi testing)"""
    print(f"\n🔍 Testing (SSH): {description}")
    print(f"   URL: {url}")
    
    try:
        # Test HTTP status
        status_cmd = f'ssh merk@100.121.231.16 "curl -s -o /dev/null -w \'%{{http_code}}\' {url}"'
        result = subprocess.run(status_cmd, shell=True, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and result.stdout:
            status_num = int(result.stdout) if result.stdout.isdigit() else 0
            
            if status_num == 200:
                print(f"   ✅ Status: {status_num} (Success)")
                # Get content
                content_cmd = f'ssh merk@100.121.231.16 "curl -s {url}"'
                content_result = subprocess.run(content_cmd, shell=True, capture_output=True, text=True, timeout=10)
                if content_result.stdout:
                    print(f"   📄 Response: {content_result.stdout[:200]}...")
            elif status_num == 404:
                print(f"   ❌ Status: {status_num} (Not Found)")
            elif status_num == 500:
                print(f"   💥 Status: {status_num} (Server Error)")
            else:
                print(f"   ⚠️  Status: {status_num}")
                
            return status_num, ""
        else:
            print(f"   💀 SSH Connection Failed")
            return 0, ""
            
    except Exception as e:
        print(f"   💀 SSH Error: {str(e)}")
        return 0, ""

def get_container_status():
    """Get Docker container status from Pi"""
    try:
        cmd = 'ssh merk@100.121.231.16 "docker ps --format \'table {{.Names}}\\t{{.Status}}\'"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return result.stdout if result.returncode == 0 else "Failed to get container status"
    except (subprocess.SubprocessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
        return "SSH connection failed"

def main():
    """Test all known API endpoints"""
    print("=" * 80)
    print("🚦 COMPREHENSIVE EXTERNAL API ENDPOINT TESTING")
    print(f"📅 Timestamp: {datetime.now().isoformat()}")
    print("=" * 80)
    
    # External endpoints that the dashboard should access
    external_endpoints = [
        ("https://100.121.231.16:8443/api/health/system", "External API System Health"),
        ("https://100.121.231.16:8443/api/health/stats", "External API Stats"),
        ("https://100.121.231.16:8443/api/vehicles/detections", "External Vehicle Detections"),
        ("https://100.121.231.16:8443/api/weather/current", "External Current Weather"),
        ("https://100.121.231.16:8443/api/events/recent", "External Recent Events"),
        ("https://100.121.231.16:8443/api/analytics", "External Traffic Analytics"),
        ("https://100.121.231.16:8443/api", "External API Root"),
        ("https://100.121.231.16:8443/docs", "External Swagger UI"),
        ("https://100.121.231.16:8443/swagger.json", "External Swagger JSON"),
    ]
    
    # Internal endpoints (via SSH) for comparison
    internal_endpoints = [
        ("http://localhost:5000/api/health/system", "Internal API System Health"),
        ("http://localhost:5000/api/health/stats", "Internal API Stats"),
        ("http://localhost:5000/api/vehicles/detections", "Internal Vehicle Detections"),
        ("http://localhost:5000/api/weather/current", "Internal Current Weather"),
        ("http://localhost:5000/api/events/recent", "Internal Recent Events"),
        ("http://localhost:5000/api/analytics", "Internal Traffic Analytics"),
        ("http://localhost:5000/api", "Internal API Root"),
        ("http://localhost:5000/docs", "Internal Swagger UI"),
        ("http://localhost:5000/swagger.json", "Internal Swagger JSON"),
        ("http://localhost:5000/health", "Internal Basic Health"),
    ]
    
    external_working = []
    external_failed = []
    internal_working = []
    internal_failed = []
    
    print("\n🌐 TESTING EXTERNAL ENDPOINTS (Dashboard Access)")
    print("=" * 50)
    
    for url, description in external_endpoints:
        status, response = test_endpoint_direct(url, description)
        
        if status == 200:
            external_working.append((url, description, response))
        else:
            external_failed.append((url, description, status))
    
    print("\n🏠 TESTING INTERNAL ENDPOINTS (Pi localhost)")
    print("=" * 50)
    
    for url, description in internal_endpoints:
        status, response = test_ssh_endpoint(url, description)
        
        if status == 200:
            internal_working.append((url, description, response))
        else:
            internal_failed.append((url, description, status))
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    
    print(f"\n🌐 EXTERNAL ENDPOINTS (Dashboard Access):")
    print(f"✅ Working: {len(external_working)}, ❌ Failed: {len(external_failed)}")
    
    if external_working:
        print("   ✅ WORKING:")
        for url, desc, _ in external_working:
            print(f"      • {desc}")
    
    if external_failed:
        print("   ❌ FAILED:")
        for url, desc, status in external_failed:
            print(f"      • {desc} (Status: {status})")
    
    print(f"\n🏠 INTERNAL ENDPOINTS (Pi localhost):")
    print(f"✅ Working: {len(internal_working)}, ❌ Failed: {len(internal_failed)}")
    
    if internal_working:
        print("   ✅ WORKING:")
        for url, desc, _ in internal_working:
            print(f"      • {desc}")
    
    if internal_failed:
        print("   ❌ FAILED:")
        for url, desc, status in internal_failed:
            print(f"      • {desc} (Status: {status})")
    
    # Container status
    print(f"\n🐳 CONTAINER STATUS:")
    container_status = get_container_status()
    print(container_status)
    
    print("\n" + "=" * 80)
    print(f"🏁 Testing completed.")
    print(f"🌐 External: {len(external_working)} working, {len(external_failed)} failed")
    print(f"🏠 Internal: {len(internal_working)} working, {len(internal_failed)} failed")
    print("=" * 80)
    
    # Analysis and recommendations
    if external_working:
        print(f"\n✅ DASHBOARD READY: {len(external_working)} external endpoints working")
    else:
        print(f"\n⚠️  DASHBOARD ISSUE: No external endpoints accessible")
        if internal_working:
            print("   Internal endpoints work - likely nginx/SSL configuration issue")
        else:
            print("   No internal endpoints work - API service may be down")

if __name__ == "__main__":
    main()