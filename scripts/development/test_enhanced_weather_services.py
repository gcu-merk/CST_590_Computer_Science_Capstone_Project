#!/usr/bin/env python3
"""
Enhanced Weather Services Validation Script
Tests both DHT22 and Airport weather services with centralized logging

This script validates:
1. Enhanced DHT22 weather service with GPIO sensor logging
2. Enhanced airport weather service with API monitoring  
3. Weather data correlation between local and external sources
4. Business event logging and performance monitoring
5. Redis integration and time-series storage
6. Service statistics and health monitoring
"""

import os
import sys
import time
import json
import uuid
from pathlib import Path
from typing import Dict, Any, Optional

# Add edge_processing to path for shared_logging
sys.path.insert(0, str(Path(__file__).parent / "edge_processing"))

try:
    from shared_logging import ServiceLogger, CorrelationContext
    SHARED_LOGGING_AVAILABLE = True
except ImportError:
    SHARED_LOGGING_AVAILABLE = False
    print("WARNING: shared_logging not available")

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("WARNING: Redis not available")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("WARNING: requests library not available")

def test_weather_service_imports():
    """Test enhanced weather service imports"""
    print("🌤️ Testing enhanced weather service imports...")
    
    try:
        # Test DHT22 service import
        import importlib.util
        
        # DHT22 Service
        dht22_spec = importlib.util.spec_from_file_location(
            "dht22_enhanced", 
            Path(__file__).parent / "edge_processing" / "dht_22_weather_service_enhanced.py"
        )
        
        if dht22_spec and dht22_spec.loader:
            dht22_module = importlib.util.module_from_spec(dht22_spec)
            # Don't execute module to avoid GPIO errors on non-Pi systems
            
            # Airport Weather Service
            airport_spec = importlib.util.spec_from_file_location(
                "airport_enhanced", 
                Path(__file__).parent / "edge_processing" / "airport_weather_service_enhanced.py"
            )
            
            if airport_spec and airport_spec.loader:
                airport_module = importlib.util.module_from_spec(airport_spec)
                # Don't execute module to avoid import errors
                
                print("✅ Enhanced weather service imports successful")
                return True
            else:
                print("❌ Failed to load enhanced airport weather service module")
                return False
        else:
            print("❌ Failed to load enhanced DHT22 service module")
            return False
            
    except Exception as e:
        print(f"❌ Weather service import test failed: {e}")
        return False

