#!/usr/bin/env python3
"""
Quick test of the data maintenance system
"""

import sys
import os
import json
from pathlib import Path

# Add the project directory to the path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

try:
    # Import the maintenance system
    from scripts.data_maintenance_manager import DataMaintenanceManager, MaintenanceConfig
    
    # Load configuration
    config_file = project_dir / "config" / "maintenance.conf"
    config = MaintenanceConfig.load_from_file(str(config_file))
    
    # Create manager
    manager = DataMaintenanceManager(config)
    
    # Get status report
    print("=== Data Maintenance System Status ===")
    report = manager.get_status_report()
    print(json.dumps(report, indent=2))
    
except Exception as e:
    print(f"Error testing maintenance system: {e}")
    import traceback
    traceback.print_exc()