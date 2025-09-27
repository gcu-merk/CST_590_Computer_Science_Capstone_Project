#!/usr/bin/env python3
"""
Update ROI configuration in IMX500 capture script
"""

import re

def update_roi_config():
    script_path = "imx500_ai_host_capture_updated.py"
    
    # Read the file
    with open(script_path, 'r') as f:
        content = f.read()
    
    # Define the new ROI configuration
    new_roi_block = '''        self.street_roi = street_roi or {
            "x_start": 0.1,   # 10% from left edge (wider coverage)
            "x_end": 0.9,     # 90% from left edge
            "y_start": 0.4,   # 40% from top (exclude cross street)
            "y_end": 0.9      # 90% from top (exclude sky, include main street only)
        }'''
    
    # Find and replace the ROI configuration block
    pattern = r'        self\.street_roi = street_roi or \{[^}]+\}'
    updated_content = re.sub(pattern, new_roi_block, content, flags=re.DOTALL)
    
    # Write the updated content
    with open(script_path, 'w') as f:
        f.write(updated_content)
    
    print(f"ROI configuration updated in {script_path}")
    
    # Verify the changes
    with open(script_path, 'r') as f:
        content = f.read()
    
    roi_match = re.search(r'self\.street_roi = street_roi or \{[^}]+\}', content, re.DOTALL)
    if roi_match:
        print("Updated ROI configuration:")
        print(roi_match.group())
    else:
        print("Warning: Could not find ROI configuration in updated file")

if __name__ == "__main__":
    update_roi_config()