#!/usr/bin/env python3
"""
Test script for host-capture weather analysis
"""

import json
import sys
import os

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'edge_processing'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'edge_api'))

def test_host_capture_weather():
    """Test weather analysis using host-capture architecture"""
    
    print("Testing host-capture weather analysis...")
    
    try:
        # Test the sky analyzer's analyze_current_sky method directly
        from weather_analysis.sky_analyzer import SkyAnalyzer
        
        print("✓ Successfully imported SkyAnalyzer")
        
        # Create sky analyzer (should use shared volume if available)
        sky_analyzer = SkyAnalyzer(use_shared_volume=True)
        print("✓ Created SkyAnalyzer with shared volume enabled")
        
        # Check provider status
        status = sky_analyzer.get_provider_status()
        print(f"📊 Provider status: {status}")
        
        # Test analyze_current_sky method
        print("\n🔍 Testing analyze_current_sky method...")
        
        result = sky_analyzer.analyze_current_sky(max_age_seconds=30.0)
        
        if 'error' in result:
            print(f"⚠️  Sky analysis returned error: {result['error']}")
            print("This is expected if no recent images are available in shared volume")
            print(f"📝 Full result: {json.dumps(result, indent=2)}")
        else:
            print(f"✅ Sky analysis successful!")
            print(f"🌤️  Condition: {result.get('condition', 'unknown')}")
            print(f"🎯 Confidence: {result.get('confidence', 0):.2f}")
            print(f"📷 Image source: {result.get('image_source', 'unknown')}")
            print(f"⏰ Image age: {result.get('image_age_seconds', 'unknown')} seconds")
        
        # Test API-style usage
        print("\n🌐 Testing API-style weather analysis...")
        
        from pi_system_status import PiSystemStatus
        system_status = PiSystemStatus()
        
        # Test weather metrics without camera image (as the API will do)
        weather_metrics = system_status.get_weather_metrics(camera_image=None)
        print(f"📊 Weather metrics: {weather_metrics.get('sky_condition', {}).get('condition', 'unavailable')}")
        
        print("\n✅ Host-capture weather analysis test completed!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Some modules may not be available in this environment")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_shared_volume_path():
    """Test if shared volume path exists and has images"""
    
    print("\n📁 Testing shared volume paths...")
    
    shared_volume_paths = [
        "/mnt/storage/camera_capture",
        "/tmp/camera_capture"
    ]
    
    for path in shared_volume_paths:
        if os.path.exists(path):
            print(f"✅ Found shared volume path: {path}")
            
            # Check for subdirectories
            subdirs = ['live', 'metadata', 'processed']
            for subdir in subdirs:
                subpath = os.path.join(path, subdir)
                if os.path.exists(subpath):
                    files = os.listdir(subpath)
                    print(f"   📂 {subdir}: {len(files)} files")
                    if files:
                        print(f"      📄 Latest: {sorted(files)[-1] if files else 'none'}")
                else:
                    print(f"   📂 {subdir}: not found")
        else:
            print(f"❌ Shared volume path not found: {path}")

if __name__ == "__main__":
    print("🧪 Testing Host-Capture Weather Analysis")
    print("=" * 50)
    
    # Test shared volume paths
    test_shared_volume_path()
    
    # Test weather analysis
    success = test_host_capture_weather()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ All tests completed successfully!")
    else:
        print("❌ Some tests failed - check output above")
    
    exit(0 if success else 1)