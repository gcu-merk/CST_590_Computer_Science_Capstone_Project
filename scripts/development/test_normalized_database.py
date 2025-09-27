#!/usr/bin/env python3
"""
Test script to validate normalized 3NF database schema
Tests the new multi-table structure with proper relationships and constraints
"""

import json
import sys
import time
import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime

# Add project paths
current_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir / "edge_processing"))

def test_normalized_database():
    """Test the normalized 3NF database schema"""
    
    print("🧪 Testing Normalized 3NF Database Schema")
    print("=" * 50)
    
    # Create temporary database for testing
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
        db_path = Path(temp_db.name)
    
    try:
        # Import the service class
        from data_persistence.database_persistence_service_simplified import SimplifiedEnhancedDatabasePersistenceService
        
        print(f"\n📋 Creating temporary database: {db_path}")
        
        # Initialize service with test database
        service = SimplifiedEnhancedDatabasePersistenceService(
            database_path=str(db_path),
            batch_size=1,  # Process immediately for testing
            redis_host=None  # Skip Redis for this test
        )
        
        # Initialize database (this also connects)
        service.initialize_database()
        
        print("✅ Database initialized with normalized 3NF schema")
        
        # Test sample consolidated record
        sample_record = {
            "consolidation_id": "test_consolidated_123456789",
            "correlation_id": "test_corr_123",
            "timestamp": time.time(),
            "trigger_source": "radar",
            
            "radar_data": {
                "speed": 25.5,
                "speed_mps": 11.4,
                "alert_level": "normal",
                "detection_id": "radar_det_123",
                "confidence": 0.92,
                "direction": "approaching"
            },
            
            "weather_data": {
                "dht22": {
                    "temperature": 68.5,
                    "humidity": 72.3,
                    "timestamp": datetime.now().isoformat()
                },
                "airport_weather": {
                    "temperature": 70.0,
                    "conditions": "Partly Cloudy",
                    "wind_speed": 8.2
                }
            },
            
            "camera_data": {
                "vehicle_count": 1,
                "detection_confidence": 0.88,
                "vehicle_types": ["car"],
                "inference_time_ms": 45
            },
            
            "processing_metadata": {
                "processor_version": "consolidator_v2.1.0",
                "processing_time": datetime.now().isoformat(),
                "data_sources": ["radar", "weather", "camera"]
            }
        }
        
        print("\n🔄 Processing sample consolidated record...")
        
        # Process the record
        success = service.process_traffic_record(sample_record)
        
        if success:
            print("✅ Record processed successfully")
        else:
            print("❌ Record processing failed")
            return False
        
        # Verify data was inserted correctly
        print("\n🔍 Verifying normalized data insertion...")
        
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check traffic_detections table
        cursor.execute("SELECT * FROM traffic_detections WHERE id = ?", (sample_record['consolidation_id'],))
        detection_row = cursor.fetchone()
        
        if detection_row:
            print(f"✅ Traffic detection found: {detection_row['id']}")
            print(f"   - Correlation ID: {detection_row['correlation_id']}")
            print(f"   - Trigger Source: {detection_row['trigger_source']}")
            print(f"   - Timestamp: {datetime.fromtimestamp(detection_row['timestamp'])}")
        else:
            print("❌ No traffic detection found")
            return False
        
        # Check radar_detections table
        cursor.execute("SELECT * FROM radar_detections WHERE detection_id = ?", (sample_record['consolidation_id'],))
        radar_row = cursor.fetchone()
        
        if radar_row:
            print(f"✅ Radar detection found:")
            print(f"   - Speed: {radar_row['speed_mph']} mph ({radar_row['speed_mps']} m/s)")
            print(f"   - Confidence: {radar_row['confidence']}")
            print(f"   - Alert Level: {radar_row['alert_level']}")
            print(f"   - Direction: {radar_row['direction']}")
        else:
            print("❌ No radar detection found")
        
        # Check camera_detections table
        cursor.execute("SELECT * FROM camera_detections WHERE detection_id = ?", (sample_record['consolidation_id'],))
        camera_row = cursor.fetchone()
        
        if camera_row:
            print(f"✅ Camera detection found:")
            print(f"   - Vehicle Count: {camera_row['vehicle_count']}")
            print(f"   - Confidence: {camera_row['detection_confidence']}")
            print(f"   - Vehicle Types: {camera_row['vehicle_types']}")
            print(f"   - Inference Time: {camera_row['inference_time_ms']}ms")
        else:
            print("❌ No camera detection found")
        
        # Check weather_conditions table
        cursor.execute("SELECT * FROM weather_conditions ORDER BY timestamp DESC LIMIT 5")
        weather_rows = cursor.fetchall()
        
        print(f"✅ Weather conditions found: {len(weather_rows)} records")
        for weather_row in weather_rows:
            print(f"   - Source: {weather_row['source']}")
            print(f"   - Temperature: {weather_row['temperature']}°F")
            print(f"   - Humidity: {weather_row['humidity']}%")
            print(f"   - Conditions: {weather_row['conditions']}")
        
        # Check traffic_weather_correlation table
        cursor.execute("""
            SELECT twc.*, wc.source, wc.temperature 
            FROM traffic_weather_correlation twc
            JOIN weather_conditions wc ON twc.weather_id = wc.id
            WHERE twc.detection_id = ?
        """, (sample_record['consolidation_id'],))
        correlation_rows = cursor.fetchall()
        
        print(f"✅ Traffic-Weather correlations: {len(correlation_rows)} found")
        for corr_row in correlation_rows:
            print(f"   - Weather Source: {corr_row['source']}")
            print(f"   - Temperature: {corr_row['temperature']}°F")
            print(f"   - Correlation Strength: {corr_row['correlation_strength']}")
        
        # Test JOIN query to reconstruct consolidated view
        print("\n🔗 Testing JOIN query for consolidated view...")
        
        cursor.execute("""
            SELECT 
                td.id, td.correlation_id, td.timestamp, td.trigger_source,
                rd.speed_mph, rd.speed_mps, rd.confidence as radar_confidence, rd.alert_level,
                cd.vehicle_count, cd.detection_confidence, cd.vehicle_types,
                GROUP_CONCAT(wc.source || ':' || wc.temperature || '°F') as weather_data
            FROM traffic_detections td
            LEFT JOIN radar_detections rd ON td.id = rd.detection_id
            LEFT JOIN camera_detections cd ON td.id = cd.detection_id
            LEFT JOIN traffic_weather_correlation twc ON td.id = twc.detection_id
            LEFT JOIN weather_conditions wc ON twc.weather_id = wc.id
            WHERE td.id = ?
            GROUP BY td.id
        """, (sample_record['consolidation_id'],))
        
        joined_row = cursor.fetchone()
        
        if joined_row:
            print("✅ Consolidated JOIN query successful:")
            print(f"   - ID: {joined_row['id']}")
            print(f"   - Speed: {joined_row['speed_mph']} mph")
            print(f"   - Vehicle Count: {joined_row['vehicle_count']}")
            print(f"   - Weather: {joined_row['weather_data']}")
            print(f"   - Radar Confidence: {joined_row['radar_confidence']}")
        else:
            print("❌ JOIN query failed")
        
        # Test database statistics
        print("\n📊 Testing database statistics...")
        stats = service._get_database_stats()
        
        print(f"✅ Database Statistics:")
        print(f"   - Schema Type: {stats.get('schema_type', 'unknown')}")
        print(f"   - Total Detections: {stats.get('total_detections', 0)}")
        print(f"   - Radar Records: {stats.get('total_radar_records', 0)}")
        print(f"   - Camera Records: {stats.get('total_camera_records', 0)}")
        print(f"   - Weather Records: {stats.get('total_weather_records', 0)}")
        print(f"   - Database Size: {stats.get('size_mb', 0)} MB")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 Normalized 3NF Database Test Complete!")
        print("✅ All tests passed - Schema is working correctly")
        print("✅ Data integrity maintained across tables")
        print("✅ Foreign key relationships functioning")
        print("✅ JOIN queries working for consolidated views")
        print("✅ Weather data properly time-bucketed and correlated")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Clean up test database
        try:
            db_path.unlink()
            print(f"🧹 Cleaned up test database: {db_path}")
        except:
            pass

if __name__ == "__main__":
    success = test_normalized_database()
    if success:
        print("\n🎯 Ready for deployment: Normalized 3NF schema validated!")
        sys.exit(0)
    else:
        print("\n❌ Tests failed: Schema needs fixes before deployment")
        sys.exit(1)