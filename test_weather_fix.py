#!/usr/bin/env python3
"""
Test script to verify the weather analysis tuple fix
"""

import sys
import os
import numpy as np

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'edge_processing'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'edge_api'))

def test_weather_fix():
    """Test that weather analysis works with proper frame data"""
    
    print("Testing weather analysis tuple fix...")
    
    try:
        # Import the modules
        from weather_analysis.sky_analysis_service import SkyAnalysisService
        from pi_system_status import PiSystemStatus
        from vehicle_detection.vehicle_detection_service import VehicleDetectionService
        
        print("✓ Successfully imported modules")
        
        # Create a test image (simulate camera frame)
        test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        print(f"✓ Created test frame with shape: {test_frame.shape}")
        
        # Test SkyAnalysisService directly
        sky_analyzer = SkyAnalysisService(enable_redis=False)
        sky_result = sky_analyzer.analyze_sky_condition(test_frame)
        
        if 'error' in sky_result:
            print(f"✗ SkyAnalysisService failed: {sky_result['error']}")
            return False
        else:
            print(f"✓ SkyAnalysisService works: condition={sky_result['condition']}, confidence={sky_result['confidence']:.2f}")
        
        # Test PiSystemStatus with weather metrics
        system_status = PiSystemStatus()
        weather_metrics = system_status.get_weather_metrics(test_frame)
        
        if 'error' in weather_metrics.get('sky_condition', {}):
            print(f"✗ PiSystemStatus failed: {weather_metrics['sky_condition']['error']}")
            return False
        else:
            condition = weather_metrics['sky_condition']['condition']
            print(f"✓ PiSystemStatus works: condition={condition}")
        
        # Test VehicleDetectionService get_current_frame
        print("\nTesting VehicleDetectionService.get_current_frame()...")
        
        # Create a mock vehicle detection service to test the method
        vehicle_service = VehicleDetectionService()
        
        # Test the get_current_frame method (this should now return frame, not tuple)
        try:
            current_frame = vehicle_service.get_current_frame()
            
            if current_frame is not None:
                if isinstance(current_frame, tuple):
                    print(f"✗ get_current_frame still returns tuple: {type(current_frame)}")
                    return False
                elif hasattr(current_frame, 'shape'):
                    print(f"✓ get_current_frame returns proper frame: shape={current_frame.shape}")
                else:
                    print(f"✗ get_current_frame returns unexpected type: {type(current_frame)}")
                    return False
            else:
                print("⚠ get_current_frame returns None (camera not available, but this is expected)")
        
        except Exception as e:
            print(f"✗ get_current_frame threw exception: {e}")
            return False
        
        print("\n✅ All tests passed! Weather analysis tuple fix is working.")
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        print("Some modules may not be available in this environment")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_weather_fix()
    exit(0 if success else 1)