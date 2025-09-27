#!/usr/bin/env python3
"""
Apply Precise Red Area ROI Configuration
"""

import re

def update_roi_to_red_area():
    script_path = "imx500_ai_host_capture_updated.py"
    
    # Read the file
    with open(script_path, 'r') as f:
        content = f.read()
    
    # Define the new ROI configuration to match red shaded area exactly
    new_roi_block = '''        self.street_roi = street_roi or {
            "x_start": 0.12,  # 12% from left edge (matches red area precisely)
            "x_end": 0.88,    # 88% from left edge (matches red area precisely)
            "y_start": 0.42,  # 42% from top (matches red area top boundary)
            "y_end": 0.88     # 88% from top (matches red area bottom boundary)
        }'''
    
    # Find and replace the ROI configuration block
    pattern = r'        self\.street_roi = street_roi or \{[^}]+\}'
    updated_content = re.sub(pattern, new_roi_block, content, flags=re.DOTALL)
    
    # Write the updated content
    with open(script_path, 'w') as f:
        f.write(updated_content)
    
    print(f"ROI configuration updated to match red shaded area exactly")
    
    # Verify the changes
    with open(script_path, 'r') as f:
        content = f.read()
    
    roi_match = re.search(r'self\.street_roi = street_roi or \{[^}]+\}', content, re.DOTALL)
    if roi_match:
        print("Updated ROI configuration (Red Area Match):")
        print(roi_match.group())
    else:
        print("Warning: Could not find ROI configuration in updated file")

if __name__ == "__main__":
    update_roi_to_red_area()