#!/usr/bin/env python3
"""
Test script to debug the Redis models import issue in the consolidator
"""

import sys
import os
print(f"Python path: {sys.path}")
print(f"Current working directory: {os.getcwd()}")
print(f"Files in current directory: {os.listdir('.')}")

print("\n=== Testing Redis Models Import ===")

# Test 1: Direct redis_models import (should fail)
print("\n1. Testing: from redis_models import RedisDataManager")
try:
    from redis_models import RedisDataManager
    print("✅ SUCCESS: redis_models import worked")
except ImportError as e:
    print(f"❌ FAILED: {e}")

# Test 2: edge_processing.redis_models import (should work)
print("\n2. Testing: from edge_processing.redis_models import RedisDataManager")
try:
    from edge_processing.redis_models import RedisDataManager
    print("✅ SUCCESS: edge_processing.redis_models import worked")
    print(f"RedisDataManager type: {type(RedisDataManager)}")
except ImportError as e:
    print(f"❌ FAILED: {e}")

# Test 3: Check if edge_processing directory exists
print(f"\n3. Checking edge_processing directory:")
if os.path.exists('edge_processing'):
    print("✅ edge_processing directory exists")
    print(f"Contents: {os.listdir('edge_processing')}")
    
    if os.path.exists('edge_processing/redis_models.py'):
        print("✅ redis_models.py file exists")
    else:
        print("❌ redis_models.py file missing")
else:
    print("❌ edge_processing directory not found")

print("\n=== Test Complete ===")