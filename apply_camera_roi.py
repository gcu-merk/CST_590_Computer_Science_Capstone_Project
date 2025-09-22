#!/usr/bin/env python3
"""
Apply and Test Camera ROI Configuration

This script applies the ROI configuration to your live camera system
and provides testing tools to verify the detection zone is working correctly.
"""

import json
import sys
import time
import subprocess
from pathlib import Path

def apply_roi_to_capture_script(roi_config, capture_script_path):
    """Apply ROI configuration to the main capture script"""
    
    # Read the current capture script
    with open(capture_script_path, 'r') as f:
        content = f.read()
    
    # Find the ROI configuration section and update it
    roi_section_start = content.find('self.street_roi = street_roi or {')
    if roi_section_start == -1:
        print("Error: Could not find ROI configuration section in capture script")
        return False
    
    # Find the end of the ROI configuration
    roi_section_end = content.find('}', roi_section_start) + 1
    
    # Create the new ROI configuration string
    new_roi_config = f"""self.street_roi = street_roi or {{
            "x_start": {roi_config["x_start"]},  # {roi_config["x_start"]*100:.1f}% from left edge
            "x_end": {roi_config["x_end"]},    # {roi_config["x_end"]*100:.1f}% from left edge
            "y_start": {roi_config["y_start"]},   # {roi_config["y_start"]*100:.1f}% from top (exclude cross street)
            "y_end": {roi_config["y_end"]}      # {roi_config["y_end"]*100:.1f}% from top
        }}"""
    
    # Replace the old configuration with the new one
    new_content = content[:roi_section_start] + new_roi_config + content[roi_section_end:]
    
    # Create backup of original file
    backup_path = str(capture_script_path) + '.backup'
    with open(backup_path, 'w') as f:
        f.write(content)
    print(f"Backup created: {backup_path}")
    
    # Write the updated content
    with open(capture_script_path, 'w') as f:
        f.write(new_content)
    
    print(f"ROI configuration applied to: {capture_script_path}")
    return True

def restart_camera_service():
    """Restart the camera service to apply new configuration"""
    print("Restarting camera service to apply new ROI configuration...")
    
    commands = [
        "sudo systemctl stop imx500-ai-capture",
        "sleep 2",
        "sudo systemctl start imx500-ai-capture",
        "sleep 3",
        "sudo systemctl status imx500-ai-capture --no-pager"
    ]
    
    for cmd in commands:
        print(f"Running: {cmd}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0 and "status" not in cmd:
            print(f"Warning: Command failed: {result.stderr}")
        elif "status" in cmd:
            print(result.stdout)

def create_test_script():
    """Create a test script to verify ROI is working"""
    test_script_content = '''#!/usr/bin/env python3
"""
Test ROI Configuration

This script monitors the camera output to verify that:
1. Vehicles on the main street are detected
2. Cross street traffic is ignored
3. Detection zone boundaries are correct
"""

import time
import json
import redis
from pathlib import Path

def test_roi_configuration():
    """Test the current ROI configuration"""
    print("Testing ROI Configuration...")
    print("=" * 40)
    
    # Connect to Redis to monitor detections
    try:
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        r.ping()
        print("✓ Connected to Redis")
    except:
        print("✗ Could not connect to Redis")
        return
    
    print("\\nMonitoring vehicle detections for 60 seconds...")
    print("Drive a vehicle down the main street to test detection zone")
    print("\\nDetection Log:")
    print("-" * 60)
    
    start_time = time.time()
    detection_count = 0
    
    while time.time() - start_time < 60:
        try:
            # Check for new detection results
            result = r.get("latest_detection_result")
            if result:
                data = json.loads(result)
                
                if data.get("ai_detections"):
                    detection_count += 1
                    timestamp = data.get("timestamp", time.time())
                    detections = data["ai_detections"]
                    
                    print(f"[{time.strftime('%H:%M:%S', time.localtime(timestamp))}] "
                          f"Detected {len(detections)} vehicle(s):")
                    
                    for i, det in enumerate(detections):
                        bbox = det.get("bounding_box", {})
                        center_x = (bbox.get("x1", 0) + bbox.get("x2", 0)) // 2
                        center_y = (bbox.get("y1", 0) + bbox.get("y2", 0)) // 2
                        confidence = det.get("confidence", 0)
                        vehicle_type = det.get("vehicle_type", "unknown")
                        
                        print(f"  {i+1}. {vehicle_type} (conf: {confidence:.2f}) "
                              f"at center ({center_x}, {center_y})")
                
                # Clear the result to avoid duplicates
                r.delete("latest_detection_result")
        
        except Exception as e:
            print(f"Error reading detection data: {e}")
        
        time.sleep(0.5)
    
    print("-" * 60)
    print(f"Test completed. Total detections: {detection_count}")
    
    if detection_count == 0:
        print("\\n⚠️  No detections recorded. This could mean:")
        print("   - No vehicles passed through the detection zone")
        print("   - ROI is too restrictive")
        print("   - Camera service is not running")
        print("   - Try driving a vehicle down the main street")
    else:
        print(f"\\n✓ ROI configuration is working ({detection_count} detections)")

if __name__ == "__main__":
    test_roi_configuration()
'''
    
    test_script_path = Path("test_camera_roi.py")
    with open(test_script_path, 'w') as f:
        f.write(test_script_content)
    
    # Make executable
    test_script_path.chmod(0o755)
    print(f"Test script created: {test_script_path}")
    return test_script_path

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print(f"  {sys.argv[0]} <config_file.json>")
        print(f"  {sys.argv[0]} --test-only")
        print("")
        print("Examples:")
        print(f"  {sys.argv[0]} camera_roi_config.json")
        print(f"  {sys.argv[0]} --test-only")
        return
    
    if sys.argv[1] == "--test-only":
        test_script_path = create_test_script()
        print(f"\\nTo test your current ROI configuration, run:")
        print(f"  python3 {test_script_path}")
        return
    
    config_file = sys.argv[1]
    
    # Load ROI configuration
    try:
        with open(config_file, 'r') as f:
            config_data = json.load(f)
        roi_config = config_data["street_roi"]
        print(f"Loaded ROI configuration from: {config_file}")
    except Exception as e:
        print(f"Error loading configuration file: {e}")
        return
    
    # Find the main capture script
    script_paths = [
        "scripts/imx500_ai_host_capture.py",
        "imx500_ai_host_capture_enhanced.py",
        "main_edge_app_enhanced.py"
    ]
    
    capture_script_path = None
    for path in script_paths:
        if Path(path).exists():
            capture_script_path = Path(path)
            break
    
    if not capture_script_path:
        print("Error: Could not find camera capture script")
        print("Expected one of:", script_paths)
        return
    
    print(f"Using capture script: {capture_script_path}")
    
    # Apply the configuration
    print("\\nApplying ROI configuration...")
    if apply_roi_to_capture_script(roi_config, capture_script_path):
        print("✓ ROI configuration applied successfully")
        
        # Ask user if they want to restart the service
        response = input("\\nRestart camera service to apply changes? (y/N): ")
        if response.lower().startswith('y'):
            restart_camera_service()
        
        # Create test script
        test_script_path = create_test_script()
        print(f"\\n✓ Test script created: {test_script_path}")
        print("\\nNext steps:")
        print(f"1. Run: python3 {test_script_path}")
        print("2. Drive a vehicle down the main street during the test")
        print("3. Verify that main street traffic is detected")
        print("4. Verify that cross street traffic is ignored")
    else:
        print("✗ Failed to apply ROI configuration")

if __name__ == "__main__":
    main()