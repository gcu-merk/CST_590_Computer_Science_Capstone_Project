#!/usr/bin/env python3
"""
Data File Maintenance Manager
Unified system for managing all data file cleanup, rotation, and maintenance
across the entire camera monitoring system.

Usage:
    python3 scripts/data-maintenance-manager.py --config config/maintenance.conf
    python3 scripts/data-maintenance-manager.py --emergency-cleanup
    python3 scripts/data-maintenance-manager.py --status
"""

import os
import sys
import json
import time
import logging
import argparse
import threading
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import shutil
import subprocess

# Configuration class for maintenance settings
@dataclass
class MaintenanceConfig:
    """Configuration for data maintenance operations"""
    
    # Image cleanup settings
    image_max_age_hours: float = 24.0
    snapshot_max_age_hours: float = 168.0  # 1 week
    processed_max_age_hours: float = 48.0
    emergency_cleanup_threshold_percent: float = 10.0
    
    # Log cleanup settings  
    log_max_age_days: int = 30
    log_max_size_mb: int = 100
    docker_log_max_size_mb: int = 50
    
    # Database maintenance
    db_backup_max_age_days: int = 14
    db_vacuum_frequency_hours: int = 168  # Weekly
    
    # General settings
    cleanup_frequency_hours: float = 1.0
    monitoring_frequency_minutes: int = 5
    storage_warning_threshold_percent: float = 20.0
    storage_critical_threshold_percent: float = 10.0
    
    # Storage paths
    ssd_base_path: str = "/mnt/storage"
    sd_base_path: str = "/"
    backup_path: str = "/mnt/storage/backups"
    
    @classmethod
    def load_from_file(cls, config_path: str) -> 'MaintenanceConfig':
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            return cls(**config_data)
        except Exception as e:
            logging.warning(f"Failed to load config from {config_path}: {e}")
            return cls()  # Return default config


