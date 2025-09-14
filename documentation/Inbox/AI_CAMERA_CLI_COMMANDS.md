# Raspberry Pi 5 AI Camera - CLI Commands Reference

## Quick Setup Commands (run on Raspberry Pi via SSH)

### 1. Update System
```bash
sudo apt update && sudo apt full-upgrade -y
```

### 2. Install AI Camera Firmware and Tools
```bash
sudo apt install imx500-all
```

### 3. Install Python Dependencies (optional, for Python examples)
```bash
sudo apt install python3-opencv python3-munkres
```

### 4. Reboot (required after firmware install)
```bash
sudo reboot
```

## Basic Camera Tests

### Check Camera Detection
```bash
rpicam-hello --list-cameras
```

### Test Basic Camera (5 second preview)
```bash
rpicam-hello -t 5s
```

### Test Camera with Info
```bash
rpicam-hello -t 5s --info-text fps
```

## AI Camera Tests

### Object Detection (MobileNet SSD)
```bash
# 10 second preview with object detection overlay
rpicam-hello -t 10s --post-process-file /usr/share/rpi-camera-assets/imx500_mobilenet_ssd.json --viewfinder-width 1920 --viewfinder-height 1080 --framerate 30
```

### Pose Estimation
```bash
# 10 second preview with pose estimation
rpicam-hello -t 10s --post-process-file /usr/share/rpi-camera-assets/imx500_posenet.json --viewfinder-width 1920 --viewfinder-height 1080 --framerate 30
```

### Record Video with AI
```bash
# Create directory on SSD for AI videos
mkdir -p /mnt/storage/ai_camera_videos

# Record 30 seconds of video with object detection to SSD
rpicam-vid -t 30s -o /mnt/storage/ai_camera_videos/ai_test_video.264 --post-process-file /usr/share/rpi-camera-assets/imx500_mobilenet_ssd.json --width 1920 --height 1080 --framerate 30

# For quick tests (save to home directory)
rpicam-vid -t 10s -o ~/ai_test_video.264 --post-process-file /usr/share/rpi-camera-assets/imx500_mobilenet_ssd.json --width 1920 --height 1080 --framerate 30
```

## Storage Management

### Check Available Storage
```bash
df -h
```

### SSD Storage Location
```bash
# Your SSD is mounted at: /mnt/storage
# Create directories for organized storage
mkdir -p /mnt/storage/ai_camera_videos
mkdir -p /mnt/storage/ai_camera_images
mkdir -p /mnt/storage/ai_models
```

### Check Storage Usage
```bash
# Check SSD usage
du -sh /mnt/storage/*

# Monitor disk usage in real-time
watch df -h
```

## Useful Directories and Files

### AI Models Location
```bash
ls /usr/share/imx500-models/
```

### Post-processing Configurations
```bash
ls /usr/share/rpi-camera-assets/
```

### Check Firmware Files
```bash
ls /lib/firmware/imx500*
```

## Troubleshooting Commands

### Check Camera Hardware
```bash
vcgencmd get_camera
```

### Check Camera in Device Tree
```bash
dtparam camera=on
```

### View Camera Boot Messages
```bash
dmesg | grep -i imx500
```

### Check Camera Service Status
```bash
systemctl status camera
```

## Performance Monitoring

### Show FPS and System Info
```bash
rpicam-hello -t 10s --info-text fps --framerate 30
```

### Monitor System Resources
```bash
htop
# or
iostat 1
```

## Advanced: Python Examples

### Download Picamera2 Examples
```bash
git clone https://github.com/raspberrypi/picamera2.git
cd picamera2/examples/imx500/
```

### Run Object Detection Demo
```bash
python imx500_object_detection_demo.py --model /usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk
```

### Run Pose Estimation Demo
```bash
python imx500_pose_estimation_higherhrnet_demo.py
```

## Quick Start Commands for SSD Storage

### Setup SSD Directories
```bash
# Create organized directories on your SSD
mkdir -p /mnt/storage/ai_videos
mkdir -p /mnt/storage/ai_images
mkdir -p /mnt/storage/ai_models
```

### Quick AI Camera Test with SSD Storage
```bash
# Quick 10-second AI video test saved to SSD
rpicam-vid -t 10s -o /mnt/storage/ai_videos/test_video.264 --post-process-file /usr/share/rpi-camera-assets/imx500_mobilenet_ssd.json --width 1920 --height 1080 --framerate 30

# Capture AI-processed image to SSD
rpicam-still -o /mnt/storage/ai_images/test_image.jpg --post-process-file /usr/share/rpi-camera-assets/imx500_mobilenet_ssd.json
```

## Docker Commands for Traffic Monitoring System

### Check Docker Status
```bash
# Check if Docker is running
sudo systemctl status docker

# Check running containers
docker ps

# Check all containers (including stopped)
docker ps -a
```

### Start Traffic Monitoring Container
```bash
# Navigate to project directory (adjust path as needed)
cd ~/CST_590_Computer_Science_Capstone_Project

# Start with docker-compose
docker-compose up -d

# Or start with logs visible
docker-compose up

# Check container status
docker-compose ps
```

### Docker Troubleshooting
```bash
# Pull latest image
docker pull gcumerk/cst590-capstone-public:latest

# View container logs
docker-compose logs -f traffic-monitor

# Restart containers
docker-compose restart

# Stop containers
docker-compose down
```

### File Transfer Commands

### Copy AI Videos from Pi to Windows
```bash
# From Windows PowerShell - copy single file
scp merk@100.121.231.16:/mnt/storage/ai_videos/test_video.264 C:\Downloads\

# Copy entire ai_videos directory
scp -r merk@100.121.231.16:/mnt/storage/ai_videos/ C:\Downloads\ai_videos\

# Copy specific file pattern
scp merk@100.121.231.16:/mnt/storage/ai_videos/*.264 C:\Downloads\
```

## Notes

- First AI model load takes several minutes (firmware loading)
- Subsequent loads are much faster (cached)
- In headless mode, you won't see the viewfinder - use video recording instead
- For remote viewing, consider streaming via network or saving images/videos
- Your SSD is mounted at `/mnt/storage` with 1.8TB of space available
- Use VLC Media Player (Standard) to view .264 video files on Windows
