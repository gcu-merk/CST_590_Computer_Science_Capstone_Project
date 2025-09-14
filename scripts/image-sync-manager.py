#!/usr/bin/env python3
"""
Image Synchronization Manager for Host-Capture/Container-Process Architecture
Coordinates between host-side camera capture and Docker container image processing

This script manages:
- Starting/stopping host camera capture service
- Monitoring image directory health
- Coordinating with Docker container startup/shutdown
- Cleaning up processed images
- Health monitoring and recovery
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
from typing import Dict, Any, Optional
import docker

# Configure logging to SSD storage
log_dir = Path("/mnt/storage/logs/applications")
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'image-sync-manager.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ImageSyncManager:
    """Manages coordination between host capture and container processing"""
    
    def __init__(self, 
                 capture_dir: str = "/mnt/storage/camera_capture",
                 container_name: str = "traffic-monitoring-edge",
                 service_name: str = "host-camera-capture",
                 check_interval: float = 30.0,
                 max_image_age_hours: float = 4.0,
                 cleanup_interval_hours: float = 1.0):
        
        self.capture_dir = Path(capture_dir)
        self.container_name = container_name
        self.service_name = service_name
        self.check_interval = check_interval
        self.max_image_age_hours = max_image_age_hours
        self.cleanup_interval_hours = cleanup_interval_hours
        
        # Directories
        self.live_dir = self.capture_dir / "live"
        self.snapshots_dir = self.capture_dir / "periodic_snapshots"
        self.metadata_dir = self.capture_dir / "metadata"
        self.processed_dir = self.capture_dir / "processed"
        
        # Docker client
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            logger.warning(f"Docker client not available: {e}")
            self.docker_client = None
        
        # State tracking
        self.running = False
        self.last_cleanup_time = datetime.now()
        self.service_restarts = 0
        self.container_restarts = 0
        
        # Threading
        self.monitor_thread = None
        self.cleanup_thread = None
        
        logger.info(f"Image sync manager initialized: {self.capture_dir}")
        self._verify_directories()
    
    def _verify_directories(self):
        """Create and verify required directories"""
        for directory in [self.live_dir, self.snapshots_dir, self.metadata_dir, self.processed_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Directory verified: {directory}")
    
    def start_management(self):
        """Start the image synchronization management"""
        if self.running:
            logger.warning("Image sync manager already running")
            return
        
        logger.info("Starting image synchronization management...")
        self.running = True
        
        # Start host camera capture service
        self._ensure_capture_service_running()
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
        
        logger.info("Image sync manager started successfully")
        return True
    
    def stop_management(self):
        """Stop the image synchronization management"""
        logger.info("Stopping image sync manager...")
        self.running = False
        
        # Wait for threads to finish
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=10)
        if self.cleanup_thread and self.cleanup_thread.is_alive():
            self.cleanup_thread.join(timeout=10)
        
        logger.info("Image sync manager stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        logger.info("Starting monitoring loop...")
        
        while self.running:
            try:
                # Check capture service health
                self._check_capture_service()
                
                # Check container health
                self._check_container_health()
                
                # Check image directory health
                self._check_image_directory_health()
                
                # Sleep until next check
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                time.sleep(10)
    
    def _cleanup_loop(self):
        """Cleanup loop for managing old images"""
        while self.running:
            try:
                now = datetime.now()
                if (now - self.last_cleanup_time).total_seconds() >= (self.cleanup_interval_hours * 3600):
                    self._cleanup_old_images()
                    self.last_cleanup_time = now
                
                time.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
                time.sleep(300)
    
    def _ensure_capture_service_running(self):
        """Ensure the host camera capture service is running"""
        try:
            # Check if service is active
            result = subprocess.run(['systemctl', 'is-active', self.service_name], 
                                 capture_output=True, text=True)
            
            if result.returncode != 0 or result.stdout.strip() != 'active':
                logger.info(f"Starting {self.service_name} service...")
                
                # Start the service
                start_result = subprocess.run(['sudo', 'systemctl', 'start', self.service_name], 
                                           capture_output=True, text=True)
                
                if start_result.returncode == 0:
                    logger.info(f"{self.service_name} service started successfully")
                    self.service_restarts += 1
                else:
                    logger.error(f"Failed to start {self.service_name}: {start_result.stderr}")
            else:
                logger.debug(f"{self.service_name} service is running")
                
        except Exception as e:
            logger.error(f"Error checking capture service: {e}")
    
    def _check_capture_service(self):
        """Check health of the capture service"""
        try:
            # Check service status
            result = subprocess.run(['systemctl', 'status', self.service_name], 
                                 capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.warning(f"{self.service_name} service not healthy, restarting...")
                self._ensure_capture_service_running()
            
            # Check if images are being created
            image_files = list(self.live_dir.glob("*.jpg"))
            if image_files:
                # Check age of newest image
                newest_file = max(image_files, key=lambda x: x.stat().st_mtime)
                image_age = time.time() - newest_file.stat().st_mtime
                
                if image_age > 60:  # No new images for 1 minute
                    logger.warning(f"No recent images detected (newest: {image_age:.1f}s old)")
                    logger.info("Restarting capture service due to stale images...")
                    self._restart_capture_service()
            else:
                logger.warning("No images found in capture directory")
                
        except Exception as e:
            logger.error(f"Error checking capture service health: {e}")
    
    def _restart_capture_service(self):
        """Restart the capture service"""
        try:
            logger.info(f"Restarting {self.service_name} service...")
            
            # Stop service
            subprocess.run(['sudo', 'systemctl', 'stop', self.service_name], 
                         capture_output=True, text=True)
            time.sleep(2)
            
            # Start service
            result = subprocess.run(['sudo', 'systemctl', 'start', self.service_name], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"{self.service_name} service restarted successfully")
                self.service_restarts += 1
            else:
                logger.error(f"Failed to restart {self.service_name}: {result.stderr}")
                
        except Exception as e:
            logger.error(f"Error restarting capture service: {e}")
    
    def _check_container_health(self):
        """Check health of the Docker container"""
        if not self.docker_client:
            return
        
        try:
            container = self.docker_client.containers.get(self.container_name)
            
            if container.status != 'running':
                logger.warning(f"Container {self.container_name} not running: {container.status}")
                
                if container.status == 'exited':
                    logger.info("Attempting to restart container...")
                    container.restart()
                    self.container_restarts += 1
                    logger.info("Container restarted")
            else:
                logger.debug(f"Container {self.container_name} is healthy")
                
        except docker.errors.NotFound:
            logger.warning(f"Container {self.container_name} not found")
        except Exception as e:
            logger.error(f"Error checking container health: {e}")
    
    def _check_image_directory_health(self):
        """Check health of the image directory"""
        try:
            # Check disk space
            total, used, free = self._get_disk_usage()
            free_percent = (free / total) * 100
            
            if free_percent < 10:  # Less than 10% free space
                logger.warning(f"Low disk space: {free_percent:.1f}% free")
                self._emergency_cleanup()
            
            # Check image count
            image_count = len(list(self.live_dir.glob("*.jpg")))
            if image_count > 1000:  # Too many images
                logger.warning(f"Too many images in live directory: {image_count}")
                self._cleanup_old_images()
            
            # Check for orphaned metadata files
            metadata_files = list(self.metadata_dir.glob("*.json"))
            image_files = list(self.live_dir.glob("*.jpg"))
            image_names = {f.name for f in image_files}
            
            orphaned_count = 0
            for metadata_file in metadata_files:
                image_name = metadata_file.stem
                if image_name not in image_names:
                    metadata_file.unlink()
                    orphaned_count += 1
            
            if orphaned_count > 0:
                logger.info(f"Cleaned up {orphaned_count} orphaned metadata files")
                
        except Exception as e:
            logger.error(f"Error checking image directory health: {e}")
    
    def _get_disk_usage(self) -> tuple:
        """Get disk usage statistics"""
        statvfs = os.statvfs(self.capture_dir)
        total = statvfs.f_frsize * statvfs.f_blocks
        free = statvfs.f_frsize * statvfs.f_bavail
        used = total - free
        return total, used, free
    
    def _cleanup_old_images(self):
        """Clean up old images to prevent disk space issues"""
        try:
            cutoff_time = time.time() - (self.max_image_age_hours * 3600)
            cleaned_count = 0
            
            # Clean up live images
            for image_file in self.live_dir.glob("*.jpg"):
                if image_file.stat().st_mtime < cutoff_time:
                    # Move to processed directory instead of deleting
                    processed_file = self.processed_dir / image_file.name
                    if not processed_file.exists():
                        image_file.rename(processed_file)
                        cleaned_count += 1
                    else:
                        image_file.unlink()
                    
                    # Clean up corresponding metadata
                    metadata_file = self.metadata_dir / f"{image_file.name}.json"
                    if metadata_file.exists():
                        metadata_file.unlink()
            
            # Clean up old snapshots
            for snapshot_file in self.snapshots_dir.glob("*.jpg"):
                if snapshot_file.stat().st_mtime < cutoff_time:
                    snapshot_file.unlink()
                    cleaned_count += 1
            
            # Clean up old processed files (keep for 24 hours)
            processed_cutoff = time.time() - (24 * 3600)
            for processed_file in self.processed_dir.glob("*.jpg"):
                if processed_file.stat().st_mtime < processed_cutoff:
                    processed_file.unlink()
                    cleaned_count += 1
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} old image files")
                
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
    
    def _emergency_cleanup(self):
        """Emergency cleanup when disk space is critically low"""
        try:
            logger.warning("Performing emergency cleanup due to low disk space")
            
            # Remove all but the most recent 50 images
            image_files = list(self.live_dir.glob("*.jpg"))
            image_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            for image_file in image_files[50:]:  # Keep only 50 newest
                image_file.unlink()
                
                # Remove corresponding metadata
                metadata_file = self.metadata_dir / f"{image_file.name}.json"
                if metadata_file.exists():
                    metadata_file.unlink()
            
            # Remove all processed files
            for processed_file in self.processed_dir.glob("*.jpg"):
                processed_file.unlink()
            
            # Remove old snapshots
            snapshot_files = list(self.snapshots_dir.glob("*.jpg"))
            snapshot_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            for snapshot_file in snapshot_files[10:]:  # Keep only 10 newest snapshots
                snapshot_file.unlink()
            
            logger.info("Emergency cleanup completed")
            
        except Exception as e:
            logger.error(f"Emergency cleanup error: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current sync manager status"""
        try:
            # Disk usage
            total, used, free = self._get_disk_usage()
            
            # Image counts
            live_images = len(list(self.live_dir.glob("*.jpg")))
            snapshots = len(list(self.snapshots_dir.glob("*.jpg")))
            processed = len(list(self.processed_dir.glob("*.jpg")))
            
            # Service status
            try:
                service_result = subprocess.run(['systemctl', 'is-active', self.service_name], 
                                             capture_output=True, text=True)
                service_status = service_result.stdout.strip()
            except:
                service_status = 'unknown'
            
            # Container status
            container_status = 'unknown'
            if self.docker_client:
                try:
                    container = self.docker_client.containers.get(self.container_name)
                    container_status = container.status
                except:
                    container_status = 'not_found'
            
            return {
                'running': self.running,
                'capture_dir': str(self.capture_dir),
                'disk_usage': {
                    'total_gb': total / (1024**3),
                    'used_gb': used / (1024**3),
                    'free_gb': free / (1024**3),
                    'free_percent': (free / total) * 100
                },
                'image_counts': {
                    'live': live_images,
                    'snapshots': snapshots,
                    'processed': processed
                },
                'services': {
                    'capture_service': service_status,
                    'container': container_status
                },
                'restarts': {
                    'service': self.service_restarts,
                    'container': self.container_restarts
                },
                'last_cleanup': self.last_cleanup_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get status: {e}")
            return {'error': str(e)}

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    global sync_manager
    logger.info(f"Received signal {signum}, shutting down...")
    if sync_manager:
        sync_manager.stop_management()
    sys.exit(0)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Image synchronization manager")
    parser.add_argument('--capture-dir', default='/mnt/storage/camera_capture',
                       help='Directory for captured images')
    parser.add_argument('--container-name', default='traffic-monitoring-edge',
                       help='Docker container name to monitor')
    parser.add_argument('--service-name', default='host-camera-capture',
                       help='Systemd service name for host capture')
    parser.add_argument('--check-interval', type=float, default=30.0,
                       help='Health check interval in seconds')
    parser.add_argument('--max-image-age', type=float, default=4.0,
                       help='Maximum image age in hours before cleanup')
    parser.add_argument('--cleanup-interval', type=float, default=1.0,
                       help='Cleanup interval in hours')
    parser.add_argument('--status', action='store_true',
                       help='Show status and exit')
    
    args = parser.parse_args()
    
    global sync_manager
    sync_manager = ImageSyncManager(
        capture_dir=args.capture_dir,
        container_name=args.container_name,
        service_name=args.service_name,
        check_interval=args.check_interval,
        max_image_age_hours=args.max_image_age,
        cleanup_interval_hours=args.cleanup_interval
    )
    
    # Handle status mode
    if args.status:
        status = sync_manager.get_status()
        print(json.dumps(status, indent=2))
        sys.exit(0)
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start sync manager
    if sync_manager.start_management():
        logger.info("Image sync manager is running...")
        
        try:
            # Keep main thread alive
            while sync_manager.running:
                time.sleep(60)
                
                # Log periodic status
                status = sync_manager.get_status()
                logger.info(f"Status: {status['image_counts']['live']} live images, "
                           f"{status['disk_usage']['free_gb']:.1f}GB free, "
                           f"service: {status['services']['capture_service']}, "
                           f"container: {status['services']['container']}")
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        finally:
            sync_manager.stop_management()
    else:
        logger.error("Failed to start sync manager")
        sys.exit(1)

if __name__ == "__main__":
    main()