#!/usr/bin/env python3
"""
Enhanced Data File Maintenance Service with Centralized Logging
Unified system for managing all data file cleanup, rotation, and maintenance
with full centralized logging and correlation tracking.
"""

import os
import sys
import json
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import shutil
import subprocess

# Add edge_processing to path for shared_logging
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import centralized logging infrastructure
try:
    from shared_logging import ServiceLogger, CorrelationContext
    CENTRALIZED_LOGGING_AVAILABLE = True
except ImportError:
    CENTRALIZED_LOGGING_AVAILABLE = False
    print("ERROR: Centralized logging not available - this is required for enhanced services")
    sys.exit(1)

# Redis for coordination
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("ERROR: Redis not available - this is required for enhanced services")
    sys.exit(1)


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
    def from_environment(cls) -> 'MaintenanceConfig':
        """Load configuration from environment variables"""
        return cls(
            image_max_age_hours=float(os.getenv('MAINTENANCE_IMAGE_MAX_AGE_HOURS', 24)),
            snapshot_max_age_hours=float(os.getenv('MAINTENANCE_SNAPSHOT_MAX_AGE_HOURS', 168)),
            emergency_cleanup_threshold_percent=float(os.getenv('MAINTENANCE_EMERGENCY_THRESHOLD', 10)),
            log_max_age_days=int(os.getenv('MAINTENANCE_LOG_MAX_AGE_DAYS', 30)),
            storage_warning_threshold_percent=float(os.getenv('MAINTENANCE_WARNING_THRESHOLD', 20)),
            ssd_base_path=os.getenv('STORAGE_ROOT', '/mnt/storage')
        )


