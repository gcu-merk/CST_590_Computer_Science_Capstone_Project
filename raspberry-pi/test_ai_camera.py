#!/usr/bin/env python3
"""
Minimal AI Camera Test Script
Simple test to verify Raspberry Pi 5 AI camera is working
"""

import time
from picamera2 import Picamera2
from picamera2.devices.imx500 import IMX500

def test_basic_camera():
    """Test basic camera functionality without AI"""
    print("Testing basic camera functionality...")
    
    picam2 = Picamera2()
    picam2.configure(picam2.create_preview_configuration())
    
    print("Starting camera preview for 5 seconds...")
    picam2.start()
    time.sleep(5)
    picam2.stop()
    print("Basic camera test complete!")

def test_ai_camera():
    """Test AI camera with object detection"""
    print("Testing AI camera with object detection...")
    
    # Initialize IMX500 with MobileNet SSD model
    model_file = "/usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk"
    imx500 = IMX500(model_file)
    
    picam2 = Picamera2()
    config = picam2.create_preview_configuration()
    picam2.configure(config)
    
    print("Starting AI camera for 10 seconds...")
    print("Note: First run may take several minutes to load AI model...")
    
    picam2.start()
    
    # Simple loop to capture frames
    for i in range(100):  # ~10 seconds at 10fps
        request = picam2.capture_request()
        
        # Get AI outputs
        outputs = imx500.get_outputs(request.get_metadata())
        if outputs:
            print(f"Frame {i}: AI inference successful")
        else:
            print(f"Frame {i}: No AI outputs")
            
        request.release()
        time.sleep(0.1)
    
    picam2.stop()
    print("AI camera test complete!")

def check_camera_info():
    """Display camera information"""
    print("=== Camera Information ===")
    
    try:
        picam2 = Picamera2()
        camera_info = picam2.camera_properties
        print(f"Camera model: {camera_info.get('Model', 'Unknown')}")
        print(f"Camera controls: {list(camera_info.keys())}")
        
        # Check available models
        import os
        models_dir = "/usr/share/imx500-models/"
        if os.path.exists(models_dir):
            models = [f for f in os.listdir(models_dir) if f.endswith('.rpk')]
            print(f"Available AI models: {models}")
        else:
            print("No AI models directory found")
            
    except Exception as e:
        print(f"Error getting camera info: {e}")

if __name__ == "__main__":
    print("Raspberry Pi 5 AI Camera Test")
    print("==============================")
    
    # Check camera info
    check_camera_info()
    
    try:
        # Test basic camera first
        test_basic_camera()
        
        # Then test AI functionality
        test_ai_camera()
        
    except Exception as e:
        print(f"Error during camera test: {e}")
        print("Make sure:")
        print("1. Camera is properly connected")
        print("2. IMX500 firmware is installed (sudo apt install imx500-all)")
        print("3. You're running on Raspberry Pi with camera enabled")
