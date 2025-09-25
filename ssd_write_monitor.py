#!/usr/bin/env python3
"""
SSD Write Endurance Monitor
Tracks write operations to help monitor SSD lifespan
"""

import time
import subprocess
import json
from datetime import datetime

def get_disk_stats():
    """Get disk statistics from /proc/diskstats"""
    try:
        with open('/proc/diskstats', 'r') as f:
            for line in f:
                if 'sda1' in line:
                    parts = line.split()
                    return {
                        'device': parts[2],
                        'reads': int(parts[3]),
                        'sectors_read': int(parts[5]),
                        'writes': int(parts[7]),
                        'sectors_written': int(parts[9]),
                        'time_writing_ms': int(parts[10])
                    }
    except Exception as e:
        print(f"Error reading disk stats: {e}")
        return None

def bytes_to_human(bytes_val):
    """Convert bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.2f} PB"

def estimate_ssd_life(total_gb_written, ssd_capacity_gb=1800, rated_tbw=600):
    """
    Estimate SSD remaining life
    Samsung T7 Shield 2TB typically rated for ~600 TBW (Terabytes Written)
    """
    total_tb_written = total_gb_written / 1024
    percent_used = (total_tb_written / rated_tbw) * 100
    remaining_percent = max(0, 100 - percent_used)
    
    return {
        'total_tb_written': total_tb_written,
        'percent_used': percent_used,
        'remaining_percent': remaining_percent,
        'rated_tbw': rated_tbw
    }

def main():
    stats = get_disk_stats()
    if not stats:
        print("Could not read disk statistics")
        return
    
    # Convert sectors to bytes (512 bytes per sector)
    bytes_written = stats['sectors_written'] * 512
    gb_written = bytes_written / (1024**3)
    
    # Get SSD endurance estimate
    endurance = estimate_ssd_life(gb_written)
    
    print("=== SSD Write Endurance Monitor ===")
    print(f"Timestamp: {datetime.now()}")
    print(f"Device: {stats['device']}")
    print()
    print("=== Write Statistics ===")
    print(f"Total bytes written: {bytes_to_human(bytes_written)}")
    print(f"Total GB written: {gb_written:.2f} GB")
    print(f"Total write operations: {stats['writes']:,}")
    print(f"Average write size: {bytes_written / max(stats['writes'], 1) / 1024:.2f} KB")
    print()
    print("=== SSD Endurance Estimate ===")
    print(f"Total TB written: {endurance['total_tb_written']:.3f} TB")
    print(f"Rated endurance: {endurance['rated_tbw']} TBW")
    print(f"Endurance used: {endurance['percent_used']:.3f}%")
    print(f"Remaining life: {endurance['remaining_percent']:.1f}%")
    print()
    
    # Health assessment
    if endurance['percent_used'] < 10:
        health = "EXCELLENT"
    elif endurance['percent_used'] < 50:
        health = "GOOD"
    elif endurance['percent_used'] < 80:
        health = "FAIR"
    elif endurance['percent_used'] < 95:
        health = "CAUTION"
    else:
        health = "CRITICAL"
    
    print(f"SSD Health Status: {health}")
    
    # Save stats to log file
    log_data = {
        'timestamp': datetime.now().isoformat(),
        'stats': stats,
        'endurance': endurance,
        'health': health
    }
    
    try:
        with open('/mnt/storage/logs/ssd_endurance.log', 'a') as f:
            f.write(json.dumps(log_data) + '\n')
    except Exception as e:
        print(f"Could not write to log file: {e}")

if __name__ == '__main__':
    main()