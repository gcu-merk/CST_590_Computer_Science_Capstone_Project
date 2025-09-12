#!/usr/bin/env python3
"""
Comprehensive test script for sky condition analysis using Raspberry Pi camera
Supports live camera, static images, and batch testing
"""

import cv2
import sys
import os
import json
import time
import argparse
import numpy as np
from datetime import datetime
from pathlib import Path

# Add path for modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'edge_processing'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'edge_api'))

try:
    from weather_analysis.sky_analyzer import SkyAnalyzer
    from pi_system_status import PiSystemStatus
    MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Import error: {e}")
    print("Some modules not available. Creating mock implementations for testing...")
    MODULES_AVAILABLE = False

# Mock implementations for testing without full setup
class MockSkyAnalyzer:
    def analyze_sky_condition(self, image):
        return {
            'condition': 'clear',
            'confidence': 0.85,
            'timestamp': datetime.now().isoformat(),
            'analysis_methods': {
                'color': {'condition': 'clear', 'confidence': 0.85},
                'brightness': {'condition': 'clear', 'confidence': 0.80},
                'texture': {'condition': 'clear', 'confidence': 0.90}
            },
            'mock': True
        }
    
    def get_visibility_estimate(self, condition, confidence):
        return 'good' if condition == 'clear' else 'fair'

class MockPiSystemStatus:
    def get_enhanced_metrics(self, camera_image=None):
        return {
            'weather': {
                'sky_condition': {'condition': 'clear', 'confidence': 0.85},
                'timestamp': datetime.now().isoformat(),
                'mock': True
            }
        }

