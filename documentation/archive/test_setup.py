#!/usr/bin/env python3
"""
Test script to verify the setup is working
"""

import cv2
import numpy as np
import tensorflow as tf
import sys
import time
import serial

def test_camera():
    """Test camera access"""
    print("Testing AI Camera access...")
    
    # First try AI Camera
    try:
        from picamera2 import Picamera2
        
        picam2 = Picamera2()
        config = picam2.create_preview_configuration(
            main={"size": (640, 480), "format": "RGB888"}
        )
        picam2.configure(config)
        picam2.start()
        
        # Capture a test frame
        frame = picam2.capture_array()
        picam2.stop()
        picam2.close()
        
        print(f"✅ AI Camera working - Frame size: {frame.shape}")
        print(f"   Format: RGB888, Resolution: 640x480")
        return True
        
    except ImportError:
        print("⚠️  AI Camera libraries not found, trying USB camera...")
        
        # Fallback to USB camera test
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ No camera accessible")
            return False
        
        ret, frame = cap.read()
        if not ret:
            print("❌ Cannot read from camera")
            cap.release()
            return False
        
        print(f"✅ USB Camera working - Frame size: {frame.shape}")
        cap.release()
        return True
        
    except Exception as e:
        print(f"❌ Camera error: {e}")
        return False

def test_tensorflow():
    """Test TensorFlow installation"""
    print("Testing TensorFlow...")
    
    try:
        # Simple TensorFlow operation
        a = tf.constant([1, 2, 3])
        b = tf.constant([4, 5, 6])
        c = tf.add(a, b)
        
        print(f"✅ TensorFlow working - Version: {tf.__version__}")
        print(f"   Test operation result: {c.numpy()}")
        
        # Check if GPU is available (not expected on Pi, but good to know)
        gpus = tf.config.list_physical_devices('GPU')
        if gpus:
            print(f"   GPU devices found: {len(gpus)}")
        else:
            print("   Running on CPU (expected for Pi)")
        
        return True
    except Exception as e:
        print(f"❌ TensorFlow error: {e}")
        return False

def test_opencv():
    """Test OpenCV installation"""
    print("Testing OpenCV...")
    
    try:
        # Create a simple test image
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        cv2.rectangle(img, (10, 10), (90, 90), (0, 255, 0), 2)
        
        # Test some basic operations
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        
        print(f"✅ OpenCV working - Version: {cv2.__version__}")
        print(f"   Test image created: {img.shape}")
        print(f"   Edge detection completed: {edges.shape}")
        
        return True
    except Exception as e:
        print(f"❌ OpenCV error: {e}")
        return False

def test_tensorflow_hub():
    """Test TensorFlow Hub (optional but recommended)"""
    print("Testing TensorFlow Hub...")
    
    try:
        import tensorflow_hub as hub
        print("✅ TensorFlow Hub available")
        return True
    except ImportError:
        print("⚠️  TensorFlow Hub not installed (optional)")
        print("   Install with: pip install tensorflow-hub")
        return False

def test_ops243c_radar():
    """Test OPS243-C radar sensor"""
    print("Testing OPS243-C radar sensor...")
    
    # Common serial ports for the radar
    possible_ports = ['/dev/ttyACM0', '/dev/ttyACM1', '/dev/ttyUSB0', '/dev/ttyUSB1']
    
    for port in possible_ports:
        try:
            # Try to connect
            ser = serial.Serial(
                port=port,
                baudrate=9600,
                timeout=2.0,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            
            time.sleep(1)  # Let connection stabilize
            
            # Query sensor info
            ser.write(b'??\r')
            ser.flush()
            time.sleep(0.5)
            
            # Read response
            response = ser.read_all().decode('utf-8', errors='ignore')
            
            if 'OPS243' in response or len(response) > 5:
                print(f"✅ OPS243-C radar found on {port}")
                print(f"   Response: {response.strip()}")
                
                # Test speed output mode
                ser.write(b'OS\r')  # Output speed
                ser.flush()
                time.sleep(0.5)
                
                ser.write(b'UM\r')  # Units m/s
                ser.flush()
                time.sleep(0.5)
                
                print("   Radar configured for speed detection")
                ser.close()
                return True
            
            ser.close()
            
        except Exception as e:
            continue  # Try next port
    
    print("❌ OPS243-C radar not found")
    print("   Check connections and power")
    print("   Sensor should be connected via USB or UART")
    return False
    """Test basic vehicle detection pipeline"""
    print("Testing basic detection pipeline...")
    
    try:
        # Create a simple background subtractor test
        bg_subtractor = cv2.createBackgroundSubtractorMOG2()
        
        # Create test frames
        frame1 = np.zeros((480, 640, 3), dtype=np.uint8)
        frame2 = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Add a "vehicle" (rectangle) to second frame
        cv2.rectangle(frame2, (200, 200), (400, 350), (255, 255, 255), -1)
        
        # Test background subtraction
        mask1 = bg_subtractor.apply(frame1)
        mask2 = bg_subtractor.apply(frame2)
        
        # Find contours
        contours, _ = cv2.findContours(mask2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        print(f"✅ Basic detection test passed")
        print(f"   Found {len(contours)} contours")
        
        return True
    except Exception as e:
        print(f"❌ Detection test failed: {e}")
        return False

def main():
    print("🚗 Raspberry Pi 5 Traffic Monitor Setup Test")
    print("=" * 50)
    
    tests = [
        ("Camera", test_camera),
        ("TensorFlow", test_tensorflow),
        ("OpenCV", test_opencv),
        ("TensorFlow Hub", test_tensorflow_hub),
        ("Serial Ports", test_serial_ports),
        ("OPS243-C Radar", test_ops243c_radar),
        ("Detection Pipeline", run_basic_detection_test)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 20)
        results[test_name] = test_func()
    
    print("\n" + "=" * 50)
    print("SUMMARY:")
    print("=" * 50)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:20} {status}")
    
    all_critical_passed = all([
        results.get("Camera", False),
        results.get("TensorFlow", False),
        results.get("OpenCV", False),
        results.get("Detection Pipeline", False)
    ])
    
    radar_working = results.get("OPS243-C Radar", False)
    
    if all_critical_passed:
        print("\n🎉 All critical tests passed! You're ready to run the traffic monitor.")
        print("\nNext steps:")
        if radar_working:
            print("1. Run: python3 vehicle_detection.py")
            print("   (Camera + Radar integration)")
        else:
            print("1. Run: python3 vehicle_detection.py --no-radar")
            print("   (Camera only - connect radar later)")
        print("2. Set up the API server")
        print("3. Configure cloud integration")
    else:
        print("\n⚠️  Some tests failed. Please check the installation.")

if __name__ == "__main__":
    main()