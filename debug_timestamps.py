#!/usr/bin/env python3
"""Debug script to check timestamp issues in analytics API"""

from datetime import datetime, timedelta
import sqlite3

# Test timestamp calculations
now = datetime.now()
yesterday = now - timedelta(seconds=86400)

print(f"Current time: {now}")
print(f"24 hours ago: {yesterday}")
print(f"Current timestamp: {now.timestamp()}")
print(f"24h ago timestamp: {yesterday.timestamp()}")

# Test database connection and query
try:
    conn = sqlite3.connect('/app/data/traffic_data.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get latest timestamps from database
    cursor.execute("SELECT MAX(timestamp) as max_ts, MIN(timestamp) as min_ts FROM traffic_detections")
    result = cursor.fetchone()
    print(f"\nDatabase timestamp range:")
    print(f"Latest: {result['max_ts']} ({datetime.fromtimestamp(result['max_ts'])})")
    print(f"Earliest: {result['min_ts']} ({datetime.fromtimestamp(result['min_ts'])})")
    
    # Test our query
    cursor.execute("""
        SELECT COUNT(*) as count, 
               MAX(r.speed_mph) as max_speed,
               MIN(r.speed_mph) as min_speed
        FROM traffic_detections t 
        JOIN radar_detections r ON t.id = r.detection_id 
        WHERE t.timestamp BETWEEN ? AND ?
    """, [yesterday.timestamp(), now.timestamp()])
    
    result = cursor.fetchone()
    print(f"\nQuery results for last 24h:")
    print(f"Count: {result['count']}")
    print(f"Max speed: {result['max_speed']}")  
    print(f"Min speed: {result['min_speed']}")
    
    # Get a few recent samples
    cursor.execute("""
        SELECT t.timestamp, r.speed_mph, r.alert_level
        FROM traffic_detections t 
        JOIN radar_detections r ON t.id = r.detection_id 
        WHERE t.timestamp BETWEEN ? AND ?
        ORDER BY t.timestamp DESC LIMIT 5
    """, [yesterday.timestamp(), now.timestamp()])
    
    print(f"\nRecent speed samples:")
    for row in cursor.fetchall():
        print(f"  {datetime.fromtimestamp(row['timestamp'])}: {row['speed_mph']} mph ({row['alert_level']})")
        
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")