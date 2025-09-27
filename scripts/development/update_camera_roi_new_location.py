#!/usr/bin/env python3
"""
Update Camera ROI Environment Variables for New Location

This script updates the IMX500 camera service environment variables
to use the new ROI configuration for the green area monitoring.
"""

import json
import subprocess
import sys

def load_new_roi_config():
    """Load the new ROI configuration"""
    try:
        with open('/mnt/storage/new_location_roi_config.json', 'r') as f:
            config = json.load(f)
        return config['street_roi']
    except Exception as e:
        print(f"❌ Error loading ROI config: {e}")
        return None

def update_systemd_environment(roi_config):
    """Update the systemd service environment variables"""
    
    env_updates = [
        f"STREET_ROI_X_START={roi_config['x_start']}",
        f"STREET_ROI_X_END={roi_config['x_end']}",
        f"STREET_ROI_Y_START={roi_config['y_start']}",
        f"STREET_ROI_Y_END={roi_config['y_end']}"
    ]
    
    print("🔧 Updating IMX500 service environment variables...")
    print("=" * 50)
    
    for env_var in env_updates:
        print(f"Setting: {env_var}")
    
    # Create environment file for systemd service
    env_file_content = "\n".join(env_updates) + "\n"
    
    try:
        with open('/tmp/imx500-env-update', 'w') as f:
            f.write(env_file_content)
        
        # Update the systemd service environment
        subprocess.run([
            'sudo', 'mkdir', '-p', '/etc/systemd/system/imx500-ai-capture.service.d/'
        ], check=True)
        
        override_content = f"""[Service]
{env_file_content.replace('=', '=')}
Environment={' '.join(env_updates)}
"""
        
        with open('/tmp/imx500-override.conf', 'w') as f:
            f.write(override_content)
        
        subprocess.run([
            'sudo', 'cp', '/tmp/imx500-override.conf', 
            '/etc/systemd/system/imx500-ai-capture.service.d/override.conf'
        ], check=True)
        
        print("✅ Environment variables updated successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error updating environment: {e}")
        return False

def restart_camera_service():
    """Restart the camera service to apply new ROI"""
    print("\n🔄 Restarting camera service...")
    
    try:
        # Reload systemd configuration
        subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=True)
        
        # Restart the service
        subprocess.run(['sudo', 'systemctl', 'restart', 'imx500-ai-capture'], check=True)
        
        print("✅ Camera service restarted with new ROI configuration!")
        return True
        
    except Exception as e:
        print(f"❌ Error restarting service: {e}")
        return False

def verify_new_config():
    """Verify the new configuration is applied"""
    print("\n🔍 Verifying new ROI configuration...")
    
    try:
        result = subprocess.run([
            'sudo', 'systemctl', 'show', 'imx500-ai-capture', 
            '--property=Environment'
        ], capture_output=True, text=True, check=True)
        
        print("Current service environment:")
        print(result.stdout)
        
        # Check service status
        status_result = subprocess.run([
            'sudo', 'systemctl', 'status', 'imx500-ai-capture', '--no-pager'
        ], capture_output=True, text=True)
        
        if "active (running)" in status_result.stdout:
            print("✅ Service is running with new configuration!")
        else:
            print("⚠️ Service status:")
            print(status_result.stdout)
        
    except Exception as e:
        print(f"❌ Error verifying config: {e}")

def main():
    """Main update function"""
    print("🚀 UPDATING CAMERA ROI FOR NEW LOCATION")
    print("=" * 60)
    
    # Load new ROI configuration
    roi_config = load_new_roi_config()
    if not roi_config:
        sys.exit(1)
    
    print("📐 New ROI Configuration:")
    print(f"   X-axis: {roi_config['x_start']*100:.0f}% to {roi_config['x_end']*100:.0f}%")
    print(f"   Y-axis: {roi_config['y_start']*100:.0f}% to {roi_config['y_end']*100:.0f}%")
    print("   Focus: Green area on left side of image")
    print("   Excludes: Right side parking lot, sky, ground edges")
    print()
    
    # Update environment variables
    if not update_systemd_environment(roi_config):
        sys.exit(1)
    
    # Restart service
    if not restart_camera_service():
        sys.exit(1)
    
    # Verify configuration
    verify_new_config()
    
    print("\n🎯 ROI UPDATE COMPLETE!")
    print("Camera is now monitoring the green area of interest.")

if __name__ == "__main__":
    main()