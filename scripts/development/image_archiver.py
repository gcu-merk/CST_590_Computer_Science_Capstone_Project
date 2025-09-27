#!/usr/bin/env python3
"""
Image Archival Service
Automatically organizes captured images into date-based folders and manages storage
"""

import os
import shutil
import time
import logging
import glob
from datetime import datetime, timedelta
from pathlib import Path
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ImageArchiver:
    """Organizes and archives captured images"""
    
    def __init__(self, 
                 source_dir='/mnt/storage/camera_capture/live',
                 archive_base='/mnt/storage/camera_capture/archived',
                 metadata_dir='/mnt/storage/camera_capture/metadata',
                 ai_results_dir='/mnt/storage/camera_capture/ai_results'):
        
        self.source_dir = Path(source_dir)
        self.archive_base = Path(archive_base)
        self.metadata_dir = Path(metadata_dir)
        self.ai_results_dir = Path(ai_results_dir)
        
        # Create directories if they don't exist
        self.archive_base.mkdir(exist_ok=True)
        
        self.stats = {
            'images_archived': 0,
            'vehicle_detections': 0,
            'bytes_processed': 0
        }
    
    def archive_images(self, age_minutes=30):
        """Archive images older than specified minutes"""
        logger.info(f"🗂️  Starting image archival (age > {age_minutes} minutes)")
        
        cutoff_time = time.time() - (age_minutes * 60)
        
        # Find images to archive
        image_pattern = self.source_dir / "capture_*.jpg"
        images = glob.glob(str(image_pattern))
        
        for image_path in images:
            try:
                # Check if image is old enough
                if os.path.getmtime(image_path) < cutoff_time:
                    self._archive_single_image(image_path)
            except Exception as e:
                logger.error(f"Error processing {image_path}: {e}")
        
        logger.info(f"✅ Archival complete: {self.stats['images_archived']} images, "
                   f"{self.stats['vehicle_detections']} with vehicles, "
                   f"{self.stats['bytes_processed'] / 1024 / 1024:.1f} MB")
    
    def _archive_single_image(self, image_path):
        """Archive a single image with metadata"""
        image_file = Path(image_path)
        
        # Extract date from filename: capture_20250922_151739_536.jpg
        try:
            filename = image_file.stem
            date_part = filename.split('_')[1]  # 20250922
            time_part = filename.split('_')[2]  # 151739
            
            # Create date-based directory structure
            year = date_part[:4]
            month = date_part[4:6]
            day = date_part[6:8]
            
            # Create archive directory: /archived/2025/09/22/
            archive_dir = self.archive_base / year / month / day
            archive_dir.mkdir(parents=True, exist_ok=True)
            
            # Check if there's corresponding AI detection data
            has_vehicles = self._check_vehicle_detection(filename)
            
            # Organize into subdirectories
            if has_vehicles:
                final_dir = archive_dir / "vehicle_detections"
                self.stats['vehicle_detections'] += 1
            else:
                final_dir = archive_dir / "no_vehicles"
            
            final_dir.mkdir(exist_ok=True)
            
            # Move the image
            destination = final_dir / image_file.name
            shutil.move(str(image_file), str(destination))
            
            # Update stats
            self.stats['images_archived'] += 1
            self.stats['bytes_processed'] += destination.stat().st_size
            
            logger.debug(f"📁 Archived: {image_file.name} -> {final_dir}")
            
        except Exception as e:
            logger.error(f"Failed to archive {image_path}: {e}")
    
    def _check_vehicle_detection(self, filename):
        """Check if image had vehicle detections"""
        # Look for corresponding metadata file
        metadata_pattern = self.metadata_dir / f"{filename}.json"
        ai_result_pattern = self.ai_results_dir / f"{filename}_results.json"
        
        # Check metadata directory for vehicle detection info
        if metadata_pattern.exists():
            try:
                import json
                with open(metadata_pattern) as f:
                    data = json.load(f)
                    return data.get('vehicles_detected', 0) > 0
            except Exception:
                pass
        
        # Check AI results directory
        if ai_result_pattern.exists():
            try:
                import json
                with open(ai_result_pattern) as f:
                    data = json.load(f)
                    return len(data.get('detections', [])) > 0
            except Exception:
                pass
        
        return False
    
    def cleanup_old_archives(self, days_to_keep=30):
        """Remove archived images older than specified days"""
        logger.info(f"🧹 Cleaning up archives older than {days_to_keep} days")
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        removed_count = 0
        
        # Walk through archive directory structure
        for year_dir in self.archive_base.iterdir():
            if not year_dir.is_dir():
                continue
                
            for month_dir in year_dir.iterdir():
                if not month_dir.is_dir():
                    continue
                    
                for day_dir in month_dir.iterdir():
                    if not day_dir.is_dir():
                        continue
                    
                    # Parse directory date
                    try:
                        dir_date = datetime.strptime(f"{year_dir.name}/{month_dir.name}/{day_dir.name}", "%Y/%m/%d")
                        
                        if dir_date < cutoff_date:
                            shutil.rmtree(day_dir)
                            removed_count += 1
                            logger.info(f"🗑️  Removed old archive: {dir_date.strftime('%Y-%m-%d')}")
                    except Exception as e:
                        logger.error(f"Error processing date directory {day_dir}: {e}")
        
        logger.info(f"✅ Cleanup complete: {removed_count} old archives removed")
    
    def get_storage_stats(self):
        """Get storage statistics"""
        try:
            # Get live directory stats
            live_files = list(self.source_dir.glob("*.jpg"))
            live_size = sum(f.stat().st_size for f in live_files if f.exists())
            
            # Get archive directory stats
            archive_files = list(self.archive_base.rglob("*.jpg"))
            archive_size = sum(f.stat().st_size for f in archive_files if f.exists())
            
            return {
                'live_images': len(live_files),
                'live_size_mb': live_size / 1024 / 1024,
                'archived_images': len(archive_files),
                'archived_size_mb': archive_size / 1024 / 1024,
                'total_size_mb': (live_size + archive_size) / 1024 / 1024
            }
        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            return {}

def main():
    parser = argparse.ArgumentParser(description='Archive captured images')
    parser.add_argument('--age-minutes', type=int, default=30, 
                       help='Archive images older than this many minutes (default: 30)')
    parser.add_argument('--cleanup-days', type=int, default=30,
                       help='Remove archives older than this many days (default: 30)')
    parser.add_argument('--stats-only', action='store_true',
                       help='Only show storage statistics')
    
    args = parser.parse_args()
    
    archiver = ImageArchiver()
    
    if args.stats_only:
        stats = archiver.get_storage_stats()
        print("📊 Storage Statistics:")
        print(f"Live Images: {stats.get('live_images', 0)} ({stats.get('live_size_mb', 0):.1f} MB)")
        print(f"Archived Images: {stats.get('archived_images', 0)} ({stats.get('archived_size_mb', 0):.1f} MB)")
        print(f"Total Storage: {stats.get('total_size_mb', 0):.1f} MB")
    else:
        # Archive old images
        archiver.archive_images(age_minutes=args.age_minutes)
        
        # Cleanup very old archives
        archiver.cleanup_old_archives(days_to_keep=args.cleanup_days)
        
        # Show final stats
        stats = archiver.get_storage_stats()
        logger.info(f"📊 Final stats: {stats.get('live_images', 0)} live, "
                   f"{stats.get('archived_images', 0)} archived, "
                   f"{stats.get('total_size_mb', 0):.1f} MB total")

if __name__ == '__main__':
    main()