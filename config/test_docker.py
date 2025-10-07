#!/usr/bin/env python3
"""
Docker Configuration Test

Quick test to verify the configuration system works in Docker containers.
Run this inside a container to validate configuration loading.

Usage:
    docker exec traffic-monitor python config/test_docker.py
"""

import sys
import os


def test_import():
    """Test that config module can be imported"""
    try:
        from config import get_config
        print("✅ Config module imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import config: {e}")
        print(f"   PYTHONPATH: {os.environ.get('PYTHONPATH', 'NOT SET')}")
        print(f"   Current dir: {os.getcwd()}")
        print(f"   sys.path: {sys.path}")
        return False


def test_load_config():
    """Test that configuration loads from environment"""
    try:
        from config import get_config
        config = get_config()
        print(f"✅ Configuration loaded successfully")
        print(f"   Environment: {config.environment}")
        print(f"   Redis: {config.redis.host}:{config.redis.port}")
        print(f"   Database: {config.database.path}")
        print(f"   API: {config.api.host}:{config.api.port}")
        print(f"   Log Level: {config.logging.level}")
        return True
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        return False


def test_environment_vars():
    """Test that Docker environment variables are accessible"""
    print("\n📋 Environment Variables:")
    
    env_vars = [
        'REDIS_HOST', 'REDIS_PORT', 'REDIS_DB',
        'DATABASE_PATH', 'API_HOST', 'API_PORT',
        'LOG_LEVEL', 'ENVIRONMENT', 'STORAGE_ROOT'
    ]
    
    for var in env_vars:
        value = os.environ.get(var, 'NOT SET')
        print(f"   {var}: {value}")
    
    return True


def test_validation():
    """Test that config validation works"""
    try:
        from config import get_config
        config = get_config()
        errors = config.validate()
        
        if errors:
            print(f"⚠️  Configuration warnings:")
            for error in errors:
                print(f"   - {error}")
        else:
            print("✅ Configuration validation passed")
        
        return True
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return False


def main():
    print("=" * 60)
    print("Docker Configuration System Test")
    print("=" * 60)
    print()
    
    tests = [
        ("Import Test", test_import),
        ("Load Config", test_load_config),
        ("Environment Variables", test_environment_vars),
        ("Validation", test_validation),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n🔍 {name}")
        print("-" * 60)
        result = test_func()
        results.append((name, result))
        print()
    
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Configuration system is Docker-ready.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
