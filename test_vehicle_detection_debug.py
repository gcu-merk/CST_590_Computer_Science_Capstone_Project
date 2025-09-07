#!/usr/bin/env python3
"""
Test script to verify vehicle detection service with debugging
"""
import sys
import os
import time
import logging

# Add the edge_processing directory to the path
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), 'edge_processing'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'edge_processing', 'vehicle_detection'))

try:
    from edge_processing.vehicle_detection.vehicle_detection_service import VehicleDetectionService
except ImportError:
    try:
        from vehicle_detection.vehicle_detection_service import VehicleDetectionService
    except ImportError:
        from vehicle_detection_service import VehicleDetectionService

def test_vehicle_detection_service():
    """Test the vehicle detection service with debugging enabled"""
    print("🧪 Testing Vehicle Detection Service with Debugging")
    print("=" * 60)

    # Configure logging to see debug messages
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create service instance with debugging enabled
    service = VehicleDetectionService(
        camera_index=0,
        periodic_snapshots=True,
        snapshot_interval_minutes=1,  # Test with 1 minute for faster feedback
        periodic_snapshot_path="/tmp/test_snapshots",
        use_imx500_ai=False,  # Disable IMX500 for testing
        suppress_camera_warning=False
    )

    print("✅ Service created successfully")
    print(f"📁 Snapshot path: {service.periodic_snapshot_path}")
    print(f"⏰ Snapshot interval: {service.snapshot_interval_minutes} minutes")

    # Start the service
    print("\n🚀 Starting vehicle detection service...")
    success = service.start_detection()

    if success:
        print("✅ Service started successfully")
        print("🔄 Service should be running in background...")
        print("⏳ Waiting 30 seconds to see if snapshots are created...")

        # Wait and check for snapshots
        time.sleep(30)

        # Check if snapshots were created
        if os.path.exists(service.periodic_snapshot_path):
            snapshots = [f for f in os.listdir(service.periodic_snapshot_path)
                        if f.startswith('periodic_snapshot_') and f.endswith('.jpg')]
            print(f"📸 Found {len(snapshots)} snapshots:")
            for snap in snapshots:
                print(f"  - {snap}")
        else:
            print("❌ No snapshot directory found")

        # Stop the service
        print("\n🛑 Stopping service...")
        service.stop_detection()
        print("✅ Service stopped")

    else:
        print("❌ Failed to start service")

if __name__ == "__main__":
    test_vehicle_detection_service()
