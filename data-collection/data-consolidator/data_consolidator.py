#!/usr/bin/env python3
"""
Data Consolidator Service
Consolidates data from multiple edge processing services for storage and analysis
"""

import sys
import time
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ConsolidatedRecord:
    """Consolidated data record from multiple sources"""
    timestamp: float
    vehicle_detections: List[Dict] = None
    speed_measurements: List[Dict] = None
    fused_tracks: List[Dict] = None
    system_metrics: Dict = None

class DataConsolidator:
    """
    Consolidates data from multiple edge processing services
    Prepares data for storage and further analysis
    """
    
    def __init__(self):
        self.is_running = False
        self.consolidated_records = []
        
    def consolidate_data(self, vehicle_detections=None, speed_measurements=None, 
                        fused_tracks=None, system_metrics=None):
        """Consolidate data from multiple sources into a single record"""
        
        record = ConsolidatedRecord(
            timestamp=time.time(),
            vehicle_detections=vehicle_detections or [],
            speed_measurements=speed_measurements or [],
            fused_tracks=fused_tracks or [],
            system_metrics=system_metrics or {}
        )
        
        self.consolidated_records.append(record)
        logger.debug(f"Consolidated record created with {len(record.vehicle_detections)} detections, "
                    f"{len(record.speed_measurements)} speed measurements, "
                    f"{len(record.fused_tracks)} tracks")
        
        return record
    
    def get_consolidated_data(self, since_timestamp=None):
        """Get consolidated data since a specific timestamp"""
        if since_timestamp is None:
            return self.consolidated_records
        
        return [
            record for record in self.consolidated_records
            if record.timestamp >= since_timestamp
        ]
    
    def export_to_json(self, filename):
        """Export consolidated data to JSON file"""
        try:
            data = []
            for record in self.consolidated_records:
                data.append({
                    'timestamp': record.timestamp,
                    'vehicle_detections': record.vehicle_detections,
                    'speed_measurements': record.speed_measurements,
                    'fused_tracks': record.fused_tracks,
                    'system_metrics': record.system_metrics
                })
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Exported {len(data)} consolidated records to {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export data: {e}")
            return False

if __name__ == "__main__":
    # Test the data consolidator
    consolidator = DataConsolidator()
    
    # Mock some test data
    mock_detections = [
        {'id': 'det_1', 'type': 'car', 'confidence': 0.85}
    ]
    
    mock_speeds = [
        {'id': 'speed_1', 'speed_mps': 15.5, 'direction': 'approaching'}
    ]
    
    mock_tracks = [
        {'id': 'track_1', 'vehicle_type': 'car', 'speed': 15.5}
    ]
    
    mock_metrics = {
        'cpu_percent': 25.5,
        'memory_percent': 45.2,
        'temperature': 55.8
    }
    
    # Consolidate test data
    record = consolidator.consolidate_data(
        vehicle_detections=mock_detections,
        speed_measurements=mock_speeds,
        fused_tracks=mock_tracks,
        system_metrics=mock_metrics
    )
    
    print(f"Created consolidated record at {record.timestamp}")
    
    # Export to file
    consolidator.export_to_json("test_consolidated_data.json")
    
    print("Data consolidator test completed")