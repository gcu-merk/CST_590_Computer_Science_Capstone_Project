#!/usr/bin/env python3
"""
Container-based Data Maintenance System
Lightweight maintenance script designed to run inside Docker containers
Handles file cleanup, log rotation, and health monitoring within container environment

Usage:
    python3 container-maintenance.py --daily-cleanup
    python3 container-maintenance.py --emergency-cleanup  
    python3 container-maintenance.py --status
    python3 container-maintenance.py --daemon
"""

import os
import sys
import json
import time
import logging
import argparse
import signal
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import shutil
import subprocess
import glob

class ContainerMaintenanceConfig:
    """Configuration for container-based maintenance"""
    
    def __init__(self):
        # Container-specific paths (inside container)
        self.data_path = Path(os.getenv('DATA_VOLUME', '/mnt/storage'))
        self.camera_path = self.data_path / "camera_capture"
        self.live_dir = self.camera_path / "live"
        self.processed_dir = self.camera_path / "processed"
        self.metadata_dir = self.camera_path / "metadata"
        self.snapshots_dir = self.data_path / "periodic_snapshots"
        self.ai_images_dir = self.data_path / "ai_camera_images"
        self.logs_dir = self.data_path / "logs"
        self.temp_dir = Path("/tmp")
        
        # Maintenance settings (container-optimized)
        self.image_max_age_hours = float(os.getenv('MAINTENANCE_IMAGE_MAX_AGE_HOURS', '24'))
        self.snapshot_max_age_hours = float(os.getenv('MAINTENANCE_SNAPSHOT_MAX_AGE_HOURS', '168'))  # 1 week
        self.processed_max_age_hours = float(os.getenv('MAINTENANCE_PROCESSED_MAX_AGE_HOURS', '48'))
        self.log_max_age_days = int(os.getenv('MAINTENANCE_LOG_MAX_AGE_DAYS', '30'))
        self.log_max_size_mb = int(os.getenv('MAINTENANCE_LOG_MAX_SIZE_MB', '50'))
        
        # Emergency thresholds
        self.emergency_threshold_percent = float(os.getenv('MAINTENANCE_EMERGENCY_THRESHOLD', '90'))
        self.warning_threshold_percent = float(os.getenv('MAINTENANCE_WARNING_THRESHOLD', '80'))
        
        # Container limits
        self.max_live_images = int(os.getenv('MAINTENANCE_MAX_LIVE_IMAGES', '500'))
        self.max_processed_images = int(os.getenv('MAINTENANCE_MAX_PROCESSED_IMAGES', '200'))
        self.max_snapshots = int(os.getenv('MAINTENANCE_MAX_SNAPSHOTS', '100'))


