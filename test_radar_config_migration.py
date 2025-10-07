#!/usr/bin/env python3
"""
Test Configuration Loading for Radar Service

This script verifies that radar_service.py can load configuration correctly
from the centralized config system.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_config_import():
    """Test that config module can be imported"""
    print("Testing config import...")
    try:
        from config.settings import get_config
        print("✅ Config module imported successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import config: {e}")
        return False

def test_config_loading():
    """Test that configuration loads with defaults"""
    print("\nTesting configuration loading...")
    try:
        from config.settings import get_config
        config = get_config()
        
        print("✅ Configuration loaded successfully")
        print(f"  - Environment: {config.environment}")
        print(f"  - Radar UART: {config.radar.uart_port}")
        print(f"  - Radar Baud: {config.radar.baud_rate}")
        print(f"  - Redis Host: {config.redis.host}")
        print(f"  - Redis Port: {config.redis.port}")
        print(f"  - Speed Units: {config.radar.speed_units}")
        return True
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_radar_service_import():
    """Test that radar service can be imported with new config"""
    print("\nTesting radar service import...")
    try:
        # This will fail if there are syntax errors or import issues
        import radar_service
        print("✅ Radar service module imported successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import radar_service: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_radar_service_initialization():
    """Test that radar service can be initialized with config"""
    print("\nTesting radar service initialization...")
    try:
        from config.settings import get_config
        import radar_service
        
        config = get_config()
        service = radar_service.RadarServiceEnhanced(config=config)
        
        print("✅ Radar service initialized successfully")
        print(f"  - UART Port: {service.uart_port}")
        print(f"  - Baud Rate: {service.baudrate}")
        print(f"  - Redis Host: {service.redis_host}")
        print(f"  - Redis Port: {service.redis_port}")
        
        # Verify values match config
        assert service.uart_port == config.radar.uart_port, "UART port mismatch"
        assert service.baudrate == config.radar.baud_rate, "Baud rate mismatch"
        assert service.redis_host == config.redis.host, "Redis host mismatch"
        assert service.redis_port == config.redis.port, "Redis port mismatch"
        
        print("✅ Service configuration values match centralized config")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize radar service: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_validation():
    """Test configuration validation"""
    print("\nTesting configuration validation...")
    try:
        from config.settings import get_config
        config = get_config()
        
        errors = config.validate()
        if errors:
            print(f"⚠️  Configuration has {len(errors)} validation warnings:")
            for error in errors:
                print(f"  - {error}")
        else:
            print("✅ Configuration validation passed (no errors)")
        
        return True
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("=" * 70)
    print("Radar Service Configuration Migration Test Suite")
    print("=" * 70)
    
    tests = [
        ("Config Import", test_config_import),
        ("Config Loading", test_config_loading),
        ("Radar Service Import", test_radar_service_import),
        ("Radar Service Initialization", test_radar_service_initialization),
        ("Config Validation", test_config_validation),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' raised exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Radar service migration successful.")
        return 0
    else:
        print("⚠️  Some tests failed. Please review errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
