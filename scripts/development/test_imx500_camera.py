#!/usr/bin/env python3
"""
Test IMX500 camera access within Docker container.
Modified for containerized Raspberry Pi environment.
"""
import os
import sys

# Check if required packages are available
try:
    from picamera2 import Picamera2
    from picamera2.devices.imx500 import IMX500
    import cv2
except ImportError as e:
    print(f"❌ Missing required packages: {e}")
    print("Install with: pip install picamera2 opencv-python")
    sys.exit(1)

def is_running_in_docker():
    """Check if running inside a Docker container"""
    try:
        with open('/proc/1/cgroup', 'rt') as f:
            return 'docker' in f.read()
    except (FileNotFoundError, IOError) as e:
        return False

def check_docker_requirements():
    """Check if Docker container has necessary camera access"""
    print("=== Docker Environment Check ===")

    # Check if running in Docker
    in_docker = is_running_in_docker()
    print(f"Running in Docker: {in_docker}")

    # Check camera devices
    camera_devices = ['/dev/video0', '/dev/video1', '/dev/media0', '/dev/media1']
    available_devices = []
    for device in camera_devices:
        if os.path.exists(device):
            available_devices.append(device)
    print(f"Available camera devices: {available_devices}")

    # Check IMX500 model path
    model_paths = [
        '/usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk',
        '/app/models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk'
    ]

    available_models = []
    for model_path in model_paths:
        if os.path.exists(model_path):
            available_models.append(model_path)
    print(f"Available AI models: {available_models}")

    return in_docker, available_devices, available_models

def test_camera_in_docker():
    """Test camera functionality within Docker container"""
    print("\n=== IMX500 Camera Test (Docker) ===")

    # Check Docker environment
    in_docker, camera_devices, model_paths = check_docker_requirements()

    if not camera_devices:
        print("❌ No camera devices found!")
        print("Make sure to run Docker with device mounting:")
        print("docker run --device=/dev/video0 --device=/dev/media0 --device=/dev/media1 ...")
        return False

    # Set paths based on environment
    if in_docker:
        output_path = "/app/test_imx500_image.jpg"
        model_path = model_paths[0] if model_paths else None
    else:
        output_path = "/mnt/external_ssd/test_imx500_image.jpg"
        model_path = "/usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk"

    print(f"Output path: {output_path}")
    print(f"Model path: {model_path}")

    try:
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        print("Initializing camera...")
        # Initialize Picamera2
        picam2 = Picamera2()
        camera_config = picam2.create_still_configuration(main={"size": (1920, 1080)})
        picam2.configure(camera_config)
        picam2.start()
        print("✅ Camera initialized successfully")

        # Initialize IMX500 if model is available
        imx500 = None
        if model_path and os.path.exists(model_path):
            try:
                imx500 = IMX500(model_path)
                print("✅ IMX500 AI model loaded successfully")
            except Exception as e:
                print(f"⚠️  Could not load IMX500 model: {e}")
                print("Continuing with basic camera test only...")

        # Capture image
        print("Capturing image...")
        frame = picam2.capture_array()

        # Save image
        success = cv2.imwrite(output_path, frame)
        if success:
            print(f"✅ Image saved to {output_path}")
            file_size = os.path.getsize(output_path)
            print(f"   File size: {file_size} bytes")
        else:
            print(f"❌ Failed to save image to {output_path}")

        # Test AI detection if available
        if imx500:
            print("Testing AI detection...")
            try:
                request = picam2.capture_request()
                outputs = imx500.get_outputs(request.get_metadata())
                print("✅ AI Detection test completed")
                print(f"   Detection outputs: {outputs}")
                request.release()
            except Exception as e:
                print(f"⚠️  AI detection test failed: {e}")

        picam2.stop()
        print("✅ Camera test completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Error during camera test: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure Docker container has camera device access:")
        print("   docker run --device=/dev/video0 --device=/dev/media0 --device=/dev/media1 ...")
        print("2. Check camera permissions:")
        print("   sudo chmod 666 /dev/video0 /dev/media0 /dev/media1")
        print("3. Verify IMX500 firmware is installed on host")
        return False

def main():
    """Main test function"""
    print("Raspberry Pi IMX500 Camera Test (Docker Compatible)")
    print("=" * 50)

    success = test_camera_in_docker()

    if success:
        print("\n🎉 Camera test PASSED!")
        print("Your IMX500 camera is working correctly in Docker.")
    else:
        print("\n❌ Camera test FAILED!")
        print("Check the error messages above for troubleshooting.")

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
