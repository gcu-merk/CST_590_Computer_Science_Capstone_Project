#!/usr/bin/env python3
"""
Enhanced IMX500 Camera Service Validation Script
Tests the enhanced IMX500 service with centralized logging and correlation tracking

This script validates:
1. Enhanced camera service initialization with ServiceLogger
2. Correlation tracking functionality
3. Business event logging
4. Performance monitoring
5. Redis correlation with radar events
6. Centralized logging integration
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

def test_correlation_context():
    """Test correlation context functionality"""
    print("🔗 Testing CorrelationContext...")
    
    if not SHARED_LOGGING_AVAILABLE:
        print("❌ Shared logging not available")
        return False
        
    test_correlation_id = str(uuid.uuid4())
    
    with CorrelationContext.set_correlation_id(test_correlation_id):
        retrieved_id = CorrelationContext.get_correlation_id()
        
        if retrieved_id == test_correlation_id:
            print("✅ CorrelationContext working correctly")
            return True
        else:
            print(f"❌ CorrelationContext failed: expected {test_correlation_id}, got {retrieved_id}")
            return False

def test_service_logger():
    """Test ServiceLogger functionality"""
    print("📝 Testing ServiceLogger...")
    
    if not SHARED_LOGGING_AVAILABLE:
        print("❌ Shared logging not available")
        return False
        
    try:
        # Initialize logger
        logger = ServiceLogger("test_camera_service")
        
        # Test basic logging
        logger.info("Test log message", extra={
            "business_event": "test_event",
            "test_parameter": "test_value"
        })
        
        # Test performance monitoring
        @logger.monitor_performance("test_operation")
        def test_operation():
            time.sleep(0.1)  # Simulate work
            return "success"
        
        result = test_operation()
        
        if result == "success":
            print("✅ ServiceLogger working correctly")
            return True
        else:
            print("❌ ServiceLogger performance monitoring failed")
            return False
            
    except Exception as e:
        print(f"❌ ServiceLogger test failed: {e}")
        return False

def test_redis_correlation():
    """Test Redis correlation functionality"""
    print("🔄 Testing Redis correlation...")
    
    if not REDIS_AVAILABLE:
        print("❌ Redis not available")
        return False
        
    try:
        # Connect to Redis
        redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        redis_client.ping()
        
        # Create test correlation data
        correlation_id = str(uuid.uuid4())
        test_radar_data = {
            "correlation_id": correlation_id,
            "vehicle_speed": 45.5,
            "detection_time": time.time(),
            "radar_sensor_id": "test_radar"
        }
        
        # Store in Redis
        radar_key = f"radar_event:{correlation_id}"
        redis_client.setex(radar_key, 300, json.dumps(test_radar_data))  # 5 min TTL
        
        # Retrieve and validate
        stored_data = redis_client.get(radar_key)
        if stored_data:
            parsed_data = json.loads(stored_data)
            if parsed_data["correlation_id"] == correlation_id:
                print("✅ Redis correlation working correctly")
                # Cleanup
                redis_client.delete(radar_key)
                return True
            else:
                print("❌ Correlation ID mismatch in Redis data")
                return False
        else:
            print("❌ Failed to retrieve correlation data from Redis")
            return False
            
    except Exception as e:
        print(f"❌ Redis correlation test failed: {e}")
        return False

def test_camera_service_import():
    """Test enhanced camera service import"""
    print("📷 Testing enhanced camera service import...")
    
    try:
        # Import the enhanced camera service
        scripts_dir = Path(__file__).parent / "scripts"
        if scripts_dir.exists():
            sys.path.insert(0, str(scripts_dir))
            
        # Try to import the main class (without initializing camera hardware)
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "imx500_enhanced", 
            Path(__file__).parent / "scripts" / "imx500_ai_host_capture_enhanced.py"
        )
        
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Check if the main class exists
            if hasattr(module, 'IMX500AICaptureService'):
                print("✅ Enhanced camera service import successful")
                return True
            else:
                print("❌ IMX500AICaptureService class not found")
                return False
        else:
            print("❌ Failed to load enhanced camera service module")
            return False
            
    except Exception as e:
        print(f"❌ Camera service import test failed: {e}")
        return False

def test_logging_configuration():
    """Test logging configuration"""
    print("⚙️ Testing logging configuration...")
    
    # Check for required environment variables
    required_env_vars = [
        "LOG_LEVEL",
        "LOG_DIR", 
        "SERVICE_NAME"
    ]
    
    missing_vars = []
    for var in required_env_vars:
        if var not in os.environ:
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️ Missing environment variables: {missing_vars}")
        print("💡 Set these in systemd service file:")
        for var in missing_vars:
            if var == "LOG_LEVEL":
                print(f"   Environment={var}=INFO")
            elif var == "LOG_DIR":
                print(f"   Environment={var}=/mnt/storage/logs")
            elif var == "SERVICE_NAME":
                print(f"   Environment={var}=imx500_camera")
        return False
    else:
        print("✅ All required environment variables present")
        return True

def run_validation():
    """Run complete validation suite"""
    print("🚗 Enhanced IMX500 Camera Service Validation")
    print("=" * 50)
    
    tests = [
        ("Correlation Context", test_correlation_context),
        ("Service Logger", test_service_logger),
        ("Redis Correlation", test_redis_correlation), 
        ("Camera Service Import", test_camera_service_import),
        ("Logging Configuration", test_logging_configuration)
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
        print(f"{test_name:.<30} {status}")
        if passed_test:
            passed += 1
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All validation tests passed!")
        print("\n💡 Next steps:")
        print("1. Deploy enhanced camera service to Raspberry Pi")
        print("2. Start systemd service: sudo systemctl start imx500-ai-capture")
        print("3. Monitor logs: journalctl -f -u imx500-ai-capture")
        print("4. Verify correlation with radar events in production")
        return True
    else:
        print(f"⚠️ {total - passed} validation tests failed")
        print("\n💡 Fix the failing tests before deployment")
        return False

if __name__ == "__main__":
    success = run_validation()
    sys.exit(0 if success else 1)