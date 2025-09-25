#!/bin/bash
# Docker script to run IMX500 camera test with proper device mounting
# Run this script on your Raspberry Pi to test the camera within Docker

set -e

echo "=== Docker IMX500 Camera Test ==="
echo "This script will run the camera test within a Docker container"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo "⚠️  Warning: Not running on Raspberry Pi. Camera test may not work."
fi

# Use your actual Docker image instead of building locally
IMAGE_NAME="gcumerk/cst590-capstone-public:latest"

# Pull the latest image if not present
if ! docker images | grep -q "gcumerk/cst590-capstone-public"; then
    echo "Pulling Docker image..."
    docker pull "$IMAGE_NAME"
fi

# Check for camera devices
echo "Checking camera devices..."
CAMERA_DEVICES=""
if [ -e "/dev/video0" ]; then
    CAMERA_DEVICES="$CAMERA_DEVICES --device=/dev/video0"
fi
if [ -e "/dev/video1" ]; then
    CAMERA_DEVICES="$CAMERA_DEVICES --device=/dev/video1"
fi
if [ -e "/dev/media0" ]; then
    CAMERA_DEVICES="$CAMERA_DEVICES --device=/dev/media0"
fi
if [ -e "/dev/media1" ]; then
    CAMERA_DEVICES="$CAMERA_DEVICES --device=/dev/media1"
fi

# Add GPIO and other devices
OTHER_DEVICES=""
if [ -e "/dev/gpiomem" ]; then
    OTHER_DEVICES="$OTHER_DEVICES --device=/dev/gpiomem"
fi
if [ -e "/dev/ttyACM0" ]; then
    OTHER_DEVICES="$OTHER_DEVICES --device=/dev/ttyACM0"
fi

if [ -z "$CAMERA_DEVICES" ]; then
    echo "❌ No camera devices found!"
    echo "Make sure your IMX500 camera is connected and detected."
    exit 1
fi

echo "Found camera devices: $CAMERA_DEVICES"

# Set proper permissions for camera devices
echo "Setting camera device permissions..."
sudo chmod 666 /dev/video* /dev/media* 2>/dev/null || true

# Create output directory
mkdir -p /tmp/camera-test-output
sudo mkdir -p /mnt/storage/periodic_snapshots /mnt/storage/ai_camera_images
sudo chmod 777 /mnt/storage/periodic_snapshots /mnt/storage/ai_camera_images 2>/dev/null || true

# Run the camera test in Docker
echo "Running camera test in Docker..."
docker run --rm \
    --name cst590-camera-test \
    --privileged \
    $CAMERA_DEVICES \
    $OTHER_DEVICES \
    --device=/dev/vchiq \
    --device=/dev/vcsm \
    -v /tmp/camera-test-output:/app/output \
    -v /mnt/storage/periodic_snapshots:/mnt/storage/periodic_snapshots \
    -v /mnt/storage/ai_camera_images:/mnt/storage/ai_camera_images \
    -v /usr/share/imx500-models:/usr/share/imx500-models:ro \
    -e PYTHONPATH=/app \
    -e PYTHONUNBUFFERED=1 \
    -e DISPLAY=:0 \
    -e LIBCAMERA_LOG_LEVELS=ERROR \
    -e IMX500_MODEL_PATH=/usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk \
    -e PERIODIC_SNAPSHOT_PATH=/mnt/storage/periodic_snapshots \
    -e SNAPSHOT_INTERVAL_MINUTES=5 \
    -e DETECTION_SAVE_PATH=/mnt/storage/ai_camera_images \
    "$IMAGE_NAME" \
    python3 -c "
import cv2
import sys
import os

print('=== CST590 Camera Test with Actual Docker Image ===')
print('Testing camera access...')

# Test camera access
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print('❌ Camera not accessible')
    sys.exit(1)

print('✅ Camera opened successfully')
ret, frame = cap.read()
if ret:
    os.makedirs('/app/output', exist_ok=True)
    cv2.imwrite('/app/output/cst590_test_image.jpg', frame)
    print(f'✅ Image captured! Size: {frame.shape}')
    print('📁 Saved to: /app/output/cst590_test_image.jpg')
else:
    print('❌ Failed to capture frame')
    sys.exit(1)

cap.release()
print('🎉 CST590 camera test completed successfully!')
"

# Check if image was created
if [ -f "/tmp/camera-test-output/cst590_test_image.jpg" ]; then
    echo "✅ Camera test successful!"
    echo "Image saved to: /tmp/camera-test-output/cst590_test_image.jpg"
    ls -la /tmp/camera-test-output/cst590_test_image.jpg
else
    echo "❌ Camera test failed - no image was captured"
    echo "Check Docker logs above for error details"
fi

echo ""
echo "=== Test Complete ==="
