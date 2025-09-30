#!/usr/bin/env python3
"""
Create a test camera image for the traffic monitoring system
"""

from PIL import Image, ImageDraw, ImageFont
import os
from datetime import datetime

def create_test_image():
    # Create a test camera image
    img = Image.new('RGB', (1280, 720), color='lightblue')
    draw = ImageDraw.Draw(img)

    # Try to use a decent font
    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf', 72)
    except:
        try:
            font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 72)
        except:
            font = ImageFont.load_default()

    # Draw test content
    draw.text((50, 200), 'CAMERA TEST', fill='black', font=font)
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    draw.text((50, 300), f'Generated: {timestamp}', fill='darkblue', font=font)
    draw.text((50, 400), 'Traffic Monitoring System', fill='darkgreen', font=font)

    # Add a simple border
    draw.rectangle([10, 10, 1270, 710], outline='black', width=5)

    # Create the directory structure
    output_dir = '/mnt/storage/camera_capture/live'
    os.makedirs(output_dir, exist_ok=True)
    
    # Save the image
    output_path = os.path.join(output_dir, 'test_camera_snapshot.jpg')
    img.save(output_path, 'JPEG')
    print(f'Test image saved to: {output_path}')
    
    # Also create a backup in local data directory if it exists
    local_dir = '/home/pi/CST_590_Computer_Science_Capstone_Project/data/camera_capture/live'
    try:
        os.makedirs(local_dir, exist_ok=True)
        local_path = os.path.join(local_dir, 'test_camera_snapshot.jpg')
        img.save(local_path, 'JPEG')
        print(f'Backup image saved to: {local_path}')
    except Exception as e:
        print(f'Could not save backup: {e}')

if __name__ == '__main__':
    print("Creating test camera image...")
    create_test_image()
    print("Test image creation complete!")