def test_sky_analysis_with_camera():
    """Test sky analysis using live camera feed with enhanced controls"""
    
    print("Initializing sky analyzer...")
    sky_analyzer = SkyAnalyzer() if MODULES_AVAILABLE else MockSkyAnalyzer()
    system_status = PiSystemStatus() if MODULES_AVAILABLE else MockPiSystemStatus()
    
    # Results storage
    analysis_history = []
    save_results = False
    
    # Initialize camera (adjust for your camera setup)
    try:
        # For Raspberry Pi Camera - try different camera indices
        cap = None
        for camera_id in [0, 1, 2]:
            cap = cv2.VideoCapture(camera_id)
            if cap.isOpened():
                print(f"Camera {camera_id} opened successfully")
                break
            cap.release()
        
        if cap is None or not cap.isOpened():
            print("Error: Could not open any camera. Using test image instead...")
            return test_with_generated_image()
            
        # Set camera properties for better image quality
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        print("\nCamera Controls:")
        print("  'q' - Quit")
        print("  's' - Analyze current frame")
        print("  'c' - Continuous analysis (toggle)")
        print("  'r' - Save results to file (toggle)")
        print("  'p' - Save current frame as image")
        print("  'h' - Show analysis history")
        
        continuous_mode = False
        frame_count = 0
        last_analysis_time = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Could not read frame")
                break
            
            frame_count += 1
            current_time = time.time()
            
            # Create display frame with overlays
            display_frame = frame.copy()
            
            # Draw sky region indicator
            height, width = frame.shape[:2]
            sky_height = int(height * 0.3)
            cv2.rectangle(display_frame, (0, 0), (width, sky_height), (0, 255, 0), 2)
            cv2.putText(display_frame, "Sky Analysis Region", (10, 25), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Add status indicators
            status_y = height - 60
            cv2.putText(display_frame, f"Frame: {frame_count}", (10, status_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(display_frame, f"Continuous: {'ON' if continuous_mode else 'OFF'}", 
                       (10, status_y + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, 
                       (0, 255, 0) if continuous_mode else (0, 0, 255), 2)
            cv2.putText(display_frame, f"Save Results: {'ON' if save_results else 'OFF'}", 
                       (10, status_y + 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, 
                       (0, 255, 0) if save_results else (0, 0, 255), 2)
            
            # Continuous analysis mode
            if continuous_mode and (current_time - last_analysis_time > 2.0):  # Every 2 seconds
                result = analyze_frame(sky_analyzer, system_status, frame)
                analysis_history.append(result)
                
                # Display result on frame
                condition = result.get('sky_condition', {}).get('condition', 'unknown')
                confidence = result.get('sky_condition', {}).get('confidence', 0)
                cv2.putText(display_frame, f"Sky: {condition} ({confidence:.2f})", 
                           (width - 300, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                
                last_analysis_time = current_time
                
                if save_results:
                    save_analysis_result(result, frame_count)
            
            # Display the frame
            cv2.imshow('Sky Analysis - See console for controls', display_frame)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                break
            elif key == ord('s'):
                print(f"\n[Frame {frame_count}] Analyzing sky condition...")
                result = analyze_frame(sky_analyzer, system_status, frame)
                analysis_history.append(result)
                display_analysis_result(result)
                
                if save_results:
                    save_analysis_result(result, frame_count)
                    
            elif key == ord('c'):
                continuous_mode = not continuous_mode
                print(f"Continuous analysis: {'ENABLED' if continuous_mode else 'DISABLED'}")
                
            elif key == ord('r'):
                save_results = not save_results
                print(f"Result saving: {'ENABLED' if save_results else 'DISABLED'}")
                
            elif key == ord('p'):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"sky_frame_{timestamp}.jpg"
                cv2.imwrite(filename, frame)
                print(f"Frame saved as: {filename}")
                
            elif key == ord('h'):
                display_analysis_history(analysis_history)
                
    except Exception as e:
        print(f"Error during camera operation: {e}")
    finally:
        if cap:
            cap.release()
        cv2.destroyAllWindows()
        
        # Save final results
        if analysis_history and save_results:
            save_analysis_history(analysis_history)

def analyze_frame(sky_analyzer, system_status, frame):
    """Analyze a single frame and return comprehensive results"""
    try:
        # Sky condition analysis
        sky_result = sky_analyzer.analyze_sky_condition(frame)
        
        # Enhanced system metrics with weather
        enhanced_metrics = system_status.get_enhanced_metrics(frame)
        
        # Combine results
        result = {
            'timestamp': datetime.now().isoformat(),
            'sky_condition': sky_result,
            'system_weather': enhanced_metrics.get('weather', {}),
            'visibility_estimate': sky_analyzer.get_visibility_estimate(
                sky_result.get('condition', 'unknown'), 
                sky_result.get('confidence', 0)
            ),
            'frame_info': {
                'height': frame.shape[0],
                'width': frame.shape[1],
                'channels': frame.shape[2] if len(frame.shape) > 2 else 1
            }
        }
        
        return result
        
    except Exception as e:
        return {
            'timestamp': datetime.now().isoformat(),
            'error': str(e),
            'sky_condition': {'condition': 'error', 'confidence': 0}
        }

def display_analysis_result(result):
    """Display analysis result in formatted output"""
    print("=" * 60)
    print(f"Sky Analysis Result - {result['timestamp']}")
    print("=" * 60)
    
    sky_data = result.get('sky_condition', {})
    print(f"Sky Condition: {sky_data.get('condition', 'unknown')}")
    print(f"Confidence: {sky_data.get('confidence', 0):.2f}")
    print(f"Visibility Estimate: {result.get('visibility_estimate', 'unknown')}")
    
    # Show detailed analysis
    if 'analysis_methods' in sky_data:
        print("\nDetailed Analysis:")
        for method, data in sky_data['analysis_methods'].items():
            print(f"  {method.capitalize()}: {data.get('condition', 'unknown')} "
                  f"(confidence: {data.get('confidence', 0):.2f})")
    
    # Frame information
    frame_info = result.get('frame_info', {})
    print(f"\nFrame Info: {frame_info.get('width', 0)}x{frame_info.get('height', 0)}")
    
    if sky_data.get('mock'):
        print("\n⚠️  Using mock analysis (modules not fully available)")
    
    print("=" * 60)

def display_analysis_history(history):
    """Display summary of analysis history"""
    if not history:
        print("No analysis history available")
        return
    
    print("\n" + "=" * 60)
    print(f"Analysis History ({len(history)} results)")
    print("=" * 60)
    
    # Count conditions
    conditions = {}
    for result in history:
        condition = result.get('sky_condition', {}).get('condition', 'unknown')
        conditions[condition] = conditions.get(condition, 0) + 1
    
    print("Condition Summary:")
    for condition, count in conditions.items():
        percentage = (count / len(history)) * 100
        print(f"  {condition}: {count} ({percentage:.1f}%)")
    
    # Show recent results
    print(f"\nRecent Results (last {min(5, len(history))}):")
    for i, result in enumerate(history[-5:], 1):
        sky_data = result.get('sky_condition', {})
        timestamp = result.get('timestamp', '')[:19]  # Remove microseconds
        print(f"  {i}. {timestamp}: {sky_data.get('condition', 'unknown')} "
              f"({sky_data.get('confidence', 0):.2f})")
    
    print("=" * 60)

def save_analysis_result(result, frame_number):
    """Save individual analysis result to file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"sky_analysis_{timestamp}_frame_{frame_number}.json"
    
    try:
        with open(filename, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        print(f"Result saved to: {filename}")
    except Exception as e:
        print(f"Error saving result: {e}")

def save_analysis_history(history):
    """Save complete analysis history"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"sky_analysis_session_{timestamp}.json"
    
    try:
        session_data = {
            'session_info': {
                'timestamp': datetime.now().isoformat(),
                'total_analyses': len(history),
                'duration_minutes': 0  # Could calculate from timestamps
            },
            'results': history
        }
        
        with open(filename, 'w') as f:
            json.dump(session_data, f, indent=2, default=str)
        print(f"Session history saved to: {filename}")
    except Exception as e:
        print(f"Error saving history: {e}")

def test_with_generated_image():
    """Test with a generated sky image when camera is not available"""
    print("Generating test sky image...")
    
    # Create a simple test image with blue sky and some clouds
    height, width = 480, 640
    image = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Blue sky background
    image[:, :] = [135, 206, 235]  # Sky blue
    
    # Add some white clouds
    cv2.ellipse(image, (200, 80), (60, 30), 0, 0, 360, (255, 255, 255), -1)
    cv2.ellipse(image, (400, 60), (80, 40), 0, 0, 360, (255, 255, 255), -1)
    cv2.ellipse(image, (500, 100), (50, 25), 0, 0, 360, (255, 255, 255), -1)
    
    print("Testing with generated sky image...")
    test_sky_analysis_with_image_data(image, "Generated Test Image")

def test_sky_analysis_with_image(image_path):
    """Test sky analysis with a static image file"""
    
    print(f"Testing sky analysis with image: {image_path}")
    
    # Load image
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Could not load image {image_path}")
        return
    
    test_sky_analysis_with_image_data(image, image_path)

def test_sky_analysis_with_image_data(image, source_name):
    """Test sky analysis with image data (common function for file and generated images)"""
    
    print(f"Analyzing sky condition in: {source_name}")
    
    # Initialize analyzer
    sky_analyzer = SkyAnalyzer() if MODULES_AVAILABLE else MockSkyAnalyzer()
    system_status = PiSystemStatus() if MODULES_AVAILABLE else MockPiSystemStatus()
    
    # Analyze sky condition
    result = analyze_frame(sky_analyzer, system_status, image)
    
    # Display results
    print(f"\nResults for {source_name}:")
    display_analysis_result(result)
    
    # Display image with sky region highlighted
    display_image = image.copy()
    height, width = image.shape[:2]
    sky_region_height = int(height * 0.3)
    
    # Draw rectangle around sky region
    cv2.rectangle(display_image, (0, 0), (width, sky_region_height), (0, 255, 0), 2)
    cv2.putText(display_image, f"Sky: {result['sky_condition']['condition']} ({result['sky_condition']['confidence']:.2f})", 
                (10, sky_region_height + 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    # Add visibility estimate
    cv2.putText(display_image, f"Visibility: {result['visibility_estimate']}", 
                (10, sky_region_height + 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
    
    # Show image
    cv2.imshow(f'Sky Analysis Result - {source_name}', display_image)
    print("\nPress any key to close the image window...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def test_batch_images(image_directory):
    """Test sky analysis on a batch of images"""
    
    print(f"Testing batch analysis on directory: {image_directory}")
    
    # Get all image files
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
    image_files = []
    
    directory_path = Path(image_directory)
    if not directory_path.exists():
        print(f"Error: Directory {image_directory} does not exist")
        return
    
    for ext in image_extensions:
        image_files.extend(directory_path.glob(f'*{ext}'))
        image_files.extend(directory_path.glob(f'*{ext.upper()}'))
    
    if not image_files:
        print(f"No image files found in {image_directory}")
        return
    
    print(f"Found {len(image_files)} images to analyze")
    
    # Initialize analyzer
    sky_analyzer = SkyAnalyzer() if MODULES_AVAILABLE else MockSkyAnalyzer()
    system_status = PiSystemStatus() if MODULES_AVAILABLE else MockPiSystemStatus()
    
    # Analyze all images
    results = []
    for i, image_file in enumerate(image_files, 1):
        print(f"\nAnalyzing image {i}/{len(image_files)}: {image_file.name}")
        
        image = cv2.imread(str(image_file))
        if image is None:
            print(f"  Error: Could not load {image_file}")
            continue
        
        result = analyze_frame(sky_analyzer, system_status, image)
        result['image_file'] = str(image_file)
        results.append(result)
        
        # Quick display of result
        sky_data = result.get('sky_condition', {})
        print(f"  Result: {sky_data.get('condition', 'unknown')} "
              f"(confidence: {sky_data.get('confidence', 0):.2f})")
    
    # Summary
    print("\n" + "=" * 60)
    print("BATCH ANALYSIS SUMMARY")
    print("=" * 60)
    
    # Count conditions
    conditions = {}
    for result in results:
        condition = result.get('sky_condition', {}).get('condition', 'unknown')
        conditions[condition] = conditions.get(condition, 0) + 1
    
    print("Condition Distribution:")
    for condition, count in conditions.items():
        percentage = (count / len(results)) * 100
        print(f"  {condition}: {count} images ({percentage:.1f}%)")
    
    # Save batch results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"batch_sky_analysis_{timestamp}.json"
    
    batch_data = {
        'batch_info': {
            'timestamp': datetime.now().isoformat(),
            'directory': str(image_directory),
            'total_images': len(results),
            'conditions_summary': conditions
        },
        'results': results
    }
    
    try:
        with open(results_file, 'w') as f:
            json.dump(batch_data, f, indent=2, default=str)
        print(f"\nBatch results saved to: {results_file}")
    except Exception as e:
        print(f"Error saving batch results: {e}")

def performance_test():
    """Test the performance of sky analysis"""
    
    print("Running performance test...")
    
    # Create test image
    test_image = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)
    
    # Initialize analyzer
    sky_analyzer = SkyAnalyzer() if MODULES_AVAILABLE else MockSkyAnalyzer()
    
    # Warm-up run
    sky_analyzer.analyze_sky_condition(test_image)
    
    # Performance test
    num_iterations = 10
    start_time = time.time()
    
    for i in range(num_iterations):
        result = sky_analyzer.analyze_sky_condition(test_image)
    
    end_time = time.time()
    total_time = end_time - start_time
    avg_time = total_time / num_iterations
    fps = 1.0 / avg_time
    
    print(f"Performance Results:")
    print(f"  Total time for {num_iterations} analyses: {total_time:.3f} seconds")
    print(f"  Average time per analysis: {avg_time:.3f} seconds")
    print(f"  Theoretical FPS: {fps:.1f}")
    print(f"  Memory usage: Depends on image size and OpenCV operations")
    
    if MODULES_AVAILABLE:
        print(f"  Analysis methods: Real sky analyzer")
    else:
        print(f"  Analysis methods: Mock analyzer (for testing)")

def create_test_images():
    """Create various test images for sky condition validation"""
    
    print("Creating test sky condition images...")
    
    test_dir = Path("test_sky_images")
    test_dir.mkdir(exist_ok=True)
    
    # Clear sky
    clear_sky = np.zeros((480, 640, 3), dtype=np.uint8)
    clear_sky[:, :] = [135, 206, 235]  # Sky blue
    cv2.imwrite(str(test_dir / "clear_sky.jpg"), clear_sky)
    
    # Partly cloudy
    partly_cloudy = clear_sky.copy()
    cv2.ellipse(partly_cloudy, (200, 80), (60, 30), 0, 0, 360, (255, 255, 255), -1)
    cv2.ellipse(partly_cloudy, (400, 60), (40, 20), 0, 0, 360, (240, 240, 240), -1)
    cv2.imwrite(str(test_dir / "partly_cloudy.jpg"), partly_cloudy)
    
    # Cloudy
    cloudy = np.zeros((480, 640, 3), dtype=np.uint8)
    cloudy[:, :] = [128, 128, 128]  # Gray
    # Add some darker clouds
    cv2.ellipse(cloudy, (100, 60), (80, 40), 0, 0, 360, (100, 100, 100), -1)
    cv2.ellipse(cloudy, (300, 80), (100, 50), 0, 0, 360, (90, 90, 90), -1)
    cv2.ellipse(cloudy, (500, 70), (70, 35), 0, 0, 360, (110, 110, 110), -1)
    cv2.imwrite(str(test_dir / "cloudy.jpg"), cloudy)
    
    # Overcast
    overcast = np.zeros((480, 640, 3), dtype=np.uint8)
    overcast[:, :] = [80, 80, 80]  # Dark gray
    cv2.imwrite(str(test_dir / "overcast.jpg"), overcast)
    
    print(f"Test images created in: {test_dir}")
    print("  - clear_sky.jpg")
    print("  - partly_cloudy.jpg") 
    print("  - cloudy.jpg")
    print("  - overcast.jpg")
    
    return str(test_dir)

def main():
    """Main function with argument parsing for different test modes"""
    
    parser = argparse.ArgumentParser(description='Sky Condition Analysis Test Suite')
    parser.add_argument('--mode', choices=['camera', 'image', 'batch', 'performance', 'create-tests'], 
                       default='camera', help='Test mode to run')
    parser.add_argument('--input', type=str, help='Input file or directory path')
    parser.add_argument('--generate-test-images', action='store_true', 
                       help='Generate test images before running')
    
    args = parser.parse_args()
    
    print("Sky Condition Analysis Test Suite")
    print("=" * 40)
    print(f"Mode: {args.mode}")
    print(f"Modules available: {MODULES_AVAILABLE}")
    print()
    
    # Generate test images if requested
    if args.generate_test_images:
        test_dir = create_test_images()
        if args.mode == 'batch' and not args.input:
            args.input = test_dir
    
    # Run appropriate test mode
    if args.mode == 'camera':
        print("Testing with live camera feed...")
        test_sky_analysis_with_camera()
        
    elif args.mode == 'image':
        if not args.input:
            print("Error: --input required for image mode")
            print("Usage: python test_sky_analysis.py --mode image --input path/to/image.jpg")
            return
        test_sky_analysis_with_image(args.input)
        
    elif args.mode == 'batch':
        if not args.input:
            print("Error: --input required for batch mode")
            print("Usage: python test_sky_analysis.py --mode batch --input path/to/directory")
            return
        test_batch_images(args.input)
        
    elif args.mode == 'performance':
        performance_test()
        
    elif args.mode == 'create-tests':
        create_test_images()
        
    print("\nTest completed.")

if __name__ == "__main__":
    main()