#!/usr/bin/env python3
"""
Test script to debug the exact variable scoping issue in the consolidator import
"""

print("=== Testing Variable Scoping in Import Logic ===")

# Simulate our current code structure
RedisDataManager = None
VehicleDetection = None
VehicleType = None
BoundingBox = None
RedisKeys = None

print(f"Initial RedisDataManager: {RedisDataManager}")

try:
    from redis_models import (
        VehicleDetection, VehicleType, BoundingBox, 
        RedisDataManager, RedisKeys
    )
    print("✅ Imported Redis models from redis_models")
    print(f"RedisDataManager after first import: {RedisDataManager}")
except ImportError as e:
    print(f"❌ First import failed: {e}")
    try:
        from edge_processing.redis_models import (
            VehicleDetection, VehicleType, BoundingBox, 
            RedisDataManager, RedisKeys
        )
        print("✅ Imported Redis models from edge_processing.redis_models")
        print(f"RedisDataManager after second import: {RedisDataManager}")
    except ImportError as e2:
        print(f"❌ Second import failed: {e2}")
        RedisDataManager = None

print(f"Final RedisDataManager: {RedisDataManager}")
print(f"RedisDataManager is None: {RedisDataManager is None}")

# Verify we have the required classes
if RedisDataManager is None:
    print("❌ RedisDataManager not available - consolidator cannot start")
else:
    print("✅ RedisDataManager is available - consolidator can start")
    print(f"RedisDataManager type: {type(RedisDataManager)}")