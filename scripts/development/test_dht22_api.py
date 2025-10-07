#!/usr/bin/env python3
"""
DHT22 API Health Check Script
Tests the complete DHT22 data pipeline from Redis to API endpoint
"""

import requests
import json
import redis
import sys
from datetime import datetime

def test_redis_connection():
    """Test Redis connectivity and DHT22 data"""
    print("=" * 50)
    print("🔍 Testing Redis Connection")
    print("=" * 50)
    
    try:
        # Try both localhost and redis hostname
        for host in ['redis', 'localhost']:
            try:
                r = redis.Redis(host=host, port=6379, db=0)
                r.ping()
                print(f"✅ Redis connection ({host}): OK")
                redis_host = host
                break
            except (redis.ConnectionError, redis.TimeoutError):
                continue
        else:
            print("❌ Could not connect to Redis on any host")
            return False
        
        # Check DHT22 data
        dht22_hash = r.hgetall('weather:dht22')
        if dht22_hash:
            print("✅ DHT22 hash data found:")
            for key, value in dht22_hash.items():
                print(f"   {key.decode()}: {value.decode()}")
        else:
            print("❌ No DHT22 hash data found")
            
        # Check DHT22 latest JSON
        dht22_latest = r.get('weather:dht22:latest')
        if dht22_latest:
            print("✅ DHT22 latest JSON data found:")
            data = json.loads(dht22_latest)
            print(f"   Temperature: {data.get('temperature_c')}°C ({data.get('temperature_f')}°F)")
            print(f"   Humidity: {data.get('humidity')}%")
            print(f"   Timestamp: {data.get('timestamp')}")
        else:
            print("❌ No DHT22 latest JSON data found")
            
        return True
    except Exception as e:
        print(f"❌ Redis error: {e}")
        return False

def test_api_endpoints():
    """Test API endpoints"""
    print("\n" + "=" * 50)
    print("🌐 Testing API Endpoints")
    print("=" * 50)
    
    endpoints = [
        "http://localhost:5000/api/health",
        "http://localhost:5000/api/weather/dht22", 
        "http://localhost:5000/api/weather/latest",
        "http://localhost:5001/api/weather/dht22"  # Dedicated DHT22 API
    ]
    
    for endpoint in endpoints:
        try:
            print(f"\n🔗 Testing: {endpoint}")
            response = requests.get(endpoint, timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print("   ✅ JSON Response received")
                    if 'temperature_c' in str(data):
                        print(f"   🌡️  Contains temperature data")
                    if 'humidity' in str(data):
                        print(f"   💧 Contains humidity data")
                    print(f"   📄 Response preview: {str(data)[:100]}...")
                except (ValueError, json.JSONDecodeError) as e:
                    print(f"   📄 Raw response: {response.text[:100]}...")
            else:
                print(f"   ❌ Error response: {response.text[:100]}...")
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Connection refused - service not running")
        except requests.exceptions.Timeout:
            print(f"   ❌ Timeout - service not responding")
        except Exception as e:
            print(f"   ❌ Error: {e}")

def test_docker_containers():
    """Check Docker container status"""
    print("\n" + "=" * 50)
    print("🐳 Testing Docker Containers")
    print("=" * 50)
    
    import subprocess
    
    try:
        # Check for DHT22 related containers
        result = subprocess.run(['docker', 'ps', '--filter', 'name=dht22'], 
                               capture_output=True, text=True)
        if result.stdout.strip():
            print("✅ DHT22 containers found:")
            print(result.stdout)
        else:
            print("❌ No DHT22 containers running")
            
        # Check for API containers
        result = subprocess.run(['docker', 'ps', '--filter', 'name=traffic-monitor'], 
                               capture_output=True, text=True)
        if result.stdout.strip():
            print("\n✅ API containers found:")
            print(result.stdout)
        else:
            print("❌ No API containers running")
            
    except Exception as e:
        print(f"❌ Docker check error: {e}")

def main():
    """Run complete DHT22 health check"""
    print(f"DHT22 Health Check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test Redis
    redis_ok = test_redis_connection()
    
    # Test APIs
    test_api_endpoints()
    
    # Test Docker
    test_docker_containers()
    
    print("\n" + "=" * 50)
    print("📊 Health Check Summary")
    print("=" * 50)
    print(f"Redis Connection: {'✅ OK' if redis_ok else '❌ FAILED'}")
    print("\nFor detailed container logs, run:")
    print("docker logs dht22-weather")
    print("docker logs traffic-monitor")

if __name__ == "__main__":
    main()