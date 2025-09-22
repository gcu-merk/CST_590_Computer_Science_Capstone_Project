#!/usr/bin/env python3
"""
Simple ROI Monitoring - Watch for Vehicle Detections in Real-Time
"""

import subprocess
import time
import re

def monitor_detections():
    print("🎯 ROI Detection Monitor - Red Shaded Area")
    print("=" * 50)
    print("Monitoring camera logs for vehicle detections...")
    print("Current ROI Configuration:")
    print("  - X: 12% to 88% (red area width)")
    print("  - Y: 42% to 88% (red area height)")
    print("  - Coverage: 76% × 46% of image")
    print()
    print("✅ Drive a vehicle through the RED SHADED AREA to test detection")
    print("❌ Cross street traffic should be IGNORED")
    print()
    print("Press Ctrl+C to stop monitoring...")
    print("-" * 50)
    
    last_detection_time = 0
    detection_count = 0
    
    try:
        while True:
            # Get recent logs
            result = subprocess.run([
                'sudo', 'journalctl', '-u', 'imx500-ai-capture', 
                '--since', '10 seconds ago', '--no-pager'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                
                for line in lines:
                    if 'INFO - ✅ IMX500 AI capture:' in line:
                        # Extract vehicle count from log line
                        match = re.search(r'(\d+) vehicles', line)
                        if match:
                            vehicle_count = int(match.group(1))
                            timestamp_match = re.search(r'(\d{2}:\d{2}:\d{2})', line)
                            timestamp = timestamp_match.group(1) if timestamp_match else "unknown"
                            
                            if vehicle_count > 0:
                                detection_count += 1
                                print(f"🚗 [{timestamp}] DETECTION #{detection_count}: {vehicle_count} vehicle(s) in RED AREA!")
                                last_detection_time = time.time()
                            elif time.time() - last_detection_time > 30:  # Show "no vehicles" every 30 seconds
                                print(f"✨ [{timestamp}] Monitoring active - no vehicles in red area")
                                last_detection_time = time.time()
            
            time.sleep(2)
            
    except KeyboardInterrupt:
        print(f"\n\n📊 Monitoring Summary:")
        print(f"  Total detections: {detection_count}")
        if detection_count > 0:
            print("  ✅ ROI configuration is working - vehicles detected in red area!")
        else:
            print("  ℹ️  No vehicles detected (normal if no traffic passed through red area)")
        print("\nROI configuration test complete!")

if __name__ == "__main__":
    monitor_detections()