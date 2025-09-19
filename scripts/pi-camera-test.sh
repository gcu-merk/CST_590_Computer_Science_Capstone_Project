#!/bin/bash
# Simple camera test script for Raspberry Pi with Docker
# Run this directly on your Pi

set -e

echo "=== Raspberry Pi Camera Test with Docker ==="
echo "Testing camera access from Docker container..."
echo ""

# Check if user is in docker group
if ! groups | grep -q docker; then
    echo "⚠️  You may need to add your user to docker group:"
    echo "   sudo usermod -aG docker $USER"
    echo "   Then logout and login again"
    echo ""
fi

# Create output directory
mkdir -p /tmp/camera-test
cd /tmp/camera-test

# Test 1: List camera devices
echo "🔍 Test 1: Checking primary camera device in Docker..."
sudo docker run --rm --privileged \
    --device=/dev/video0 \
    --device=/dev/media0 \
    python:3.9-slim bash -c "
        apt-get update -qq && apt-get install -y -qq v4l-utils > /dev/null 2>&1
        echo 'Primary camera device info:'
        v4l2-ctl --device=/dev/video0 --info
        echo ''
        echo 'Available formats:'
        v4l2-ctl --device=/dev/video0 --list-formats
    "

echo ""
echo "✅ Camera devices accessible from Docker"
echo ""

# Test 2: Simple image capture
echo "📸 Test 2: Capturing test image from primary camera..."
sudo docker run --rm --privileged \
    --device=/dev/video0 \
    --device=/dev/media0 \
    -v /tmp/camera-test:/output \
    python:3.9-slim bash -c "
        apt-get update -qq && apt-get install -y -qq python3-pip v4l-utils > /dev/null 2>&1
        pip install opencv-python-headless > /dev/null 2>&1
        python3 -c \"
import cv2
import sys

print('Attempting to capture image...')
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print('❌ Could not open camera')
    sys.exit(1)

ret, frame = cap.read()
if ret:
    cv2.imwrite('/output/test_capture.jpg', frame)
    print('✅ Image captured successfully!')
    print('Image saved to: /tmp/camera-test/test_capture.jpg')
else:
    print('❌ Failed to capture frame')
    sys.exit(1)

cap.release()
print(f'Image dimensions: {frame.shape}')
\"
    "

# Check results
echo ""
if [ -f "/tmp/camera-test/test_capture.jpg" ]; then
    echo "🎉 SUCCESS! Camera test completed successfully"
    echo "📁 Image saved to: /tmp/camera-test/test_capture.jpg"
    echo "📊 File size: $(du -h /tmp/camera-test/test_capture.jpg | cut -f1)"
    echo ""
    echo "You can view the image with:"
    echo "   feh /tmp/camera-test/test_capture.jpg"
    echo "   or"
    echo "   scp merk@$(hostname -I | awk '{print $1}'):/tmp/camera-test/test_capture.jpg ."
else
    echo "❌ Test failed - no image was captured"
fi

echo ""
echo "=== Test Complete ==="
