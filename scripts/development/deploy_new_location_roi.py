#!/usr/bin/env python3
"""
Deploy New Location ROI Configuration

This script applies the ROI configuration for the new sensor station location,
focusing on the green area of interest on the left side of the camera view.
"""

import json
import sys
from pathlib import Path

def load_new_roi_config():
    """Load the new location ROI configuration"""
    config_file = Path("new_location_roi_config.json")
    
    if not config_file.exists():
        print(f"❌ Configuration file not found: {config_file}")
        return None
    
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    return config

def display_roi_summary(config):
    """Display a summary of the new ROI configuration"""
    roi = config['street_roi']
    
    print("🎯 NEW ROI CONFIGURATION SUMMARY")
    print("=" * 50)
    print(f"📍 Location: {config.get('location', 'New sensor position')}")
    print(f"📅 Timestamp: {config.get('timestamp', 'Unknown')}")
    print()
    print("📐 DETECTION ZONE (Green Area):")
    print(f"   X-axis: {roi['x_start']*100:.0f}% to {roi['x_end']*100:.0f}% (Left side focus)")
    print(f"   Y-axis: {roi['y_start']*100:.0f}% to {roi['y_end']*100:.0f}% (Excluding sky/ground)")
    print()
    print("🚫 EXCLUSION ZONES:")
    if 'exclusions' in config:
        for zone_name, zone_config in config['exclusions'].items():
            print(f"   • {zone_name}: {zone_config['description']}")
    print()
    print("📝 CONFIGURATION NOTES:")
    for note in config.get('notes', []):
        print(f"   • {note}")
    print()

def create_deployment_command():
    """Create the deployment command for the new ROI"""
    return '''
# Deployment commands for new ROI configuration:

# 1. Copy configuration to Pi
scp new_location_roi_config.json merk@100.121.231.16:/mnt/storage/

# 2. Update the camera service with new ROI
ssh merk@100.121.231.16 "cd /mnt/storage && python3 -c \\"
import json
with open('new_location_roi_config.json', 'r') as f:
    config = json.load(f)
roi = config['street_roi']
print(f'New ROI: x_start={roi[\\\"x_start\\\"]}, x_end={roi[\\\"x_end\\\"]}, y_start={roi[\\\"y_start\\\"]}, y_end={roi[\\\"y_end\\\"]}')
\\"

# 3. Restart camera service to apply new ROI
ssh merk@100.121.231.16 "sudo systemctl restart imx500-ai-capture"
'''

def main():
    """Main deployment function"""
    print("🚀 DEPLOYING NEW LOCATION ROI CONFIGURATION")
    print("=" * 60)
    
    # Load configuration
    config = load_new_roi_config()
    if not config:
        sys.exit(1)
    
    # Display summary
    display_roi_summary(config)
    
    # Show deployment commands
    print("💻 DEPLOYMENT COMMANDS:")
    print(create_deployment_command())
    
    print("✅ Configuration file ready for deployment!")
    print("📋 Use the commands above to apply the new ROI to your Pi")

if __name__ == "__main__":
    main()