class EnhancedDataMaintenanceService:
    """Enhanced data file maintenance service with centralized logging"""
    
    def __init__(self):
        # Initialize centralized logging
        self.logger = ServiceLogger(os.getenv('SERVICE_NAME', 'data_maintenance_service'))
        
        # Load configuration
        self.config = MaintenanceConfig.from_environment()
        
        # Initialize Redis connection
        self.redis_client = self._setup_redis()
        
        # Service state
        self.running = False
        self.last_cleanup_time = datetime.now()
        self.last_db_vacuum_time = datetime.now()
        
        # Storage paths
        self.ssd_path = Path(self.config.ssd_base_path)
        self.camera_path = self.ssd_path / "camera_capture"
        self.live_dir = self.camera_path / "live"
        self.processed_dir = self.camera_path / "processed"
        self.metadata_dir = self.camera_path / "metadata"
        self.snapshots_dir = self.ssd_path / "periodic_snapshots"
        self.ai_images_dir = self.ssd_path / "ai_camera_images"
        self.logs_dir = self.ssd_path / "logs"
        self.backup_dir = Path(self.config.backup_path)
        
        # Statistics tracking
        self.stats = {
            'last_cleanup': None,
            'images_cleaned': 0,
            'logs_cleaned': 0,
            'space_freed_mb': 0,
            'db_backups_created': 0,
            'emergency_cleanups': 0
        }
        
        self.logger.log_business_event("maintenance_service_initialized", {
            'ssd_path': str(self.ssd_path),
            'config': {
                'image_max_age_hours': self.config.image_max_age_hours,
                'log_max_age_days': self.config.log_max_age_days,
                'cleanup_frequency_hours': self.config.cleanup_frequency_hours
            }
        })

    def _setup_redis(self) -> redis.Redis:
        """Setup Redis connection"""
        try:
            redis_host = os.getenv('REDIS_HOST', 'localhost')
            redis_port = int(os.getenv('REDIS_PORT', 6379))
            
            client = redis.Redis(
                host=redis_host,
                port=redis_port,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # Test connection
            client.ping()
            
            self.logger.log_business_event("redis_connected", {
                'host': redis_host,
                'port': redis_port
            })
            
            return client
            
        except Exception as e:
            self.logger.log_error("Failed to connect to Redis", error=str(e))
            raise

    def get_storage_usage(self, path: Path) -> Dict[str, float]:
        """Get storage usage statistics for a path"""
        try:
            with CorrelationContext(self.logger, "storage_usage_check"):
                stat = shutil.disk_usage(path)
                total_gb = stat.total / (1024**3)
                used_gb = (stat.total - stat.free) / (1024**3)
                free_gb = stat.free / (1024**3)
                usage_percent = (used_gb / total_gb) * 100
                
                usage_stats = {
                    'total_gb': round(total_gb, 2),
                    'used_gb': round(used_gb, 2),
                    'free_gb': round(free_gb, 2),
                    'usage_percent': round(usage_percent, 2)
                }
                
                self.logger.log_performance_metric("storage_usage", usage_stats)
                return usage_stats
                
        except Exception as e:
            self.logger.log_error(f"Failed to get storage usage for {path}", error=str(e))
            return {}

    def cleanup_old_images(self) -> int:
        """Clean up old images and return number of files cleaned"""
        files_cleaned = 0
        space_freed = 0
        
        try:
            with CorrelationContext(self.logger, "image_cleanup"):
                cutoff_time = datetime.now() - timedelta(hours=self.config.image_max_age_hours)
                
                # Cleanup directories
                cleanup_dirs = [
                    (self.live_dir, "live_images"),
                    (self.processed_dir, "processed_images"),
                    (self.ai_images_dir, "ai_images"),
                    (self.snapshots_dir, "snapshots")
                ]
                
                for cleanup_dir, dir_type in cleanup_dirs:
                    if cleanup_dir.exists():
                        for file_path in cleanup_dir.rglob("*"):
                            if file_path.is_file():
                                try:
                                    file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                                    if file_mtime < cutoff_time:
                                        file_size = file_path.stat().st_size
                                        file_path.unlink()
                                        files_cleaned += 1
                                        space_freed += file_size
                                        
                                        self.logger.log_business_event("file_cleaned", {
                                            'file_path': str(file_path),
                                            'dir_type': dir_type,
                                            'file_age_hours': (datetime.now() - file_mtime).total_seconds() / 3600,
                                            'file_size_bytes': file_size
                                        })
                                        
                                except Exception as e:
                                    self.logger.log_error(f"Failed to cleanup file {file_path}", error=str(e))
                
                space_freed_mb = space_freed / (1024 * 1024)
                
                self.logger.log_business_event("image_cleanup_completed", {
                    'files_cleaned': files_cleaned,
                    'space_freed_mb': round(space_freed_mb, 2),
                    'cutoff_hours': self.config.image_max_age_hours
                })
                
                # Update stats
                self.stats['images_cleaned'] += files_cleaned
                self.stats['space_freed_mb'] += space_freed_mb
                
                return files_cleaned
                
        except Exception as e:
            self.logger.log_error("Image cleanup failed", error=str(e))
            return 0

    def cleanup_old_logs(self) -> int:
        """Clean up old log files and return number of files cleaned"""
        files_cleaned = 0
        
        try:
            with CorrelationContext(self.logger, "log_cleanup"):
                cutoff_time = datetime.now() - timedelta(days=self.config.log_max_age_days)
                
                if self.logs_dir.exists():
                    for log_file in self.logs_dir.rglob("*.log"):
                        try:
                            file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                            if file_mtime < cutoff_time:
                                log_size = log_file.stat().st_size
                                log_file.unlink()
                                files_cleaned += 1
                                
                                self.logger.log_business_event("log_file_cleaned", {
                                    'log_file': str(log_file),
                                    'file_age_days': (datetime.now() - file_mtime).days,
                                    'file_size_bytes': log_size
                                })
                                
                        except Exception as e:
                            self.logger.log_error(f"Failed to cleanup log file {log_file}", error=str(e))
                
                self.logger.log_business_event("log_cleanup_completed", {
                    'files_cleaned': files_cleaned,
                    'cutoff_days': self.config.log_max_age_days
                })
                
                self.stats['logs_cleaned'] += files_cleaned
                return files_cleaned
                
        except Exception as e:
            self.logger.log_error("Log cleanup failed", error=str(e))
            return 0

    def emergency_cleanup(self) -> bool:
        """Perform emergency cleanup when storage is critically low"""
        try:
            with CorrelationContext(self.logger, "emergency_cleanup"):
                self.logger.log_business_event("emergency_cleanup_started", {
                    'trigger': 'low_storage_space'
                })
                
                # More aggressive cleanup - reduce age thresholds
                original_image_age = self.config.image_max_age_hours
                original_log_age = self.config.log_max_age_days
                
                # Reduce thresholds for emergency cleanup
                self.config.image_max_age_hours = max(1, original_image_age * 0.5)
                self.config.log_max_age_days = max(1, original_log_age * 0.5)
                
                # Perform cleanup
                images_cleaned = self.cleanup_old_images()
                logs_cleaned = self.cleanup_old_logs()
                
                # Restore original thresholds
                self.config.image_max_age_hours = original_image_age
                self.config.log_max_age_days = original_log_age
                
                self.logger.log_business_event("emergency_cleanup_completed", {
                    'images_cleaned': images_cleaned,
                    'logs_cleaned': logs_cleaned,
                    'total_cleaned': images_cleaned + logs_cleaned
                })
                
                self.stats['emergency_cleanups'] += 1
                return True
                
        except Exception as e:
            self.logger.log_error("Emergency cleanup failed", error=str(e))
            return False

    def run_maintenance_cycle(self):
        """Run a single maintenance cycle"""
        try:
            with CorrelationContext(self.logger, "maintenance_cycle"):
                self.logger.log_business_event("maintenance_cycle_started", {})
                
                # Check storage usage
                storage_stats = self.get_storage_usage(self.ssd_path)
                
                # Store stats in Redis for monitoring
                if self.redis_client and storage_stats:
                    self.redis_client.hset(
                        "maintenance:storage_stats",
                        mapping={
                            "usage_percent": storage_stats.get('usage_percent', 0),
                            "free_gb": storage_stats.get('free_gb', 0),
                            "last_check": datetime.now().isoformat(),
                            **self.stats
                        }
                    )
                
                # Check if emergency cleanup is needed
                usage_percent = storage_stats.get('usage_percent', 0)
                if usage_percent >= (100 - self.config.emergency_cleanup_threshold_percent):
                    self.logger.log_business_event("emergency_cleanup_triggered", {
                        'usage_percent': usage_percent,
                        'threshold': self.config.emergency_cleanup_threshold_percent
                    })
                    self.emergency_cleanup()
                else:
                    # Regular cleanup
                    images_cleaned = self.cleanup_old_images()
                    logs_cleaned = self.cleanup_old_logs()
                    
                    self.logger.log_business_event("regular_cleanup_completed", {
                        'images_cleaned': images_cleaned,
                        'logs_cleaned': logs_cleaned
                    })
                
                self.last_cleanup_time = datetime.now()
                self.stats['last_cleanup'] = self.last_cleanup_time.isoformat()
                
                self.logger.log_business_event("maintenance_cycle_completed", {
                    'storage_usage_percent': usage_percent,
                    'stats': self.stats
                })
                
        except Exception as e:
            import traceback
            print(f"MAINTENANCE CYCLE ERROR: {str(e)}")
            print(f"ERROR TYPE: {type(e).__name__}")
            print(f"TRACEBACK: {traceback.format_exc()}")
            print(f"SSD PATH: {str(self.ssd_path) if hasattr(self, 'ssd_path') else 'Not set'}")
            
            self.logger.log_error(
                f"Maintenance cycle failed: {str(e)} (Type: {type(e).__name__})",
                error=str(e),
                error_type=type(e).__name__
            )

    def run(self):
        """Main service loop"""
        self.running = True
        
        self.logger.log_business_event("maintenance_service_started", {
            'config': {
                'cleanup_frequency_hours': self.config.cleanup_frequency_hours,
                'image_max_age_hours': self.config.image_max_age_hours,
                'log_max_age_days': self.config.log_max_age_days
            }
        })
        
        try:
            while self.running:
                # Run maintenance cycle
                self.run_maintenance_cycle()
                
                # Sleep until next cycle
                sleep_seconds = self.config.cleanup_frequency_hours * 3600
                self.logger.log_performance_metric("maintenance_sleep", {
                    'sleep_duration_seconds': sleep_seconds,
                    'next_run_time': (datetime.now() + timedelta(seconds=sleep_seconds)).isoformat()
                })
                
                time.sleep(sleep_seconds)
                
        except KeyboardInterrupt:
            self.logger.log_business_event("maintenance_service_stopping", {
                'reason': 'keyboard_interrupt'
            })
        except Exception as e:
            self.logger.log_error("Maintenance service crashed", error=str(e))
            raise
        finally:
            self.running = False
            self.logger.log_business_event("maintenance_service_stopped", {
                'final_stats': self.stats
            })

    def stop(self):
        """Stop the maintenance service"""
        self.running = False


def main():
    """Main entry point for enhanced data maintenance service"""
    print("Starting Enhanced Data Maintenance Service with Centralized Logging...")
    
    # Verify centralized logging is available
    if not CENTRALIZED_LOGGING_AVAILABLE:
        print("ERROR: Centralized logging is required but not available")
        sys.exit(1)
    
    # Create and run service
    service = EnhancedDataMaintenanceService()
    
    try:
        service.run()
    except KeyboardInterrupt:
        print("Shutting down maintenance service...")
        service.stop()
    except Exception as e:
        print(f"Maintenance service failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()