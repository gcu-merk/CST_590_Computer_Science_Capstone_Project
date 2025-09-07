# Camera Testing Scripts

This directory contains scripts for testing the IMX500 AI camera on Raspberry Pi, including Docker-compatible versions.

## Files

- `test_imx500_camera.py` - Main camera test script (Docker-compatible)
- `docker_camera_test.sh` - Docker wrapper script for easy testing

## Usage

### Option 1: Direct Python Script (Host System)

Run directly on Raspberry Pi (requires picamera2, OpenCV, IMX500 packages):

```bash
python3 scripts/test_imx500_camera.py
```

### Option 2: Docker Container (Recommended)

Run the camera test within a Docker container:

```bash
# Make script executable
chmod +x scripts/docker_camera_test.sh

# Run the test
./scripts/docker_camera_test.sh
```

## What the Test Does

1. **Environment Detection**: Checks if running in Docker vs host system
2. **Device Check**: Verifies camera devices are accessible
3. **Model Check**: Confirms IMX500 AI models are available
4. **Camera Test**: Initializes and tests basic camera functionality
5. **AI Test**: Tests IMX500 object detection capabilities
6. **Image Capture**: Saves a test image to verify camera works

## Docker Requirements

When running in Docker, ensure:

1. **Device Mounting**: Camera devices must be mounted
   ```bash
   --device=/dev/video0 --device=/dev/media0 --device=/dev/media1
   ```

2. **Privileged Mode**: May be needed for camera access
   ```bash
   --privileged
   ```

3. **Model Files**: IMX500 models should be accessible
   ```bash
   -v /usr/share/imx500-models:/usr/share/imx500-models:ro
   ```

## Troubleshooting

### No Camera Devices Found
```bash
# Check device permissions
ls -la /dev/video* /dev/media*

# Set permissions
sudo chmod 666 /dev/video* /dev/media*
```

### Import Errors
```bash
# Install required packages
sudo apt install -y python3-opencv python3-munkres imx500-all
```

### Docker Issues
```bash
# Check Docker can access devices
docker run --rm --device=/dev/video0 busybox ls /dev/video0

# Run with privileged mode
docker run --privileged --device=/dev/video0 [image] [command]
```

## Output

The test will:
- Show environment information
- Display available devices and models
- Capture and save a test image
- Test AI detection capabilities
- Report success/failure status

Test images are saved to:
- Host system: `/mnt/external_ssd/test_imx500_image.jpg`
- Docker: `/app/test_imx500_image.jpg` (mounted to `/tmp/camera-test-output` on host)
