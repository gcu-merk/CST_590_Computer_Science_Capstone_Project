#!/usr/bin/env python3
"""
SD Card Backup Service
Automatically creates compressed backups of the SD card to the SSD
"""

import os
import subprocess
import logging
import time
from datetime import datetime
from pathlib import Path
import schedule

# Configuration
BACKUP_DIR = os.getenv('BACKUP_DIR', '/mnt/backups')
SD_DEVICE = os.getenv('SD_DEVICE', '/dev/mmcblk0')
MAX_BACKUPS = int(os.getenv('MAX_BACKUPS', '3'))
BACKUP_SCHEDULE = os.getenv('BACKUP_SCHEDULE', '02:00')  # Default: 2 AM daily
COMPRESSION_LEVEL = int(os.getenv('COMPRESSION_LEVEL', '6'))  # 1-9, lower is faster

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('sd-backup')


def get_disk_usage(path):
    """Get disk usage statistics"""
    stat = os.statvfs(path)
    free = stat.f_bavail * stat.f_frsize
    total = stat.f_blocks * stat.f_frsize
    used = (stat.f_blocks - stat.f_bfree) * stat.f_frsize
    return {
        'total': total,
        'used': used,
        'free': free,
        'percent': (used / total) * 100
    }


def check_backup_space():
    """Check if there's enough space for backup"""
    try:
        # Get SD card size
        result = subprocess.run(
            ['blockdev', '--getsize64', SD_DEVICE],
            capture_output=True,
            text=True,
            check=True
        )
        sd_size = int(result.stdout.strip())
        
        # Get backup directory space
        disk_usage = get_disk_usage(BACKUP_DIR)
        
        # Need at least 1.5x SD card size for compressed backup (safety margin)
        required_space = sd_size * 1.5
        
        if disk_usage['free'] < required_space:
            logger.error(f"Insufficient space: {disk_usage['free'] / (1024**3):.2f} GB free, "
                        f"need ~{required_space / (1024**3):.2f} GB")
            return False
        
        logger.info(f"Space check passed: {disk_usage['free'] / (1024**3):.2f} GB available")
        return True
        
    except Exception as e:
        logger.error(f"Error checking backup space: {e}")
        return False


def cleanup_old_backups():
    """Remove old backups keeping only MAX_BACKUPS most recent"""
    try:
        backup_path = Path(BACKUP_DIR)
        backup_files = sorted(
            backup_path.glob('pi5-sdcard-*.img.gz'),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        if len(backup_files) > MAX_BACKUPS:
            for old_backup in backup_files[MAX_BACKUPS:]:
                logger.info(f"Removing old backup: {old_backup.name}")
                old_backup.unlink()
                
    except Exception as e:
        logger.error(f"Error cleaning up old backups: {e}")


def create_backup():
    """Create a compressed backup of the SD card"""
    logger.info("=" * 60)
    logger.info("Starting SD card backup")
    logger.info("=" * 60)
    
    # Check if SD device exists
    if not os.path.exists(SD_DEVICE):
        logger.error(f"SD card device not found: {SD_DEVICE}")
        return False
    
    # Check space
    if not check_backup_space():
        logger.error("Insufficient space for backup")
        return False
    
    # Create backup directory
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    # Generate backup filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f"{BACKUP_DIR}/pi5-sdcard-{timestamp}.img.gz"
    
    logger.info(f"Backup file: {backup_file}")
    logger.info(f"Source device: {SD_DEVICE}")
    logger.info(f"Compression level: {COMPRESSION_LEVEL}")
    
    start_time = time.time()
    
    try:
        # Create the backup using dd and pigz
        logger.info("Creating backup... (this may take 30-60 minutes)")
        
        # dd command to read SD card
        dd_cmd = [
            'dd',
            f'if={SD_DEVICE}',
            'bs=4M',
            'status=progress'
        ]
        
        # pigz command for parallel compression
        pigz_cmd = [
            'pigz',
            f'-{COMPRESSION_LEVEL}',
            '-c'
        ]
        
        # Run dd | pigz > backup_file
        with open(backup_file, 'wb') as outfile:
            dd_process = subprocess.Popen(
                dd_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            pigz_process = subprocess.Popen(
                pigz_cmd,
                stdin=dd_process.stdout,
                stdout=outfile,
                stderr=subprocess.PIPE
            )
            
            # Allow dd_process to receive SIGPIPE if pigz_process exits
            dd_process.stdout.close()
            
            # Wait for completion
            pigz_stderr = pigz_process.communicate()[1]
            dd_return = dd_process.wait()
            
            if dd_return != 0:
                logger.error(f"dd command failed with return code {dd_return}")
                return False
            
            if pigz_process.returncode != 0:
                logger.error(f"pigz command failed: {pigz_stderr.decode()}")
                return False
        
        # Calculate duration and size
        duration = time.time() - start_time
        backup_size = os.path.getsize(backup_file)
        
        logger.info("=" * 60)
        logger.info("Backup completed successfully!")
        logger.info(f"Duration: {duration / 60:.2f} minutes")
        logger.info(f"Backup size: {backup_size / (1024**3):.2f} GB")
        logger.info(f"Location: {backup_file}")
        logger.info("=" * 60)
        
        # Cleanup old backups
        cleanup_old_backups()
        
        return True
        
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        # Remove incomplete backup file
        if os.path.exists(backup_file):
            try:
                os.remove(backup_file)
                logger.info("Removed incomplete backup file")
            except (OSError, PermissionError) as e:
                pass
        return False


def backup_job():
    """Scheduled backup job"""
    logger.info(f"Backup job triggered at {datetime.now()}")
    success = create_backup()
    
    if success:
        logger.info("Backup job completed successfully")
    else:
        logger.error("Backup job failed")


def main():
    """Main service loop"""
    logger.info("SD Card Backup Service starting...")
    logger.info(f"Backup directory: {BACKUP_DIR}")
    logger.info(f"SD device: {SD_DEVICE}")
    logger.info(f"Schedule: Daily at {BACKUP_SCHEDULE}")
    logger.info(f"Max backups to keep: {MAX_BACKUPS}")
    logger.info(f"Compression level: {COMPRESSION_LEVEL}")
    
    # Check if running with sufficient privileges
    if os.geteuid() != 0:
        logger.error("This service must run as root to access block devices")
        return
    
    # Check if pigz is available
    try:
        subprocess.run(['which', 'pigz'], check=True, capture_output=True)
        logger.info("pigz (parallel gzip) is available")
    except subprocess.CalledProcessError:
        logger.error("pigz not found. Please install: apt-get install pigz")
        return
    
    # Schedule the backup job
    schedule.every().day.at(BACKUP_SCHEDULE).do(backup_job)
    logger.info(f"Next backup scheduled for: {schedule.next_run()}")
    
    # Optional: Run backup immediately on startup if requested
    if os.getenv('RUN_ON_STARTUP', 'false').lower() == 'true':
        logger.info("Running backup on startup as requested")
        backup_job()
    
    # Run scheduled tasks
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("Service stopped by user")
    except Exception as e:
        logger.error(f"Service error: {e}")
        raise


if __name__ == '__main__':
    main()
