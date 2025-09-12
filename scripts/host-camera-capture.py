#!/usr/bin/env python3
"""
Host-side camera capture script for Raspberry Pi 5 with IMX500 AI Camera
Captures images using rpicam-still and saves them to shared volume for Docker container processing

This script runs on the Raspberry Pi host system to work around OpenCV 4.12.0 
compatibility issues with the IMX500 AI camera's V4L2 backend in Docker containers.

Features:
- High-quality image capture (4056x3040, ~1.4MB)
- Automatic image rotation and cleanup
- Configurable capture intervals
- Health monitoring and error recovery
- Shared volume coordination with Docker containers
"""

import os
import sys
import time
import json
import logging
import argparse
import subprocess
import signal
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/host-camera-capture.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HostCameraCapture:
    """Host-side camera capture service for Docker container processing"""
    
    def __init__(self, 
                 capture_dir: str = "/mnt/storage/camera_capture",
                 capture_interval: float = 1.0,
                 image_width: int = 4056,
                 image_height: int = 3040,
                 jpeg_quality: int = 95,
                 max_images: int = 100,
                 enable_periodic_snapshots: bool = True,
                 snapshot_interval: int = 300):  # 5 minutes
        
        self.capture_dir = Path(capture_dir)
        self.capture_interval = capture_interval
        self.image_width = image_width
        self.image_height = image_height
        self.jpeg_quality = jpeg_quality
        self.max_images = max_images
        self.enable_periodic_snapshots = enable_periodic_snapshots
        self.snapshot_interval = snapshot_interval
        
        # Create directories
        self.live_dir = self.capture_dir / "live"
        self.snapshots_dir = self.capture_dir / "periodic_snapshots"
        self.metadata_dir = self.capture_dir / "metadata"
        
        for directory in [self.live_dir, self.snapshots_dir, self.metadata_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # State tracking
        self.running = False
        self.capture_count = 0
        self.last_snapshot_time = datetime.now()
        self.error_count = 0
        self.last_successful_capture = None
        
        # Threading
        self.capture_thread = None
        self.cleanup_thread = None
        self.snapshot_thread = None
        
        logger.info(f"Host camera capture initialized: {self.capture_dir}")
        logger.info(f"Image resolution: {self.image_width}x{self.image_height}")
        logger.info(f"Capture interval: {self.capture_interval}s")
    
    def start_capture(self):
        """Start the camera capture service"""
        if self.running:
            logger.warning("Capture service already running")
            return
        
        logger.info("Starting host camera capture service...")
        self.running = True
        
        # Test camera first
        if not self._test_camera():
            logger.error("Camera test failed - cannot start capture service")
            self.running = False
            return False
        
        # Start capture thread
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
        
        # Start periodic snapshot thread if enabled
        if self.enable_periodic_snapshots:
            self.snapshot_thread = threading.Thread(target=self._snapshot_loop, daemon=True)
            self.snapshot_thread.start()
        
        logger.info("Host camera capture service started successfully")
        return True
    
    def stop_capture(self):
        """Stop the camera capture service"""
        logger.info("Stopping host camera capture service...")
        self.running = False
        
        # Wait for threads to finish
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=5)
        if self.cleanup_thread and self.cleanup_thread.is_alive():
            self.cleanup_thread.join(timeout=5)
        if self.snapshot_thread and self.snapshot_thread.is_alive():
            self.snapshot_thread.join(timeout=5)
        
        logger.info("Host camera capture service stopped")
    
    def _test_camera(self) -> bool:
        """Test camera functionality with rpicam-still"""
        try:
            logger.info("Testing camera with rpicam-still...")
            
            test_file = self.capture_dir / "camera_test.jpg"
            cmd = [
                'rpicam-still',
                '-o', str(test_file),
                '--immediate',
                '--width', str(self.image_width),
                '--height', str(self.image_height),
                '--quality', str(self.jpeg_quality),
                '--timeout', '5000'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and test_file.exists() and test_file.stat().st_size > 100000:
                logger.info(f"Camera test successful: {test_file.stat().st_size} bytes")
                test_file.unlink()  # Clean up test file
                return True
            else:
                logger.error(f"Camera test failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Camera test exception: {e}")
            return False
    
    def _capture_loop(self):
        """Main capture loop running in separate thread"""
        logger.info("Starting capture loop...")
        
        while self.running:
            try:
                start_time = time.time()
                
                # Capture image
                success = self._capture_single_image()
                if success:
                    self.capture_count += 1
                    self.last_successful_capture = datetime.now()
                    self.error_count = 0
                else:
                    self.error_count += 1
                    logger.warning(f"Capture failed (error count: {self.error_count})")
                
                # Handle consecutive errors
                if self.error_count >= 5:
                    logger.error("Too many consecutive capture errors - restarting camera")
                    self._restart_camera()
                    self.error_count = 0
                
                # Wait for next capture interval
                elapsed = time.time() - start_time
                sleep_time = max(0, self.capture_interval - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
            except Exception as e:
                logger.error(f"Capture loop error: {e}")
                time.sleep(1)
    
    def _capture_single_image(self) -> bool:
        """Capture a single image using rpicam-still"""
        try:
            timestamp = datetime.now()
            filename = f"capture_{timestamp.strftime('%Y%m%d_%H%M%S_%f')[:-3]}.jpg"
            image_path = self.live_dir / filename
            metadata_path = self.metadata_dir / f"{filename}.json"
            
            # rpicam-still command for high-quality capture
            cmd = [
                'rpicam-still',
                '-o', str(image_path),
                '--immediate',  # Don't wait for auto-exposure/white balance
                '--width', str(self.image_width),
                '--height', str(self.image_height),
                '--quality', str(self.jpeg_quality),
                '--timeout', '3000',  # 3 second timeout
                '--nopreview',  # No preview for headless operation
                '--encoding', 'jpg'
            ]
            
            # Execute capture command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0 and image_path.exists():
                file_size = image_path.stat().st_size
                
                # Verify image size is reasonable (should be ~1.4MB for high quality)
                if file_size < 50000:  # Less than 50KB indicates problem
                    logger.warning(f"Image file too small: {file_size} bytes")
                    image_path.unlink()
                    return False
                
                # Create metadata file
                metadata = {
                    'filename': filename,
                    'timestamp': timestamp.isoformat(),
                    'capture_time': timestamp.timestamp(),
                    'file_size': file_size,
                    'resolution': f"{self.image_width}x{self.image_height}",
                    'quality': self.jpeg_quality,
                    'capture_method': 'rpicam-still',
                    'host_capture': True
                }
                
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                logger.debug(f"Captured: {filename} ({file_size} bytes)")
                return True
            else:
                logger.warning(f"rpicam-still failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.warning("Camera capture timeout")
            return False
        except Exception as e:
            logger.error(f"Capture error: {e}")
            return False
    
    def _cleanup_loop(self):
        """Cleanup old images to prevent disk space issues"""
        while self.running:
            try:
                # Get all images in live directory
                images = list(self.live_dir.glob("*.jpg"))
                images.sort(key=lambda x: x.stat().st_mtime)
                
                # Remove oldest images if we exceed max_images
                while len(images) > self.max_images:
                    old_image = images.pop(0)
                    old_metadata = self.metadata_dir / f"{old_image.name}.json"
                    
                    old_image.unlink()
                    if old_metadata.exists():
                        old_metadata.unlink()
                    
                    logger.debug(f"Cleaned up old image: {old_image.name}")
                
                # Clean up metadata files without corresponding images
                for metadata_file in self.metadata_dir.glob("*.json"):
                    image_name = metadata_file.stem
                    if not (self.live_dir / image_name).exists():
                        metadata_file.unlink()
                        logger.debug(f"Cleaned up orphaned metadata: {metadata_file.name}")
                
                # Sleep for 30 seconds before next cleanup
                time.sleep(30)
                
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
                time.sleep(30)
    
    def _snapshot_loop(self):
        """Create periodic snapshots for monitoring"""
        while self.running:
            try:
                now = datetime.now()
                if (now - self.last_snapshot_time).total_seconds() >= self.snapshot_interval:
                    self._create_snapshot()
                    self.last_snapshot_time = now
                
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Snapshot error: {e}")
                time.sleep(60)
    
    def _create_snapshot(self):
        """Create a periodic snapshot"""
        try:
            timestamp = datetime.now()
            filename = f"snapshot_{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg"
            snapshot_path = self.snapshots_dir / filename
            
            cmd = [
                'rpicam-still',
                '-o', str(snapshot_path),
                '--immediate',
                '--width', str(self.image_width),
                '--height', str(self.image_height),
                '--quality', str(self.jpeg_quality),
                '--timeout', '3000',
                '--nopreview'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0 and snapshot_path.exists():
                logger.info(f"Created periodic snapshot: {filename}")
                
                # Clean up old snapshots (keep last 24 hours)
                cutoff_time = timestamp - timedelta(hours=24)
                for old_snapshot in self.snapshots_dir.glob("snapshot_*.jpg"):
                    if old_snapshot.stat().st_mtime < cutoff_time.timestamp():
                        old_snapshot.unlink()
                        logger.debug(f"Cleaned up old snapshot: {old_snapshot.name}")
            else:
                logger.warning(f"Snapshot capture failed: {result.stderr}")
                
        except Exception as e:
            logger.error(f"Snapshot creation error: {e}")
    
    def _restart_camera(self):
        """Restart camera service (placeholder for advanced recovery)"""
        logger.info("Attempting camera restart...")
        time.sleep(2)  # Give camera time to reset
        
        if self._test_camera():
            logger.info("Camera restart successful")
        else:
            logger.error("Camera restart failed")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current capture status"""
        return {
            'running': self.running,
            'capture_count': self.capture_count,
            'error_count': self.error_count,
            'last_successful_capture': self.last_successful_capture.isoformat() if self.last_successful_capture else None,
            'capture_interval': self.capture_interval,
            'live_images': len(list(self.live_dir.glob("*.jpg"))),
            'snapshot_images': len(list(self.snapshots_dir.glob("*.jpg"))),
            'capture_dir': str(self.capture_dir)
        }

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    global capture_service
    logger.info(f"Received signal {signum}, shutting down...")
    if capture_service:
        capture_service.stop_capture()
    sys.exit(0)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Host-side camera capture for Docker processing")
    parser.add_argument('--capture-dir', default='/mnt/storage/camera_capture',
                       help='Directory for captured images')
    parser.add_argument('--interval', type=float, default=1.0,
                       help='Capture interval in seconds')
    parser.add_argument('--width', type=int, default=4056,
                       help='Image width')
    parser.add_argument('--height', type=int, default=3040,
                       help='Image height')
    parser.add_argument('--quality', type=int, default=95,
                       help='JPEG quality (1-100)')
    parser.add_argument('--max-images', type=int, default=100,
                       help='Maximum images to keep in live directory')
    parser.add_argument('--no-snapshots', action='store_true',
                       help='Disable periodic snapshots')
    parser.add_argument('--snapshot-interval', type=int, default=300,
                       help='Snapshot interval in seconds')
    parser.add_argument('--test-only', action='store_true',
                       help='Test camera and exit')
    parser.add_argument('--status', action='store_true',
                       help='Show status and exit')
    
    args = parser.parse_args()
    
    global capture_service
    capture_service = HostCameraCapture(
        capture_dir=args.capture_dir,
        capture_interval=args.interval,
        image_width=args.width,
        image_height=args.height,
        jpeg_quality=args.quality,
        max_images=args.max_images,
        enable_periodic_snapshots=not args.no_snapshots,
        snapshot_interval=args.snapshot_interval
    )
    
    # Handle test mode
    if args.test_only:
        if capture_service._test_camera():
            print("Camera test: PASSED")
            sys.exit(0)
        else:
            print("Camera test: FAILED")
            sys.exit(1)
    
    # Handle status mode
    if args.status:
        status = capture_service.get_status()
        print(json.dumps(status, indent=2))
        sys.exit(0)
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start capture service
    if capture_service.start_capture():
        logger.info("Host camera capture service is running...")
        
        try:
            # Keep main thread alive
            while capture_service.running:
                time.sleep(10)
                
                # Log periodic status
                status = capture_service.get_status()
                logger.info(f"Status: {status['capture_count']} captures, "
                           f"{status['live_images']} live images, "
                           f"{status['error_count']} errors")
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        finally:
            capture_service.stop_capture()
    else:
        logger.error("Failed to start capture service")
        sys.exit(1)

if __name__ == "__main__":
    main()