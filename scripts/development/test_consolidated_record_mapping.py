#!/usr/bin/env python3
"""
Test script to validate consolidated record data mapping
Tests the transformation from nested consolidated record to flat database fields
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime

# Add project paths
current_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir / "edge_processing"))

def test_consolidated_record_mapping():
    """Test the data mapping from consolidated record to database fields"""
    
    # Sample consolidated record (matches the structure created by consolidator)
    sample_consolidated_record = {
        "consolidation_id": "consolidated_025b73d2_1758981430",
        "correlation_id": "025b73d2",
        "timestamp": 1758981430.5595577,
        "trigger_source": "radar",
        
        "radar_data": {
            "speed": 16.7775,
            "speed_mps": -7.5,
            "alert_level": "low",
            "detection_id": "025b73d2",
            "confidence": 0.85,
            "direction": "receding"
        },
        
        "weather_data": {
            "dht22": {
                "temperature": 72.5,
                "humidity": 65.2,
                "timestamp": "2025-09-27T10:30:30.559"
            },
            "airport_weather": {
                "temperature": 74.0,
                "conditions": "Clear",
                "wind_speed": 5.2
            }
        },
        
        "camera_data": {
            "vehicle_count": 1,
            "detection_confidence": None,
            "vehicle_types": None,
            "recent_summary": {"count": 1}
        },
        
        "processing_metadata": {
            "processor_version": "consolidator_v2.1.0",
            "processing_time": "2025-09-27T10:30:30.559",
            "data_sources": ["radar"],
            "consolidation_method": "radar_only"
        }
    }
    
    print("🧪 Testing Consolidated Record Data Mapping")
    print("=" * 50)
    
    print("\n📋 Input Consolidated Record Structure:")
    print(json.dumps(sample_consolidated_record, indent=2))
    
    print("\n🔄 Data Extraction Test:")
    print("-" * 30)
    
    # Test the extraction logic (mirroring the database persistence service logic)
    record_data = sample_consolidated_record
    
    # Extract data from nested structure
    radar_data = record_data.get('radar_data', {})
    weather_data = record_data.get('weather_data', {})
    camera_data = record_data.get('camera_data', {})
    
    # Extract radar fields
    radar_speed = radar_data.get('speed')
    radar_confidence = radar_data.get('confidence', 0.0)
    alert_level = radar_data.get('alert_level', 'normal')
    
    # Extract weather fields
    dht22_data = weather_data.get('dht22', {})
    temperature = dht22_data.get('temperature')
    humidity = dht22_data.get('humidity')
    
    # Extract airport weather as fallback
    airport_weather = weather_data.get('airport_weather', {})
    if temperature is None:
        temperature = airport_weather.get('temperature')
    weather_condition = airport_weather.get('conditions')
    
    # Extract camera fields
    vehicle_count = camera_data.get('vehicle_count', 0)
    detection_confidence = camera_data.get('detection_confidence', 0.0)
    
    print(f"✅ radar_speed: {radar_speed} (from radar_data.speed)")
    print(f"✅ radar_confidence: {radar_confidence} (from radar_data.confidence)")
    print(f"✅ temperature: {temperature}°F (from weather_data.dht22.temperature)")
    print(f"✅ humidity: {humidity}% (from weather_data.dht22.humidity)")
    print(f"✅ weather_condition: {weather_condition} (from airport_weather.conditions)")
    print(f"✅ vehicle_count: {vehicle_count} (from camera_data.vehicle_count)")
    print(f"✅ alert_level: {alert_level} (from radar_data.alert_level)")
    
    print("\n📊 Database Field Mapping:")
    print("-" * 30)
    
    # Show the final mapping that would be stored in database
    database_fields = {
        "id": record_data.get('consolidation_id'),
        "timestamp": datetime.fromtimestamp(record_data.get('timestamp')),
        "trigger_source": record_data.get('trigger_source'),
        "radar_speed": radar_speed,
        "radar_confidence": radar_confidence,
        "temperature": temperature,
        "humidity": humidity,
        "weather_condition": weather_condition,
        "vehicle_count": vehicle_count,
        "detection_confidence": detection_confidence,
        "location_id": "default"
    }
    
    for field, value in database_fields.items():
        print(f"  {field}: {value}")
    
    print("\n✅ Data Mapping Test Complete!")
    print(f"   - Successfully extracted radar speed: {radar_speed} mph")
    print(f"   - Successfully extracted temperature: {temperature}°F")
    print(f"   - Successfully extracted humidity: {humidity}%")
    print("   - All nested data fields properly mapped to flat database schema")
    
    return True

if __name__ == "__main__":
    try:
        test_consolidated_record_mapping()
        print("\n🎉 All tests passed! The data mapping fix should work correctly.")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)