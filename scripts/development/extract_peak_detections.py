#!/usr/bin/env python3
"""
Extract Peak Vehicle Detection Images
Identifies and copies the largest detection files (peak vehicle captures) to a separate directory
"""

import os
import shutil
import glob
from datetime import datetime
from pathlib import Path

def log_msg(msg):
    """Log with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}")

def extract_peak_detections():
    """Extract the largest detection files to a separate directory"""
    
    # Configuration
    source_dir = "/mnt/storage/camera_capture/live"
    dest_dir = "/mnt/storage/camera_capture/peak_detections"
    size_threshold = 3450000  # 3.45MB threshold for "large" detections
    
    log_msg("🔍 Extracting Peak Vehicle Detection Images...")
    log_msg(f"Source: {source_dir}")
    log_msg(f"Destination: {dest_dir}")
    log_msg(f"Size threshold: {size_threshold/1024/1024:.1f} MB")
    
    # Create destination directory
    os.makedirs(dest_dir, exist_ok=True)
    
    # Find all image files
    image_patterns = ["*.jpg", "*.jpeg", "*.png"]
    all_images = []
    
    for pattern in image_patterns:
        all_images.extend(glob.glob(os.path.join(source_dir, pattern)))
    
    log_msg(f"📁 Found {len(all_images)} total images")
    
    # Analyze file sizes and identify peak detections
    peak_detections = []
    
    for image_path in all_images:
        try:
            file_size = os.path.getsize(image_path)
            if file_size >= size_threshold:
                file_info = {
                    'path': image_path,
                    'size': file_size,
                    'size_mb': file_size / 1024 / 1024,
                    'filename': os.path.basename(image_path)
                }
                peak_detections.append(file_info)
        except Exception as e:
            log_msg(f"⚠️  Error processing {image_path}: {e}")
    
    # Sort by file size (largest first)
    peak_detections.sort(key=lambda x: x['size'], reverse=True)
    
    log_msg(f"🎯 Found {len(peak_detections)} peak detection images")
    
    if not peak_detections:
        log_msg("❌ No peak detections found above threshold")
        return
    
    # Display top detections
    log_msg("\n📊 Top Peak Detections:")
    for i, detection in enumerate(peak_detections[:10], 1):
        log_msg(f"  {i:2d}. {detection['filename']:<35} - {detection['size_mb']:.2f} MB")
    
    # Copy peak detection files
    copied_count = 0
    for detection in peak_detections:
        try:
            source_path = detection['path']
            dest_path = os.path.join(dest_dir, detection['filename'])
            
            # Copy file with metadata preservation
            shutil.copy2(source_path, dest_path)
            copied_count += 1
            
            log_msg(f"✅ Copied: {detection['filename']} ({detection['size_mb']:.2f} MB)")
            
        except Exception as e:
            log_msg(f"❌ Error copying {detection['filename']}: {e}")
    
    log_msg(f"\n🎉 Successfully copied {copied_count} peak detection images")
    log_msg(f"📂 Peak detections saved to: {dest_dir}")
    
    # Create summary file
    summary_file = os.path.join(dest_dir, "peak_detections_summary.txt")
    with open(summary_file, 'w') as f:
        f.write("Peak Vehicle Detection Images Summary\n")
        f.write("=" * 50 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total peak detections: {len(peak_detections)}\n")
        f.write(f"Size threshold: {size_threshold/1024/1024:.1f} MB\n\n")
        
        f.write("Peak Detection Files (largest first):\n")
        f.write("-" * 50 + "\n")
        for i, detection in enumerate(peak_detections, 1):
            f.write(f"{i:3d}. {detection['filename']:<35} - {detection['size_mb']:.2f} MB\n")
    
    log_msg(f"📝 Summary saved to: peak_detections_summary.txt")

if __name__ == "__main__":
    extract_peak_detections()