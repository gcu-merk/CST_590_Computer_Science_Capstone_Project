#!/bin/bash
# Raspberry Pi 5 AI Camera Setup and Test Script
# Run this script on your Raspberry Pi via SSH

echo "=== Raspberry Pi 5 AI Camera Setup ==="
echo "Current date: $(date)"
echo "Raspberry Pi model: $(cat /proc/device-tree/model)"
echo ""

# Step 1: Update system
echo "Step 1: Updating system packages..."
sudo apt update && sudo apt full-upgrade -y

# Step 2: Install IMX500 firmware and tools
echo "Step 2: Installing IMX500 firmware and models..."
sudo apt install -y imx500-all

# Step 3: Install additional dependencies for examples
echo "Step 3: Installing Python dependencies..."
sudo apt install -y python3-opencv python3-munkres

# Step 4: Check if camera is detected
echo "Step 4: Checking camera detection..."
echo "Available cameras:"
rpicam-hello --list-cameras

# Step 5: Test basic camera functionality
echo "Step 5: Testing basic camera (5 second preview)..."
echo "This should show camera working without AI..."
rpicam-hello -t 5s

echo ""
echo "=== AI Camera Tests ==="

# Step 6: Test AI object detection
echo "Step 6: Testing AI object detection (10 seconds)..."
echo "This will load the MobileNet SSD model for object detection"
echo "Note: First run may take several minutes to load firmware!"
rpicam-hello -t 10s --post-process-file /usr/share/rpi-camera-assets/imx500_mobilenet_ssd.json --viewfinder-width 1920 --viewfinder-height 1080 --framerate 30

# Step 7: Test pose estimation
echo "Step 7: Testing pose estimation (10 seconds)..."
rpicam-hello -t 10s --post-process-file /usr/share/rpi-camera-assets/imx500_posenet.json --viewfinder-width 1920 --viewfinder-height 1080 --framerate 30

echo ""
echo "=== Setup Complete ==="
echo "If all tests passed, your AI camera is working correctly!"
echo ""
echo "Next steps:"
echo "1. Try recording video with AI: rpicam-vid -t 10s -o test_ai_video.264 --post-process-file /usr/share/rpi-camera-assets/imx500_mobilenet_ssd.json"
echo "2. Explore Python examples at: https://github.com/raspberrypi/picamera2/tree/main/examples/imx500"
echo "3. Check available models in: /usr/share/imx500-models/"