class DataMaintenanceManager:
    """Unified data file maintenance manager"""
    
    def __init__(self, config: MaintenanceConfig):
        self.config = config
        self.logger = self._setup_logging()
        self.running = False
        self.last_cleanup_time = datetime.now()
        self.last_db_vacuum_time = datetime.now()
        
        # Storage paths
        self.ssd_path = Path(config.ssd_base_path)
        self.camera_path = self.ssd_path / "camera_capture"
        self.live_dir = self.camera_path / "live"
        self.processed_dir = self.camera_path / "processed"
        self.metadata_dir = self.camera_path / "metadata"
        self.snapshots_dir = self.ssd_path / "periodic_snapshots"
        self.ai_images_dir = self.ssd_path / "ai_camera_images"
        self.logs_dir = self.ssd_path / "logs"
        self.backup_dir = Path(config.backup_path)
        
        # Statistics tracking
        self.stats = {
            'last_cleanup': None,
            'images_cleaned': 0,
            'logs_cleaned': 0,
            'space_freed_mb': 0,
            'db_backups_created': 0,
            'emergency_cleanups': 0
        }
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for maintenance manager"""
        logger = logging.getLogger('data_maintenance')
        logger.setLevel(logging.INFO)
        
        # Create logs directory if needed
        log_dir = Path(self.config.ssd_base_path) / "logs" / "maintenance"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # File handler
        log_file = log_dir / "data-maintenance.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def get_storage_usage(self) -> Dict[str, Dict[str, float]]:
        """Get storage usage statistics for both SD card and SSD"""
        usage = {}
        
        # SSD usage
        try:
            ssd_stat = shutil.disk_usage(self.config.ssd_base_path)
            usage['ssd'] = {
                'total_gb': ssd_stat.total / (1024**3),
                'used_gb': (ssd_stat.total - ssd_stat.free) / (1024**3),
                'free_gb': ssd_stat.free / (1024**3),
                'used_percent': ((ssd_stat.total - ssd_stat.free) / ssd_stat.total) * 100
            }
        except Exception as e:
            self.logger.error(f"Failed to get SSD usage: {e}")
            usage['ssd'] = {'error': str(e)}
        
        # SD card usage
        try:
            sd_stat = shutil.disk_usage(self.config.sd_base_path)
            usage['sd'] = {
                'total_gb': sd_stat.total / (1024**3),
                'used_gb': (sd_stat.total - sd_stat.free) / (1024**3),
                'free_gb': sd_stat.free / (1024**3),
                'used_percent': ((sd_stat.total - sd_stat.free) / sd_stat.total) * 100
            }
        except Exception as e:
            self.logger.error(f"Failed to get SD usage: {e}")
            usage['sd'] = {'error': str(e)}
        
        return usage
    
    def cleanup_images(self) -> Dict[str, int]:
        """Clean up old image files from all camera directories"""
        cleanup_stats = {
            'live_images_removed': 0,
            'processed_images_removed': 0,
            'snapshots_removed': 0,
            'ai_images_removed': 0,
            'metadata_files_removed': 0,
            'space_freed_mb': 0
        }
        
        try:
            current_time = time.time()
            
            # Clean up live images
            if self.live_dir.exists():
                live_cutoff = current_time - (self.config.image_max_age_hours * 3600)
                cleanup_stats['live_images_removed'] = self._cleanup_directory(
                    self.live_dir, live_cutoff, "*.jpg"
                )
            
            # Clean up processed images
            if self.processed_dir.exists():
                processed_cutoff = current_time - (self.config.processed_max_age_hours * 3600)
                cleanup_stats['processed_images_removed'] = self._cleanup_directory(
                    self.processed_dir, processed_cutoff, "*.jpg"
                )
            
            # Clean up snapshots
            if self.snapshots_dir.exists():
                snapshot_cutoff = current_time - (self.config.snapshot_max_age_hours * 3600)
                cleanup_stats['snapshots_removed'] = self._cleanup_directory(
                    self.snapshots_dir, snapshot_cutoff, "*.jpg"
                )
            
            # Clean up AI camera images
            if self.ai_images_dir.exists():
                ai_cutoff = current_time - (self.config.image_max_age_hours * 3600)
                cleanup_stats['ai_images_removed'] = self._cleanup_directory(
                    self.ai_images_dir, ai_cutoff, "*.jpg"
                )
            
            # Clean up orphaned metadata files
            if self.metadata_dir.exists():
                cleanup_stats['metadata_files_removed'] = self._cleanup_orphaned_metadata()
            
            # Update statistics
            total_removed = sum([
                cleanup_stats['live_images_removed'],
                cleanup_stats['processed_images_removed'],
                cleanup_stats['snapshots_removed'],
                cleanup_stats['ai_images_removed']
            ])
            
            if total_removed > 0:
                self.logger.info(f"Image cleanup completed: {total_removed} files removed")
                self.stats['images_cleaned'] += total_removed
            
        except Exception as e:
            self.logger.error(f"Image cleanup failed: {e}")
        
        return cleanup_stats
    
    def _cleanup_directory(self, directory: Path, cutoff_time: float, pattern: str) -> int:
        """Clean up files in a directory older than cutoff time"""
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
        """Remove metadata files that don't have corresponding images"""
        removed_count = 0
        
        try:
            # Get list of existing images
            live_images = {f.stem for f in self.live_dir.glob("*.jpg")} if self.live_dir.exists() else set()
            processed_images = {f.stem for f in self.processed_dir.glob("*.jpg")} if self.processed_dir.exists() else set()
            all_images = live_images.union(processed_images)
            
            # Remove metadata for non-existent images
            for metadata_file in self.metadata_dir.glob("*.json"):
                image_name = metadata_file.stem
                if image_name not in all_images:
                    metadata_file.unlink()
                    removed_count += 1
                    
        except Exception as e:
            self.logger.error(f"Failed to cleanup orphaned metadata: {e}")
        
        return removed_count
    
    def cleanup_logs(self) -> Dict[str, int]:
        """Clean up old log files"""
        cleanup_stats = {
            'log_files_rotated': 0,
            'docker_logs_cleaned': 0,
            'space_freed_mb': 0
        }
        
        try:
            current_time = time.time()
            log_cutoff = current_time - (self.config.log_max_age_days * 24 * 3600)
            
            # Clean up application logs
            if self.logs_dir.exists():
                for log_dir in self.logs_dir.iterdir():
                    if log_dir.is_dir():
                        for log_file in log_dir.glob("*.log*"):
                            if log_file.stat().st_mtime < log_cutoff:
                                file_size = log_file.stat().st_size
                                log_file.unlink()
                                cleanup_stats['log_files_rotated'] += 1
                                cleanup_stats['space_freed_mb'] += file_size / (1024 * 1024)
            
            # Rotate large log files
            self._rotate_large_logs()
            
            # Clean up Docker container logs
            cleanup_stats['docker_logs_cleaned'] = self._cleanup_docker_logs()
            
            if cleanup_stats['log_files_rotated'] > 0:
                self.logger.info(f"Log cleanup completed: {cleanup_stats['log_files_rotated']} files cleaned")
                self.stats['logs_cleaned'] += cleanup_stats['log_files_rotated']
            
        except Exception as e:
            self.logger.error(f"Log cleanup failed: {e}")
        
        return cleanup_stats
    
    def _rotate_large_logs(self):
        """Rotate log files that exceed size limits"""
        try:
            max_size_bytes = self.config.log_max_size_mb * 1024 * 1024
            
            for log_dir in self.logs_dir.iterdir():
                if log_dir.is_dir():
                    for log_file in log_dir.glob("*.log"):
                        if log_file.stat().st_size > max_size_bytes:
                            # Rotate the log file
                            rotated_name = f"{log_file}.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                            log_file.rename(log_file.parent / rotated_name)
                            
                            # Create new empty log file
                            log_file.touch()
                            
                            self.logger.info(f"Rotated large log file: {log_file}")
                            
        except Exception as e:
            self.logger.error(f"Log rotation failed: {e}")
    
    def _cleanup_docker_logs(self) -> int:
        """Clean up Docker container logs"""
        cleaned_count = 0
        
        try:
            # Use docker system prune to clean up logs
            result = subprocess.run([
                'docker', 'system', 'prune', '-f', '--filter', 'until=24h'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                cleaned_count = 1
                self.logger.info("Docker system cleanup completed")
            else:
                self.logger.warning(f"Docker cleanup warning: {result.stderr}")
                
        except Exception as e:
            self.logger.error(f"Docker log cleanup failed: {e}")
        
        return cleaned_count
    
    def backup_database(self) -> bool:
        """Create database backup"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = self.backup_dir / f"postgres_backup_{timestamp}.sql"
            
            # Ensure backup directory exists
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Create PostgreSQL backup using docker exec
            backup_cmd = [
                'docker', 'exec', 'postgres',
                'pg_dumpall', '-U', 'postgres'
            ]
            
            with open(backup_file, 'w') as f:
                result = subprocess.run(backup_cmd, stdout=f, stderr=subprocess.PIPE, text=True)
            
            if result.returncode == 0:
                self.logger.info(f"Database backup created: {backup_file}")
                self.stats['db_backups_created'] += 1
                
                # Clean up old backups
                self._cleanup_old_backups()
                return True
            else:
                self.logger.error(f"Database backup failed: {result.stderr}")
                backup_file.unlink(missing_ok=True)
                return False
                
        except Exception as e:
            self.logger.error(f"Database backup error: {e}")
            return False
    
    def _cleanup_old_backups(self):
        """Remove old database backups"""
        try:
            cutoff_time = time.time() - (self.config.db_backup_max_age_days * 24 * 3600)
            
            for backup_file in self.backup_dir.glob("postgres_backup_*.sql"):
                if backup_file.stat().st_mtime < cutoff_time:
                    backup_file.unlink()
                    self.logger.info(f"Removed old backup: {backup_file.name}")
                    
        except Exception as e:
            self.logger.error(f"Backup cleanup error: {e}")
    
    def vacuum_database(self) -> bool:
        """Perform database vacuum operation"""
        try:
            vacuum_cmd = [
                'docker', 'exec', 'postgres',
                'psql', '-U', 'postgres', '-c', 'VACUUM ANALYZE;'
            ]
            
            result = subprocess.run(vacuum_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info("Database vacuum completed")
                self.last_db_vacuum_time = datetime.now()
                return True
            else:
                self.logger.error(f"Database vacuum failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Database vacuum error: {e}")
            return False
    
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
            if self.live_dir.exists():
                image_files = list(self.live_dir.glob("*.jpg"))
                image_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                
                for image_file in image_files[25:]:  # Remove all but 25 newest
                    file_size = image_file.stat().st_size
                    image_file.unlink()
                    emergency_stats['images_removed'] += 1
                    emergency_stats['space_freed_mb'] += file_size / (1024 * 1024)
                    
                    # Remove corresponding metadata
                    metadata_file = self.metadata_dir / f"{image_file.name}.json"
                    if metadata_file.exists():
                        metadata_file.unlink()
            
            # Remove all processed images
            if self.processed_dir.exists():
                for processed_file in self.processed_dir.glob("*.jpg"):
                    file_size = processed_file.stat().st_size
                    processed_file.unlink()
                    emergency_stats['images_removed'] += 1
                    emergency_stats['space_freed_mb'] += file_size / (1024 * 1024)
            
            # Keep only 5 most recent snapshots
            if self.snapshots_dir.exists():
                snapshot_files = list(self.snapshots_dir.glob("*.jpg"))
                snapshot_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                
                for snapshot_file in snapshot_files[5:]:
                    file_size = snapshot_file.stat().st_size
                    snapshot_file.unlink()
                    emergency_stats['images_removed'] += 1
                    emergency_stats['space_freed_mb'] += file_size / (1024 * 1024)
            
            # Clean up temporary files
            temp_dirs = ["/tmp", "/var/tmp", str(self.ssd_path / "tmp")]
            for temp_dir in temp_dirs:
                temp_path = Path(temp_dir)
                if temp_path.exists():
                    for temp_file in temp_path.glob("*"):
                        if temp_file.is_file() and temp_file.stat().st_mtime < (time.time() - 3600):
                            try:
                                file_size = temp_file.stat().st_size
                                temp_file.unlink()
                                emergency_stats['temp_files_removed'] += 1
                                emergency_stats['space_freed_mb'] += file_size / (1024 * 1024)
                            except (OSError, PermissionError) as e:
                                self.logger.debug(f"Could not remove temp file {temp_file}: {e}")
                                pass  # Skip files we can't remove
            
            # Force Docker cleanup
            subprocess.run(['docker', 'system', 'prune', '-af'], capture_output=True)
            
            total_removed = emergency_stats['images_removed'] + emergency_stats['temp_files_removed']
            self.logger.warning(f"Emergency cleanup completed: {total_removed} files removed, "
                              f"{emergency_stats['space_freed_mb']:.1f} MB freed")
            
        except Exception as e:
            self.logger.error(f"Emergency cleanup failed: {e}")
        
        return emergency_stats
    
    def check_storage_health(self) -> Dict[str, any]:
        """Check storage health and return status"""
        health_status = {
            'storage_usage': self.get_storage_usage(),
            'needs_cleanup': False,
            'needs_emergency_cleanup': False,
            'warnings': [],
            'recommendations': []
        }
        
        try:
            storage = health_status['storage_usage']
            
            # Check SSD usage
            if 'ssd' in storage and 'used_percent' in storage['ssd']:
                ssd_usage = storage['ssd']['used_percent']
                
                if ssd_usage > (100 - self.config.storage_critical_threshold_percent):
                    health_status['needs_emergency_cleanup'] = True
                    health_status['warnings'].append(f"SSD critically low: {ssd_usage:.1f}% used")
                elif ssd_usage > (100 - self.config.storage_warning_threshold_percent):
                    health_status['needs_cleanup'] = True
                    health_status['warnings'].append(f"SSD running low: {ssd_usage:.1f}% used")
            
            # Check SD card usage
            if 'sd' in storage and 'used_percent' in storage['sd']:
                sd_usage = storage['sd']['used_percent']
                
                if sd_usage > 90:
                    health_status['warnings'].append(f"SD card high usage: {sd_usage:.1f}% used")
                    health_status['recommendations'].append("Consider moving more data to SSD")
            
            # Count files in camera directories
            if self.live_dir.exists():
                live_count = len(list(self.live_dir.glob("*.jpg")))
                if live_count > 500:
                    health_status['needs_cleanup'] = True
                    health_status['warnings'].append(f"Many live images: {live_count} files")
            
        except Exception as e:
            health_status['warnings'].append(f"Health check error: {e}")
        
        return health_status
    
    def get_status_report(self) -> Dict[str, any]:
        """Generate comprehensive status report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'config': {
                'cleanup_frequency_hours': self.config.cleanup_frequency_hours,
                'image_max_age_hours': self.config.image_max_age_hours,
                'log_max_age_days': self.config.log_max_age_days
            },
            'statistics': self.stats.copy(),
            'storage_health': self.check_storage_health(),
            'last_operations': {
                'last_cleanup': self.stats.get('last_cleanup'),
                'last_db_vacuum': self.last_db_vacuum_time.isoformat()
            }
        }
        
        # Add file counts
        try:
            report['file_counts'] = {
                'live_images': len(list(self.live_dir.glob("*.jpg"))) if self.live_dir.exists() else 0,
                'processed_images': len(list(self.processed_dir.glob("*.jpg"))) if self.processed_dir.exists() else 0,
                'snapshots': len(list(self.snapshots_dir.glob("*.jpg"))) if self.snapshots_dir.exists() else 0,
                'metadata_files': len(list(self.metadata_dir.glob("*.json"))) if self.metadata_dir.exists() else 0
            }
        except Exception as e:
            report['file_counts'] = {'error': str(e)}
        
        return report
    
    def run_maintenance_cycle(self):
        """Run a complete maintenance cycle"""
        self.logger.info("Starting maintenance cycle")
        cycle_start = time.time()
        
        try:
            # Check storage health first
            health = self.check_storage_health()
            
            if health['needs_emergency_cleanup']:
                self.emergency_cleanup()
            elif health['needs_cleanup']:
                self.cleanup_images()
                self.cleanup_logs()
            
            # Regular scheduled maintenance
            now = datetime.now()
            
            # Image cleanup (every cycle)
            if (now - self.last_cleanup_time).total_seconds() >= (self.config.cleanup_frequency_hours * 3600):
                self.cleanup_images()
                self.cleanup_logs()
                self.last_cleanup_time = now
                self.stats['last_cleanup'] = now.isoformat()
            
            # Database vacuum (weekly)
            if (now - self.last_db_vacuum_time).total_seconds() >= (self.config.db_vacuum_frequency_hours * 3600):
                self.vacuum_database()
            
            # Database backup (daily)
            if now.hour == 2 and now.minute < 10:  # Around 2 AM
                self.backup_database()
            
        except Exception as e:
            self.logger.error(f"Maintenance cycle failed: {e}")
        
        cycle_duration = time.time() - cycle_start
        self.logger.info(f"Maintenance cycle completed in {cycle_duration:.1f} seconds")
    
    def start_daemon(self):
        """Start the maintenance daemon"""
        self.logger.info("Starting data maintenance daemon")
        self.running = True
        
        def maintenance_loop():
            while self.running:
                try:
                    self.run_maintenance_cycle()
                    # Sleep for monitoring frequency
                    time.sleep(self.config.monitoring_frequency_minutes * 60)
                except Exception as e:
                    self.logger.error(f"Maintenance loop error: {e}")
                    time.sleep(300)  # Sleep 5 minutes on error
        
        # Start maintenance loop in background thread
        maintenance_thread = threading.Thread(target=maintenance_loop, daemon=True)
        maintenance_thread.start()
        
        try:
            # Keep main thread alive
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal")
            self.stop_daemon()
    
    def stop_daemon(self):
        """Stop the maintenance daemon"""
        self.logger.info("Stopping data maintenance daemon")
        self.running = False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Data File Maintenance Manager')
    parser.add_argument('--config', '-c', default='config/maintenance.conf',
                       help='Configuration file path')
    parser.add_argument('--daemon', '-d', action='store_true',
                       help='Run as daemon')
    parser.add_argument('--cleanup', action='store_true',
                       help='Run cleanup cycle once')
    parser.add_argument('--emergency-cleanup', action='store_true',
                       help='Run emergency cleanup')
    parser.add_argument('--status', '-s', action='store_true',
                       help='Show status report')
    parser.add_argument('--backup-db', action='store_true',
                       help='Create database backup')
    parser.add_argument('--vacuum-db', action='store_true',
                       help='Vacuum database')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    # Load configuration
    config = MaintenanceConfig.load_from_file(args.config)
    
    # Set up logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create maintenance manager
    manager = DataMaintenanceManager(config)
    
    try:
        if args.daemon:
            manager.start_daemon()
        elif args.emergency_cleanup:
            stats = manager.emergency_cleanup()
            print(f"Emergency cleanup completed: {json.dumps(stats, indent=2)}")
        elif args.cleanup:
            manager.run_maintenance_cycle()
            print("Maintenance cycle completed")
        elif args.status:
            report = manager.get_status_report()
            print(json.dumps(report, indent=2))
        elif args.backup_db:
            success = manager.backup_database()
            print(f"Database backup: {'success' if success else 'failed'}")
        elif args.vacuum_db:
            success = manager.vacuum_database()
            print(f"Database vacuum: {'success' if success else 'failed'}")
        else:
            parser.print_help()
            return 1
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())