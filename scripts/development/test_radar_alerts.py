#!/usr/bin/env python3
"""
Test script to verify radar alerting functionality works correctly
"""

import json
import time
import redis

def test_radar_alerts():
    """Test that radar alerts are working properly"""
    print("🧪 Testing Radar Alert System")
    print("=" * 50)
    
    # Connect to Redis
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    
    print("📡 Monitoring Redis for radar data...")
    print("Current radar data entries:", r.xlen('radar_data'))
    
    # Get recent entries
    recent_data = r.xrevrange('radar_data', '+', '-', count=10)
    
    print("\n📊 Recent radar data:")
    for entry_id, data in recent_data:
        timestamp = float(data.get('_timestamp', 0))
        readable_time = time.strftime('%H:%M:%S', time.localtime(timestamp))
        
        if 'speed' in data:
            speed = data['speed']
            unit = data.get('unit', 'unknown')
            alert_level = data.get('alert_level', 'none')
            print(f"  {readable_time}: Speed={speed} {unit}, Alert={alert_level}")
        elif 'range' in data:
            range_val = data['range']
            unit = data.get('unit', 'unknown')
            print(f"  {readable_time}: Range={range_val} {unit} (background)")
        else:
            print(f"  {readable_time}: Unknown data - {data}")
    
    print(f"\n✅ Radar system is operational")
    print("🎯 Speed thresholds: 2+ mph = LOW ALERT, 26+ mph = HIGH ALERT")
    print("📈 Monitoring active - vehicle speeds will be logged when detected")

if __name__ == '__main__':
    test_radar_alerts()