#!/usr/bin/env python3
"""
Standalone image processor for the hybrid traffic monitoring solution.
Processes captured images using the vehicle detection service.

Usage:
    python3 process_traffic.py /path/to/image.jpg
    python3 process_traffic.py /shared/traffic_image.jpg --output /shared/processed/
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# Add app directory to Python path
sys.path.insert(0, '/app')

try:
    import cv2
    import numpy as np
    from edge_processing.vehicle_detection.vehicle_detection_service import VehicleDetectionService
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this from within the Docker container")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_image(image_path, output_dir=None, save_annotated=True):
    """
    Process a single image file for vehicle detection
    
    Args:
        image_path: Path to input image
        output_dir: Directory to save processed images (optional)
        save_annotated: Whether to save annotated image
    
    Returns:
        dict: Processing results
    """
    try:
        # Validate input
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        # Load image
        logger.info(f"Loading image: {image_path}")
        frame = cv2.imread(image_path)
        
        if frame is None:
            raise ValueError(f"Failed to load image: {image_path}")
        
        logger.info(f"Image loaded successfully: {frame.shape}")
        
        # Initialize vehicle detection service
        service = VehicleDetectionService()
        
        # Convert BGR to RGB for processing
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Run vehicle detection
        logger.info("Running vehicle detection...")
        vehicles = service.detect_vehicles(frame_rgb)
        
        # Prepare results
        results = {
            'image_path': image_path,
            'image_shape': frame.shape,
            'vehicles_detected': len(vehicles),
            'vehicles': []
        }
        
        # Process detection results
        for i, vehicle in enumerate(vehicles):
            vehicle_info = {
                'id': i,
                'confidence': vehicle.confidence,
                'vehicle_type': vehicle.vehicle_type,
                'bbox': vehicle.bbox,
                'timestamp': vehicle.timestamp
            }
            results['vehicles'].append(vehicle_info)
        
        logger.info(f"Detection complete: {len(vehicles)} vehicles found")
        
        # Save annotated image if requested
        if save_annotated and vehicles:
            if output_dir is None:
                # Save in same directory as input
                output_dir = os.path.dirname(image_path)
            
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate output filename
            input_name = Path(image_path).stem
            output_path = os.path.join(output_dir, f"{input_name}_processed.jpg")
            
            # Annotate and save
            annotated_frame = service.annotate_frame(frame_rgb, vehicles)
            annotated_bgr = cv2.cvtColor(annotated_frame, cv2.COLOR_RGB2BGR)
            
            cv2.imwrite(output_path, annotated_bgr)
            logger.info(f"Annotated image saved: {output_path}")
            results['annotated_path'] = output_path
        
        # Print summary
        print(f"✅ Processing complete:")
        print(f"   Input: {image_path}")
        print(f"   Size: {frame.shape}")
        print(f"   Vehicles detected: {len(vehicles)}")
        
        if vehicles:
            print(f"   Vehicle details:")
            for vehicle in vehicles:
                print(f"     - {vehicle.vehicle_type} (confidence: {vehicle.confidence:.2f})")
        
        return results
        
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        print(f"❌ Processing failed: {e}")
        return None

def main():
    """Main entry point for standalone image processing"""
    parser = argparse.ArgumentParser(description='Process traffic images for vehicle detection')
    parser.add_argument('image_path', help='Path to input image')
    parser.add_argument('--output', '-o', help='Output directory for processed images')
    parser.add_argument('--no-annotate', action='store_true', help='Skip saving annotated image')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Process the image
    results = process_image(
        image_path=args.image_path,
        output_dir=args.output,
        save_annotated=not args.no_annotate
    )
    
    if results is None:
        sys.exit(1)
    
    # Return success
    sys.exit(0)

if __name__ == "__main__":
    main()