class ContainerMaintenance:
    """Lightweight maintenance system for Docker containers"""
    
    def __init__(self, config: ContainerMaintenanceConfig):
        self.config = config
        self.logger = self._setup_logging()
        self.running = False
        self.stats = {
            'last_cleanup': None,
            'images_cleaned': 0,
            'logs_cleaned': 0,
            'space_freed_mb': 0,
            'emergency_cleanups': 0
        }
        
        # Ensure required directories exist
        self._ensure_directories()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup container-appropriate logging"""
        logger = logging.getLogger('container_maintenance')
        logger.setLevel(logging.INFO)
        
        # Console handler (for Docker logs)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # File handler (if log directory is writable)
        try:
            log_dir = self.config.logs_dir / "maintenance"
            log_dir.mkdir(parents=True, exist_ok=True)
            
            log_file = log_dir / "container-maintenance.log"
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.INFO)
            
            # Formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(formatter)
            file_handler.setFormatter(formatter)
            
            logger.addHandler(file_handler)
            
        except Exception as e:
            # If file logging fails, continue with console only
            console_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            ))
        
        logger.addHandler(console_handler)
        return logger
    
    def _ensure_directories(self):
        """Ensure required directories exist"""
        directories = [
            self.config.live_dir,
            self.config.processed_dir,
            self.config.metadata_dir,
            self.config.snapshots_dir,
            self.config.logs_dir / "maintenance"
        ]
        
        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                self.logger.warning(f"Could not create directory {directory}: {e}")
    
    def get_disk_usage(self, path: str = None) -> Dict[str, float]:
        """Get disk usage for specified path or data volume"""
        try:
            check_path = path or str(self.config.data_path)
            total, used, free = shutil.disk_usage(check_path)
            
            return {
                'total_gb': total / (1024**3),
                'used_gb': used / (1024**3),
                'free_gb': free / (1024**3),
                'used_percent': (used / total) * 100,
                'free_percent': (free / total) * 100
            }
        except Exception as e:
            self.logger.error(f"Failed to get disk usage for {check_path}: {e}")
            return {'error': str(e)}
    
    def cleanup_images(self) -> Dict[str, int]:
        """Clean up old image files"""
        cleanup_stats = {
            'live_images_moved': 0,
            'live_images_removed': 0,
            'processed_images_removed': 0,
            'snapshots_removed': 0,
            'ai_images_removed': 0,
            'metadata_files_removed': 0,
            'space_freed_mb': 0
        }
        
        try:
            current_time = time.time()
            
            # Clean up live images (move to processed first, then remove if too old)
            if self.config.live_dir.exists():
                cleanup_stats.update(self._cleanup_live_images(current_time))
            
            # Clean up processed images
            if self.config.processed_dir.exists():
                processed_cutoff = current_time - (self.config.processed_max_age_hours * 3600)
                cleanup_stats['processed_images_removed'] = self._cleanup_directory(
                    self.config.processed_dir, processed_cutoff, "*.jpg"
                )
            
            # Clean up snapshots
            if self.config.snapshots_dir.exists():
                snapshot_cutoff = current_time - (self.config.snapshot_max_age_hours * 3600)
                cleanup_stats['snapshots_removed'] = self._cleanup_directory(
                    self.config.snapshots_dir, snapshot_cutoff, "*.jpg"
                )
            
            # Clean up AI camera images
            if self.config.ai_images_dir.exists():
                ai_cutoff = current_time - (self.config.image_max_age_hours * 3600)
                cleanup_stats['ai_images_removed'] = self._cleanup_directory(
                    self.config.ai_images_dir, ai_cutoff, "*.jpg"
                )
            
            # Clean up orphaned metadata
            if self.config.metadata_dir.exists():
                cleanup_stats['metadata_files_removed'] = self._cleanup_orphaned_metadata()
            
            # Enforce count limits
            self._enforce_count_limits(cleanup_stats)
            
            total_removed = sum([
                cleanup_stats['live_images_removed'],
                cleanup_stats['processed_images_removed'],
                cleanup_stats['snapshots_removed'],
                cleanup_stats['ai_images_removed']
            ])
            
            if total_removed > 0:
                self.logger.info(f"Image cleanup completed: {total_removed} files removed, "
                               f"{cleanup_stats['live_images_moved']} files moved to processed")
                self.stats['images_cleaned'] += total_removed
            
        except Exception as e:
            self.logger.error(f"Image cleanup failed: {e}")
        
        return cleanup_stats
    
    def _cleanup_live_images(self, current_time: float) -> Dict[str, int]:
        """Clean up live images with smart move-to-processed logic"""
        stats = {'live_images_moved': 0, 'live_images_removed': 0, 'space_freed_mb': 0}
        
        try:
            live_cutoff = current_time - (self.config.image_max_age_hours * 3600)
            
            for image_file in self.config.live_dir.glob("*.jpg"):
                if image_file.stat().st_mtime < live_cutoff:
                    file_size = image_file.stat().st_size
                    
                    # Try to move to processed first
                    processed_file = self.config.processed_dir / image_file.name
                    if not processed_file.exists():
                        try:
                            image_file.rename(processed_file)
                            stats['live_images_moved'] += 1
                            self.logger.debug(f"Moved {image_file.name} to processed")
                        except Exception as e:
                            # If move fails, delete the file
                            image_file.unlink()
                            stats['live_images_removed'] += 1
                            stats['space_freed_mb'] += file_size / (1024 * 1024)
                            self.logger.debug(f"Removed {image_file.name} (move failed: {e})")
                    else:
                        # Processed file already exists, remove live file
                        image_file.unlink()
                        stats['live_images_removed'] += 1
                        stats['space_freed_mb'] += file_size / (1024 * 1024)
                    
                    # Clean up corresponding metadata
                    metadata_file = self.config.metadata_dir / f"{image_file.name}.json"
                    if metadata_file.exists():
                        metadata_file.unlink()
                        
        except Exception as e:
            self.logger.error(f"Live images cleanup failed: {e}")
        
        return stats
    
    def _cleanup_directory(self, directory: Path, cutoff_time: float, pattern: str) -> int:
        """Clean up files in directory older than cutoff time"""
        removed_count = 0
        
        try:
            for file_path in directory.glob(pattern):
                if file_path.stat().st_mtime < cutoff_time:
                    file_size = file_path.stat().st_size
                    file_path.unlink()
                    removed_count += 1
                    self.stats['space_freed_mb'] += file_size / (1024 * 1024)
                    
        except Exception as e:
            self.logger.error(f"Failed to cleanup {directory}: {e}")
        
        return removed_count
    
    def _cleanup_orphaned_metadata(self) -> int:
        """Remove metadata files without corresponding images"""
        removed_count = 0
        
        try:
            # Get existing image names
            live_images = {f.stem for f in self.config.live_dir.glob("*.jpg")} if self.config.live_dir.exists() else set()
            processed_images = {f.stem for f in self.config.processed_dir.glob("*.jpg")} if self.config.processed_dir.exists() else set()
            all_images = live_images.union(processed_images)
            
            # Remove orphaned metadata
            for metadata_file in self.config.metadata_dir.glob("*.json"):
                image_name = metadata_file.stem
                if image_name not in all_images:
                    metadata_file.unlink()
                    removed_count += 1
                    
        except Exception as e:
            self.logger.error(f"Orphaned metadata cleanup failed: {e}")
        
        return removed_count
    
    def _enforce_count_limits(self, cleanup_stats: Dict[str, int]):
        """Enforce maximum file count limits"""
        try:
            # Limit live images
            if self.config.live_dir.exists():
                live_images = list(self.config.live_dir.glob("*.jpg"))
                if len(live_images) > self.config.max_live_images:
                    # Sort by modification time, keep newest
                    live_images.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                    excess_images = live_images[self.config.max_live_images:]
                    
                    for image_file in excess_images:
                        # Move to processed if possible, otherwise delete
                        processed_file = self.config.processed_dir / image_file.name
                        if not processed_file.exists():
                            image_file.rename(processed_file)
                            cleanup_stats['live_images_moved'] += 1
                        else:
                            file_size = image_file.stat().st_size
                            image_file.unlink()
                            cleanup_stats['live_images_removed'] += 1
                            cleanup_stats['space_freed_mb'] += file_size / (1024 * 1024)
            
            # Limit processed images
            if self.config.processed_dir.exists():
                processed_images = list(self.config.processed_dir.glob("*.jpg"))
                if len(processed_images) > self.config.max_processed_images:
                    processed_images.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                    excess_images = processed_images[self.config.max_processed_images:]
                    
                    for image_file in excess_images:
                        file_size = image_file.stat().st_size
                        image_file.unlink()
                        cleanup_stats['processed_images_removed'] += 1
                        cleanup_stats['space_freed_mb'] += file_size / (1024 * 1024)
            
            # Limit snapshots
            if self.config.snapshots_dir.exists():
                snapshots = list(self.config.snapshots_dir.glob("*.jpg"))
                if len(snapshots) > self.config.max_snapshots:
                    snapshots.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                    excess_snapshots = snapshots[self.config.max_snapshots:]
                    
                    for snapshot_file in excess_snapshots:
                        file_size = snapshot_file.stat().st_size
                        snapshot_file.unlink()
                        cleanup_stats['snapshots_removed'] += 1
                        cleanup_stats['space_freed_mb'] += file_size / (1024 * 1024)
                        
        except Exception as e:
            self.logger.error(f"Count limit enforcement failed: {e}")
    
    def cleanup_logs(self) -> Dict[str, int]:
        """Clean up old log files"""
        cleanup_stats = {
            'log_files_removed': 0,
            'log_files_rotated': 0,
            'temp_files_removed': 0,
            'space_freed_mb': 0
        }
        
        try:
            current_time = time.time()
            log_cutoff = current_time - (self.config.log_max_age_days * 24 * 3600)
            max_size_bytes = self.config.log_max_size_mb * 1024 * 1024
            
            # Clean up application logs
            if self.config.logs_dir.exists():
                for log_file in self.config.logs_dir.rglob("*.log"):
                    try:
                        file_stat = log_file.stat()
                        
                        # Remove old log files
                        if file_stat.st_mtime < log_cutoff:
                            file_size = file_stat.st_size
                            log_file.unlink()
                            cleanup_stats['log_files_removed'] += 1
                            cleanup_stats['space_freed_mb'] += file_size / (1024 * 1024)
                        
                        # Rotate large log files
                        elif file_stat.st_size > max_size_bytes:
                            rotated_name = f"{log_file}.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                            log_file.rename(log_file.parent / rotated_name)
                            log_file.touch()  # Create new empty log file
                            cleanup_stats['log_files_rotated'] += 1
                            
                    except Exception as e:
                        self.logger.warning(f"Failed to process log file {log_file}: {e}")
            
            # Clean up temporary files
            temp_cutoff = current_time - (24 * 3600)  # 1 day old temp files
            for temp_file in self.config.temp_dir.glob("*"):
                try:
                    if temp_file.is_file() and temp_file.stat().st_mtime < temp_cutoff:
                        if temp_file.name.startswith(('tmp', 'camera', 'image', 'capture')):
                            file_size = temp_file.stat().st_size
                            temp_file.unlink()
                            cleanup_stats['temp_files_removed'] += 1
                            cleanup_stats['space_freed_mb'] += file_size / (1024 * 1024)
                except Exception:
                    pass  # Skip files we can't access
            
            if cleanup_stats['log_files_removed'] + cleanup_stats['temp_files_removed'] > 0:
                self.logger.info(f"Log cleanup completed: {cleanup_stats['log_files_removed']} logs removed, "
                               f"{cleanup_stats['temp_files_removed']} temp files removed")
            
        except Exception as e:
            self.logger.error(f"Log cleanup failed: {e}")
        
        return cleanup_stats
    
    def emergency_cleanup(self) -> Dict[str, int]:
        """Perform emergency cleanup when disk space is critically low"""
        self.logger.warning("Performing emergency cleanup due to low disk space")
        self.stats['emergency_cleanups'] += 1
        
        emergency_stats = {
            'images_removed': 0,
            'logs_removed': 0,
            'temp_files_removed': 0,
            'space_freed_mb': 0
        }
        
        try:
            # Keep only the most recent 25 images in live directory
            if self.config.live_dir.exists():
                live_images = list(self.config.live_dir.glob("*.jpg"))
                live_images.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                
                for image_file in live_images[25:]:  # Remove all but 25 newest
                    file_size = image_file.stat().st_size
                    image_file.unlink()
                    emergency_stats['images_removed'] += 1
                    emergency_stats['space_freed_mb'] += file_size / (1024 * 1024)
                    
                    # Remove corresponding metadata
                    metadata_file = self.config.metadata_dir / f"{image_file.name}.json"
                    if metadata_file.exists():
                        metadata_file.unlink()
            
            # Remove all processed images
            if self.config.processed_dir.exists():
                for processed_file in self.config.processed_dir.glob("*.jpg"):
                    file_size = processed_file.stat().st_size
                    processed_file.unlink()
                    emergency_stats['images_removed'] += 1
                    emergency_stats['space_freed_mb'] += file_size / (1024 * 1024)
            
            # Keep only 5 most recent snapshots
            if self.config.snapshots_dir.exists():
                snapshots = list(self.config.snapshots_dir.glob("*.jpg"))
                snapshots.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                
                for snapshot_file in snapshots[5:]:
                    file_size = snapshot_file.stat().st_size
                    snapshot_file.unlink()
                    emergency_stats['images_removed'] += 1
                    emergency_stats['space_freed_mb'] += file_size / (1024 * 1024)
            
            # Remove all temporary files
            for temp_file in self.config.temp_dir.glob("*"):
                try:
                    if temp_file.is_file():
                        file_size = temp_file.stat().st_size
                        temp_file.unlink()
                        emergency_stats['temp_files_removed'] += 1
                        emergency_stats['space_freed_mb'] += file_size / (1024 * 1024)
                except:
                    pass
            
            # Remove large log files
            if self.config.logs_dir.exists():
                for log_file in self.config.logs_dir.rglob("*.log"):
                    try:
                        if log_file.stat().st_size > (10 * 1024 * 1024):  # > 10MB
                            file_size = log_file.stat().st_size
                            log_file.unlink()
                            emergency_stats['logs_removed'] += 1
                            emergency_stats['space_freed_mb'] += file_size / (1024 * 1024)
                    except:
                        pass
            
            total_removed = emergency_stats['images_removed'] + emergency_stats['temp_files_removed'] + emergency_stats['logs_removed']
            self.logger.warning(f"Emergency cleanup completed: {total_removed} files removed, "
                              f"{emergency_stats['space_freed_mb']:.1f} MB freed")
            
        except Exception as e:
            self.logger.error(f"Emergency cleanup failed: {e}")
        
        return emergency_stats
    
    def check_disk_health(self) -> Dict[str, any]:
        """Check disk health and determine if cleanup is needed"""
        health_status = {
            'disk_usage': self.get_disk_usage(),
            'needs_cleanup': False,
            'needs_emergency_cleanup': False,
            'warnings': [],
            'file_counts': {}
        }
        
        try:
            # Check disk usage
            usage = health_status['disk_usage']
            if 'used_percent' in usage:
                used_percent = usage['used_percent']
                
                if used_percent >= self.config.emergency_threshold_percent:
                    health_status['needs_emergency_cleanup'] = True
                    health_status['warnings'].append(f"Critical disk usage: {used_percent:.1f}%")
                elif used_percent >= self.config.warning_threshold_percent:
                    health_status['needs_cleanup'] = True
                    health_status['warnings'].append(f"High disk usage: {used_percent:.1f}%")
            
            # Check file counts
            file_counts = {}
            if self.config.live_dir.exists():
                file_counts['live_images'] = len(list(self.config.live_dir.glob("*.jpg")))
            if self.config.processed_dir.exists():
                file_counts['processed_images'] = len(list(self.config.processed_dir.glob("*.jpg")))
            if self.config.snapshots_dir.exists():
                file_counts['snapshots'] = len(list(self.config.snapshots_dir.glob("*.jpg")))
            if self.config.metadata_dir.exists():
                file_counts['metadata_files'] = len(list(self.config.metadata_dir.glob("*.json")))
            
            health_status['file_counts'] = file_counts
            
            # Check for high file counts
            if file_counts.get('live_images', 0) > self.config.max_live_images:
                health_status['needs_cleanup'] = True
                health_status['warnings'].append(f"High live image count: {file_counts['live_images']}")
            
        except Exception as e:
            health_status['warnings'].append(f"Health check error: {e}")
        
        return health_status
    
    def get_status_report(self) -> Dict[str, any]:
        """Generate status report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'container_id': os.getenv('HOSTNAME', 'unknown'),
            'config': {
                'image_max_age_hours': self.config.image_max_age_hours,
                'snapshot_max_age_hours': self.config.snapshot_max_age_hours,
                'log_max_age_days': self.config.log_max_age_days,
                'max_live_images': self.config.max_live_images
            },
            'statistics': self.stats.copy(),
            'health': self.check_disk_health()
        }
        
        return report
    
    def run_daily_maintenance(self):
        """Run complete daily maintenance cycle"""
        self.logger.info("Starting daily maintenance cycle")
        start_time = time.time()
        
        try:
            # Check health first
            health = self.check_disk_health()
            
            if health['needs_emergency_cleanup']:
                self.emergency_cleanup()
            elif health['needs_cleanup']:
                self.cleanup_images()
                self.cleanup_logs()
            else:
                # Regular maintenance
                self.cleanup_images()
                self.cleanup_logs()
            
            # Update statistics
            self.stats['last_cleanup'] = datetime.now().isoformat()
            
            duration = time.time() - start_time
            self.logger.info(f"Daily maintenance completed in {duration:.1f} seconds")
            
        except Exception as e:
            self.logger.error(f"Daily maintenance failed: {e}")
    
    def run_daemon(self):
        """Run as daemon (for container environments)"""
        self.logger.info("Starting container maintenance daemon")
        self.running = True
        
        def signal_handler(signum, frame):
            self.logger.info("Received shutdown signal")
            self.running = False
        
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        # Run maintenance every 6 hours
        maintenance_interval = 6 * 3600  # 6 hours
        last_maintenance = 0
        
        while self.running:
            try:
                current_time = time.time()
                
                # Run maintenance if interval has passed
                if current_time - last_maintenance >= maintenance_interval:
                    self.run_daily_maintenance()
                    last_maintenance = current_time
                
                # Sleep for 5 minutes between checks
                time.sleep(300)
                
            except Exception as e:
                self.logger.error(f"Daemon loop error: {e}")
                time.sleep(300)
        
        self.logger.info("Container maintenance daemon stopped")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Container Data Maintenance')
    parser.add_argument('--daily-cleanup', action='store_true',
                       help='Run daily maintenance cycle')
    parser.add_argument('--emergency-cleanup', action='store_true',
                       help='Run emergency cleanup')
    parser.add_argument('--status', '-s', action='store_true',
                       help='Show status report')
    parser.add_argument('--daemon', '-d', action='store_true',
                       help='Run as daemon')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    # Set up logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create configuration and maintenance manager
    config = ContainerMaintenanceConfig()
    maintenance = ContainerMaintenance(config)
    
    try:
        if args.daemon:
            maintenance.run_daemon()
        elif args.daily_cleanup:
            maintenance.run_daily_maintenance()
            print("Daily maintenance completed")
        elif args.emergency_cleanup:
            stats = maintenance.emergency_cleanup()
            print(f"Emergency cleanup completed: {json.dumps(stats, indent=2)}")
        elif args.status:
            report = maintenance.get_status_report()
            print(json.dumps(report, indent=2))
        else:
            parser.print_help()
            return 1
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())