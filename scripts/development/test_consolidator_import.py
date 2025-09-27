#!/usr/bin/env python3
"""Test script to debug the consolidator import issue"""

import logging
import sys
import traceback

logging.basicConfig(level=logging.DEBUG)

print("=== Testing Consolidator Import Issue ===")
print(f"Python path: {sys.path}")
print()

# Test 1: Basic import
print("Test 1: Basic redis import...")
try:
    import redis
    print("✅ redis imported successfully")
except Exception as e:
    print(f"❌ redis import failed: {e}")
    traceback.print_exc()

print()

# Test 2: First import attempt (direct from redis_models)
print("Test 2: Direct import from redis_models...")
try:
    from redis_models import RedisDataManager, RedisKeys
    print("✅ Direct import from redis_models successful")
except Exception as e:
    print(f"❌ Direct import failed: {e}")
    traceback.print_exc()

print()

# Test 3: Second import attempt (from edge_processing.redis_models)
print("Test 3: Import from edge_processing.redis_models...")
try:
    from edge_processing.redis_models import RedisDataManager, RedisKeys
    print("✅ edge_processing.redis_models import successful")
except Exception as e:
    print(f"❌ edge_processing.redis_models import failed: {e}")
    traceback.print_exc()

print()

# Test 4: Try to use RedisDataManager
print("Test 4: Try to instantiate RedisDataManager...")
try:
    # This should exist if either import worked
    manager = RedisDataManager("redis", 6379)
    print("✅ RedisDataManager created successfully")
except NameError as e:
    print(f"❌ RedisDataManager not defined: {e}")
except Exception as e:
    print(f"❌ RedisDataManager creation failed: {e}")
    traceback.print_exc()

print()
print("=== Import Test Complete ===")