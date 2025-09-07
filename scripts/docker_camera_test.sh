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

# Build the Docker image if it doesn't exist
IMAGE_NAME="cst590-camera-test"
if ! docker images | grep -q "$IMAGE_NAME"; then
    echo "Building Docker image..."
    docker build -t "$IMAGE_NAME" .
fi

# Check for camera devices
echo "Checking camera devices..."
CAMERA_DEVICES=""
if [ -e "/dev/video0" ]; then
    CAMERA_DEVICES="$CAMERA_DEVICES --device=/dev/video0"
fi
if [ -e "/dev/media0" ]; then
    CAMERA_DEVICES="$CAMERA_DEVICES --device=/dev/media0"
fi
if [ -e "/dev/media1" ]; then
    CAMERA_DEVICES="$CAMERA_DEVICES --device=/dev/media1"
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

# Run the camera test in Docker
echo "Running camera test in Docker..."
docker run --rm \
    --name cst590-camera-test \
    --privileged \
    $CAMERA_DEVICES \
    --device=/dev/vchiq \
    --device=/dev/vcsm \
    -v /tmp/camera-test-output:/app/output \
    -v /usr/share/imx500-models:/usr/share/imx500-models:ro \
    -e PYTHONPATH=/app \
    "$IMAGE_NAME" \
    python3 scripts/test_imx500_camera.py

# Check if image was created
if [ -f "/tmp/camera-test-output/test_imx500_image.jpg" ]; then
    echo "✅ Camera test successful!"
    echo "Image saved to: /tmp/camera-test-output/test_imx500_image.jpg"
    ls -la /tmp/camera-test-output/test_imx500_image.jpg
else
    echo "❌ Camera test failed - no image was captured"
    echo "Check Docker logs above for error details"
fi

echo ""
echo "=== Test Complete ==="
