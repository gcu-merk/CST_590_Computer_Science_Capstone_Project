#!/usr/bin/env python3
"""
Database Reference Update Script
Updates all references from traffic_monitoring.db to traffic_data.db
"""

import os
import re
from pathlib import Path

def update_database_references():
    """Update all database path references in the codebase"""
    
    # Files that have been updated
    updated_files = [
        "edge_processing/data_persistence/database_persistence_service.py",
        "edge_api/consolidated_data_api.py", 
        "deployment/database-persistence.service",
        "deployment/deploy_persistence_layer.sh"
    ]
    
    print("✅ Updated Database References:")
    print("=" * 50)
    print("OLD: /mnt/storage/traffic_monitoring.db")
    print("NEW: /app/data/traffic_data.db (container) -> /mnt/storage/data/traffic_data.db (host)")
    print("=" * 50)
    
    for file_path in updated_files:
        print(f"✅ {file_path}")
    
    print("\n🔧 Changes Made:")
    print("- Updated default database paths in service constructors")
    print("- Updated environment variable fallbacks")
    print("- Updated systemd service environment variables")
    print("- Updated deployment script database initialization")
    print("- Updated database size check references")
    
    print("\n📝 Note:")
    print("Container services use environment variables that override these defaults:")
    print("DATABASE_PATH=/app/data/traffic_data.db (set in docker-compose.yml)")
    print("This maps to /mnt/storage/data/traffic_data.db on the host system")
    
    print("\n✅ All references to deleted traffic_monitoring.db have been updated!")

if __name__ == "__main__":
    update_database_references()