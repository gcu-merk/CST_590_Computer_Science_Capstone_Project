#!/bin/bash
# Camera Debugging Script for IMX500 in Docker Container
# This script helps diagnose camera issues and verify the fix deployment

echo "🔍 Camera Debugging Report - $(date)"
echo "================================================"

echo
echo "📋 1. Container Information"
echo "----------------------------"
echo "Container ID: $(hostname)"
echo "Image: $(cat /proc/1/environ 2>/dev/null | tr '\0' '\n' | grep DOCKER_IMAGE || echo 'Not found')"

echo
echo "📋 2. Camera Hardware Detection"
echo "--------------------------------"
echo "Video devices:"
ls -la /dev/video* 2>/dev/null || echo "❌ No video devices found"

echo
echo "Available cameras:"
v4l2-ctl --list-devices 2>/dev/null || echo "❌ v4l2-ctl not available or no devices"

echo
echo "📋 3. System-Level Camera Test"
echo "-------------------------------"
echo "Testing fswebcam (our fallback method):"
if command -v fswebcam >/dev/null 2>&1; then
    echo "✅ fswebcam command available"
    
    # Try to capture a test image
    TEST_IMG="/tmp/camera_test_$(date +%s).jpg"
    echo "Attempting capture to: $TEST_IMG"
    
    timeout 15 fswebcam --no-banner --resolution 1920x1080 --device /dev/video0 --jpeg 95 "$TEST_IMG" 2>&1
    RESULT=$?
    
    if [ $RESULT -eq 0 ] && [ -f "$TEST_IMG" ]; then
        SIZE=$(stat -f%z "$TEST_IMG" 2>/dev/null || stat -c%s "$TEST_IMG" 2>/dev/null)
        echo "✅ fswebcam capture successful! Image size: $SIZE bytes"
        rm -f "$TEST_IMG"
    else
        echo "❌ fswebcam capture failed (exit code: $RESULT)"
    fi
else
    echo "❌ fswebcam command not found"
fi

echo
echo "📋 4. Application Status"
echo "------------------------"
echo "Current Python processes:"
ps aux | grep python | grep -v grep || echo "No Python processes found"

echo
echo "Recent camera-related logs:"
docker logs $(hostname) --tail=20 2>/dev/null | grep -i "camera\|frame\|snapshot" | tail -10 || echo "No recent camera logs"

echo
echo "📋 5. Storage Check"
echo "-------------------"
echo "Snapshot directories:"
for DIR in "/mnt/storage/periodic_snapshots" "/tmp/periodic_snapshots" "/app/periodic_snapshots"; do
    if [ -d "$DIR" ]; then
        echo "✅ $DIR exists"
        ls -la "$DIR" | tail -5
    else
        echo "❌ $DIR not found"
    fi
done

echo
echo "📋 6. Environment Check"
echo "-----------------------"
echo "Running in container: $([ -f /.dockerenv ] && echo 'Yes' || echo 'No')"
echo "User: $(whoami)"
echo "Working directory: $(pwd)"

echo
echo "================================================"
echo "🔍 Debug report complete - $(date)"
