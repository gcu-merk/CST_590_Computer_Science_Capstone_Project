#!/usr/bin/env python3
"""
Legacy Speed Data Collection Module
This module is being migrated to the new edge_processing structure.
For the main speed analysis service, see: edge_processing/speed_analysis/speed_analysis_service.py
"""

import sys
from pathlib import Path

# Add new edge processing module to path
sys.path.append(str(Path(__file__).parent.parent.parent / "edge_processing"))

# Import the new speed analysis service
try:
    from speed_analysis.speed_analysis_service import SpeedAnalysisService, OPS243CRadar
    
    # Provide backward compatibility
    def create_speed_collection_service(radar_port='/dev/ttyACM0'):
        """Create speed collection service (backward compatibility)"""
        return SpeedAnalysisService(radar_port)
    
    # Legacy function names for compatibility
    def start_speed_collection(radar_port='/dev/ttyACM0'):
        """Start speed collection (legacy interface)"""
        service = SpeedAnalysisService(radar_port)
        return service.start_analysis()
    
except ImportError as e:
    print(f"Warning: Could not import new speed analysis service: {e}")
    print("Please ensure the edge_processing modules are properly installed.")
    
    # Fallback placeholder implementation
    def create_speed_collection_service(radar_port='/dev/ttyACM0'):
        print("Using placeholder speed collection service")
        return None
    
    def start_speed_collection(radar_port='/dev/ttyACM0'):
        print("Using placeholder speed collection function")
        return False

if __name__ == "__main__":
    print("Speed Data Collection - Legacy Interface")
    print("Redirecting to new edge_processing service...")
    
    try:
        service = create_speed_collection_service()
        if service and service.start_analysis():
            print("Speed analysis service started successfully")
            import time
            time.sleep(30)  # Run for 30 seconds
            service.stop_analysis()
        else:
            print("Failed to start speed analysis service")
    except Exception as e:
        print(f"Error: {e}")