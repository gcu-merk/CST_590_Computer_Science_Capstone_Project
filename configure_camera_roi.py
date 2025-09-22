#!/usr/bin/env python3
"""
Configure Camera ROI (Region of Interest) for Traffic Monitoring

This script helps configure the detection zone for the AI camera to:
1. Focus on the main street traffic
2. Exclude the cross street at the top of the image
3. Filter out parked cars in driveways/side areas

Current baseline: No cars parked on street (good for establishing detection zone)
"""

import json
import argparse
from pathlib import Path

def get_current_roi_config():
    """Get the current ROI configuration from the main capture script"""
    # Default values from imx500_ai_host_capture.py
    current_config = {
        "x_start": 0.15,  # 15% from left edge
        "x_end": 0.85,    # 85% from left edge (center 70%)
        "y_start": 0.5,   # 50% from top (exclude cross street at top)
        "y_end": 0.9      # 90% from top (exclude sky, include main street only)
    }
    return current_config

def suggest_optimized_roi():
    """Suggest optimized ROI based on street layout description"""
    # Based on user description:
    # - Cross street at top of image to exclude
    # - Main street traffic to capture
    # - No parked cars currently (good baseline)
    
    suggested_configs = {
        "conservative": {
            "description": "Conservative approach - focus on center main street only",
            "config": {
                "x_start": 0.2,   # 20% from left (narrow focus)
                "x_end": 0.8,     # 80% from right
                "y_start": 0.45,  # 45% from top (exclude cross street)
                "y_end": 0.85     # 85% from top (exclude bottom edge)
            }
        },
        "moderate": {
            "description": "Moderate approach - capture most of main street",
            "config": {
                "x_start": 0.1,   # 10% from left (wider coverage)
                "x_end": 0.9,     # 90% from right
                "y_start": 0.4,   # 40% from top (exclude cross street)
                "y_end": 0.9      # 90% from top
            }
        },
        "aggressive": {
            "description": "Aggressive approach - maximum main street coverage",
            "config": {
                "x_start": 0.05,  # 5% from left (full width coverage)
                "x_end": 0.95,    # 95% from right
                "y_start": 0.35,  # 35% from top (minimal cross street exclusion)
                "y_end": 0.95     # 95% from top
            }
        }
    }
    
    return suggested_configs

def create_roi_config_file(config, output_path):
    """Create a configuration file for the ROI settings"""
    config_data = {
        "street_roi": config,
        "description": "Camera ROI configuration for traffic monitoring",
        "timestamp": "2025-09-22",
        "notes": [
            "x_start/x_end: Horizontal boundaries (0.0 = left edge, 1.0 = right edge)",
            "y_start/y_end: Vertical boundaries (0.0 = top edge, 1.0 = bottom edge)",
            "Configured to exclude cross street at top of image",
            "Focus on main street traffic only"
        ]
    }
    
    with open(output_path, 'w') as f:
        json.dump(config_data, f, indent=2)
    
    print(f"ROI configuration saved to: {output_path}")

def visualize_roi(config, image_width=1920, image_height=1080):
    """Visualize the ROI boundaries in pixel coordinates"""
    x1 = int(config["x_start"] * image_width)
    x2 = int(config["x_end"] * image_width)
    y1 = int(config["y_start"] * image_height)
    y2 = int(config["y_end"] * image_height)
    
    print(f"\nROI Visualization (for {image_width}x{image_height} image):")
    print(f"Detection Zone:")
    print(f"  Top-left corner:     ({x1}, {y1})")
    print(f"  Bottom-right corner: ({x2}, {y2})")
    print(f"  Width:  {x2-x1} pixels ({((x2-x1)/image_width)*100:.1f}% of image)")
    print(f"  Height: {y2-y1} pixels ({((y2-y1)/image_height)*100:.1f}% of image)")
    print(f"\nExcluded Areas:")
    print(f"  Top area (cross street): 0 to {y1} pixels ({(y1/image_height)*100:.1f}% from top)")
    print(f"  Left area: 0 to {x1} pixels ({(x1/image_width)*100:.1f}% from left)")
    print(f"  Right area: {x2} to {image_width} pixels ({((image_width-x2)/image_width)*100:.1f}% from right)")
    print(f"  Bottom area: {y2} to {image_height} pixels ({((image_height-y2)/image_height)*100:.1f}% from bottom)")

def main():
    parser = argparse.ArgumentParser(description="Configure Camera ROI for Traffic Monitoring")
    parser.add_argument("--show-current", action="store_true", help="Show current ROI configuration")
    parser.add_argument("--show-suggestions", action="store_true", help="Show suggested ROI configurations")
    parser.add_argument("--preset", choices=["conservative", "moderate", "aggressive"], 
                       help="Apply a preset configuration")
    parser.add_argument("--custom", nargs=4, type=float, metavar=("X_START", "X_END", "Y_START", "Y_END"),
                       help="Set custom ROI values (0.0-1.0)")
    parser.add_argument("--output", default="camera_roi_config.json", help="Output configuration file")
    parser.add_argument("--visualize", action="store_true", help="Show pixel coordinates for ROI")
    
    args = parser.parse_args()
    
    if args.show_current:
        current = get_current_roi_config()
        print("Current ROI Configuration:")
        print(json.dumps(current, indent=2))
        if args.visualize:
            visualize_roi(current)
    
    if args.show_suggestions:
        suggestions = suggest_optimized_roi()
        print("\nSuggested ROI Configurations:")
        for name, preset in suggestions.items():
            print(f"\n{name.upper()}:")
            print(f"  Description: {preset['description']}")
            print(f"  Configuration:")
            for key, value in preset['config'].items():
                print(f"    {key}: {value}")
            if args.visualize:
                print(f"  Pixel boundaries:")
                visualize_roi(preset['config'])
    
    if args.preset:
        suggestions = suggest_optimized_roi()
        if args.preset in suggestions:
            config = suggestions[args.preset]['config']
            print(f"\nApplying {args.preset} preset:")
            print(json.dumps(config, indent=2))
            create_roi_config_file(config, args.output)
            if args.visualize:
                visualize_roi(config)
    
    if args.custom:
        x_start, x_end, y_start, y_end = args.custom
        if not all(0.0 <= val <= 1.0 for val in [x_start, x_end, y_start, y_end]):
            print("Error: All ROI values must be between 0.0 and 1.0")
            return
        if x_start >= x_end or y_start >= y_end:
            print("Error: Start values must be less than end values")
            return
        
        config = {
            "x_start": x_start,
            "x_end": x_end,
            "y_start": y_start,
            "y_end": y_end
        }
        print(f"\nApplying custom ROI configuration:")
        print(json.dumps(config, indent=2))
        create_roi_config_file(config, args.output)
        if args.visualize:
            visualize_roi(config)

if __name__ == "__main__":
    print("Camera ROI Configuration Tool")
    print("=" * 40)
    main()