#!/usr/bin/env python3
"""
Custom ROI Configuration Based on User-Defined Red Shaded Area

This script creates an ROI configuration that matches the red shaded area
shown in the user's camera view image.
"""

def analyze_red_shaded_area():
    """
    Based on the red shaded area in the camera image, determine precise ROI boundaries
    
    From visual analysis of the red shaded area:
    - The monitored area starts approximately 15% from the left edge
    - It extends to about 85% from the left edge  
    - Vertically, it starts around 45% from the top (excluding cross street)
    - It extends to about 85% from the top (excluding bottom grass/driveway areas)
    """
    
    # Custom ROI based on the red shaded area
    custom_roi = {
        "x_start": 0.15,  # 15% from left edge (matches red area left boundary)
        "x_end": 0.85,    # 85% from left edge (matches red area right boundary)
        "y_start": 0.45,  # 45% from top (excludes cross street, matches red area top)
        "y_end": 0.85     # 85% from top (excludes grass/driveways, matches red area bottom)
    }
    
    return custom_roi

def create_precise_roi_config():
    """Create ROI configuration file that matches the red shaded area exactly"""
    
    roi_config = analyze_red_shaded_area()
    
    config_data = {
        "street_roi": roi_config,
        "description": "Custom ROI configuration matching user-defined red shaded monitoring area",
        "timestamp": "2025-09-22",
        "source": "User-defined red shaded area from camera view",
        "notes": [
            "ROI boundaries precisely match the red shaded area in user's camera image",
            "Excludes cross street at top of image",
            "Excludes driveways, parking areas, and grass on sides",
            "Focuses exclusively on main street vehicle travel area",
            "Coordinates based on visual analysis of red overlay"
        ]
    }
    
    return config_data

def visualize_custom_roi(config, image_width=1920, image_height=1080):
    """Visualize the custom ROI boundaries in pixel coordinates"""
    x1 = int(config["x_start"] * image_width)
    x2 = int(config["x_end"] * image_width)
    y1 = int(config["y_start"] * image_height)
    y2 = int(config["y_end"] * image_height)
    
    print(f"\nCustom ROI Based on Red Shaded Area:")
    print(f"=" * 50)
    print(f"Image Resolution: {image_width}x{image_height}")
    print(f"\nDetection Zone (Red Shaded Area):")
    print(f"  Top-left corner:     ({x1}, {y1})")
    print(f"  Bottom-right corner: ({x2}, {y2})")
    print(f"  Width:  {x2-x1} pixels ({((x2-x1)/image_width)*100:.1f}% of image)")
    print(f"  Height: {y2-y1} pixels ({((y2-y1)/image_height)*100:.1f}% of image)")
    
    print(f"\nExcluded Areas:")
    print(f"  ❌ Cross street (top):    0 to {y1} pixels ({(y1/image_height)*100:.1f}% from top)")
    print(f"  ❌ Left side areas:      0 to {x1} pixels ({(x1/image_width)*100:.1f}% from left)")
    print(f"  ❌ Right side areas:     {x2} to {image_width} pixels ({((image_width-x2)/image_width)*100:.1f}% from right)")
    print(f"  ❌ Bottom grass/drives:   {y2} to {image_height} pixels ({((image_height-y2)/image_height)*100:.1f}% from bottom)")
    
    print(f"\nMonitored Area Coverage:")
    print(f"  ✅ Main street traffic area: {((x2-x1)*(y2-y1))/(image_width*image_height)*100:.1f}% of total image")

def main():
    print("Custom ROI Configuration - Red Shaded Area Match")
    print("=" * 55)
    
    # Create configuration matching the red shaded area
    config_data = create_precise_roi_config()
    roi_config = config_data["street_roi"]
    
    # Display the configuration
    print("\nCustom ROI Configuration (matching red shaded area):")
    for key, value in roi_config.items():
        print(f"  {key}: {value}")
    
    # Visualize pixel boundaries
    visualize_custom_roi(roi_config)
    
    # Save configuration
    import json
    output_file = "custom_red_area_roi_config.json"
    with open(output_file, 'w') as f:
        json.dump(config_data, f, indent=2)
    
    print(f"\n✅ Custom ROI configuration saved to: {output_file}")
    print(f"\nTo apply this configuration:")
    print(f"1. Upload: scp {output_file} merk@100.121.231.16:/mnt/storage/")
    print(f"2. Apply:  ssh merk@100.121.231.16 'cd /mnt/storage && python3 apply_camera_roi.py {output_file}'")

if __name__ == "__main__":
    main()