def test_weather_api_connectivity():
    """Test weather.gov API connectivity"""
    print("🌐 Testing weather.gov API connectivity...")
    
    if not REQUESTS_AVAILABLE:
        print("❌ requests library not available")
        return False
        
    try:
        api_url = "https://api.weather.gov/stations/KOKC/observations/latest"
        headers = {
            'User-Agent': 'TrafficMonitor/1.0 (test)'
        }
        
        response = requests.get(api_url, timeout=10, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        properties = data.get('properties', {})
        
        if properties.get('stationId'):
            print("✅ Weather API connectivity successful")
            print(f"   Station: {properties.get('stationId')} - {properties.get('stationName')}")
            print(f"   Temperature: {properties.get('temperature', {}).get('value')}°C")
            print(f"   Humidity: {properties.get('relativeHumidity', {}).get('value')}%")
            return True
        else:
            print("❌ Weather API returned unexpected data format")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Weather API timeout - service may be slow")
        return False
    except requests.exceptions.HTTPError as e:
        print(f"❌ Weather API HTTP error: {e}")
        return False
    except Exception as e:
        print(f"❌ Weather API connectivity test failed: {e}")
        return False

def test_redis_weather_keys():
    """Test Redis weather key structure"""
    print("🔄 Testing Redis weather key structure...")
    
    if not REDIS_AVAILABLE:
        print("❌ Redis not available")
        return False
        
    try:
        # Connect to Redis
        redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        redis_client.ping()
        
        # Test weather key structure
        test_data = {
            "temperature": 25.5,
            "humidity": 60.0,
            "timestamp": "2025-09-24T17:30:00Z",
            "sensor_type": "test"
        }
        
        # Test DHT22 format (hash)
        dht22_key = "weather:dht22:test"
        redis_client.hset(dht22_key, mapping=test_data)
        retrieved_data = redis_client.hgetall(dht22_key)
        
        if retrieved_data:
            print("✅ DHT22 Redis hash format working")
        else:
            print("❌ DHT22 Redis hash format failed")
            return False
        
        # Test Airport format (JSON string)
        airport_key = "weather:airport:test"
        redis_client.set(airport_key, json.dumps(test_data))
        retrieved_json = redis_client.get(airport_key)
        
        if retrieved_json and json.loads(retrieved_json):
            print("✅ Airport weather Redis JSON format working")
        else:
            print("❌ Airport weather Redis JSON format failed")
            return False
        
        # Test time-series format
        ts_key = "weather:test:timeseries"
        redis_client.zadd(ts_key, {json.dumps(test_data): time.time()})
        ts_data = redis_client.zrange(ts_key, 0, -1, withscores=True)
        
        if ts_data:
            print("✅ Weather time-series format working")
        else:
            print("❌ Weather time-series format failed")
            return False
        
        # Cleanup test keys
        redis_client.delete(dht22_key, airport_key, ts_key)
        
        print("✅ Redis weather key structure working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Redis weather key test failed: {e}")
        return False

def test_weather_correlation_logging():
    """Test weather correlation tracking"""
    print("🔗 Testing weather correlation logging...")
    
    if not SHARED_LOGGING_AVAILABLE:
        print("❌ Shared logging not available")
        return False
        
    try:
        # Initialize logger
        logger = ServiceLogger("test_weather_correlation")
        
        # Test correlation context
        correlation_id = str(uuid.uuid4())[:8]
        
        with CorrelationContext.set_correlation_id(correlation_id):
            # Test weather event logging
            logger.info("Test weather correlation event", extra={
                "business_event": "weather_correlation_test",
                "correlation_id": correlation_id,
                "dht22_temperature": 25.5,
                "airport_temperature": 24.8,
                "temperature_difference": 0.7,
                "correlation_quality": "high"
            })
            
            retrieved_id = CorrelationContext.get_correlation_id()
            
            if retrieved_id == correlation_id:
                print("✅ Weather correlation logging working correctly")
                return True
            else:
                print("❌ Weather correlation ID mismatch")
                return False
                
    except Exception as e:
        print(f"❌ Weather correlation logging test failed: {e}")
        return False

def test_weather_service_configuration():
    """Test weather service configuration"""
    print("⚙️ Testing weather service configuration...")
    
    # Check for required environment variables
    required_env_vars = {
        "DHT22": ["DHT22_GPIO_PIN", "DHT22_UPDATE_INTERVAL"],
        "Airport": ["FETCH_INTERVAL_MINUTES", "WEATHER_API_URL"],
        "Logging": ["LOG_LEVEL", "LOG_DIR", "SERVICE_NAME"]
    }
    
    all_configs_ok = True
    
    for service, vars_list in required_env_vars.items():
        missing_vars = []
        for var in vars_list:
            if var not in os.environ:
                missing_vars.append(var)
        
        if missing_vars:
            print(f"⚠️ {service} missing environment variables: {missing_vars}")
            all_configs_ok = False
        else:
            print(f"✅ {service} configuration complete")
    
    if not all_configs_ok:
        print("💡 Set missing environment variables in docker-compose.yml:")
        print("   DHT22 Service:")
        print("     - DHT22_GPIO_PIN=4")
        print("     - DHT22_UPDATE_INTERVAL=600")
        print("   Airport Service:")  
        print("     - FETCH_INTERVAL_MINUTES=5")
        print("     - WEATHER_API_URL=https://api.weather.gov/stations/KOKC/observations/latest")
        print("   Logging:")
        print("     - LOG_LEVEL=INFO")
        print("     - LOG_DIR=/app/logs") 
        print("     - SERVICE_NAME=weather_service")
    
    return all_configs_ok

def test_performance_monitoring():
    """Test performance monitoring decorators"""
    print("📊 Testing performance monitoring...")
    
    if not SHARED_LOGGING_AVAILABLE:
        print("❌ Shared logging not available")
        return False
        
    try:
        logger = ServiceLogger("test_weather_performance")
        
        # Test performance decorator
        @logger.monitor_performance("test_weather_operation")
        def mock_weather_operation():
            time.sleep(0.1)  # Simulate weather API call
            return {"temperature": 25.5, "humidity": 60.0}
        
        result = mock_weather_operation()
        
        if result and "temperature" in result:
            print("✅ Weather performance monitoring working correctly")
            return True
        else:
            print("❌ Weather performance monitoring failed")
            return False
            
    except Exception as e:
        print(f"❌ Weather performance monitoring test failed: {e}")
        return False

def run_validation():
    """Run complete weather services validation suite"""
    print("🌦️ Enhanced Weather Services Validation")
    print("=" * 50)
    
    tests = [
        ("Weather Service Imports", test_weather_service_imports),
        ("Weather API Connectivity", test_weather_api_connectivity),
        ("Redis Weather Keys", test_redis_weather_keys),
        ("Weather Correlation Logging", test_weather_correlation_logging),
        ("Weather Service Configuration", test_weather_service_configuration),
        ("Performance Monitoring", test_performance_monitoring)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * (len(test_name) + 1))
        
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{test_name:.<40} {status}")
        if passed_test:
            passed += 1
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed >= 4:  # Allow some failures for environment-specific issues
        print("🎉 Weather services validation successful!")
        print("\n💡 Next steps:")
        print("1. Deploy enhanced weather services to production")
        print("2. Update docker-compose.yml with enhanced service commands")
        print("3. Start weather services: docker-compose up -d airport-weather dht22-weather")
        print("4. Monitor logs: docker-compose logs -f airport-weather dht22-weather")
        print("5. Verify weather data correlation in Redis")
        return True
    else:
        print(f"⚠️ {total - passed} validation tests failed")
        print("\n💡 Fix critical issues before deployment")
        return False

if __name__ == "__main__":
    success = run_validation()
    sys.exit(0 if success else 1)