#!/usr/bin/env python3
"""
Test script for camera capture functionality
Run this to verify that the camera capture fix is working
"""

import sys
import os
import time

# Add the edge_processing directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from edge_processing.vehicle_detection.vehicle_detection_service import VehicleDetectionService

def test_camera_capture():
    """Test the camera capture functionality"""
    print("Testing camera capture functionality...")

    # Create service instance with image saving enabled
    service = VehicleDetectionService(
        save_detections=True,
        save_path="/mnt/storage/ai_camera_images",
        save_confidence_threshold=0.5,  # Lower threshold for testing
        max_saved_images=50
    )

    # Initialize camera
    print("Initializing camera...")
    if not service.initialize_camera():
        print("❌ Failed to initialize camera")
        return False

    print("✅ Camera initialized successfully")

    # Test frame capture
    print("Testing frame capture...")
    for i in range(3):
        ret, frame = service.capture_frame()
        if ret and frame is not None:
            print(f"✅ Frame {i+1} captured successfully - Shape: {frame.shape}")
        else:
            print(f"❌ Failed to capture frame {i+1}")
            return False
        time.sleep(0.5)  # Brief pause between captures

    # Cleanup
    service.stop_detection()
    print("✅ Camera test completed successfully")
    return True

if __name__ == "__main__":
    try:
        success = test_camera_capture()
        if success:
            print("\n🎉 Camera capture is working!")
        else:
            print("\n❌ Camera capture test failed")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
