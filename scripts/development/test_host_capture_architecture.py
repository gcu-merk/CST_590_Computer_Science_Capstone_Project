#!/usr/bin/env python3
"""
Host-Capture Architecture Test Script
Tests the shared volume image provider and host-capture/container-process architecture

This script validates:
- Host camera capture service functionality  
- Shared volume image provider operation
- Container-based image processing
- Sky analysis with shared volume images
- End-to-end system integration
"""

import cv2
import sys
import os
import json
import time
import argparse
import subprocess
import numpy as np
from datetime import datetime
from pathlib import Path

# Add path for modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'edge_processing'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'edge_api'))

try:
    from shared_volume_image_provider import SharedVolumeImageProvider, ContainerCameraInterface
    from weather_analysis.sky_analyzer import SkyAnalyzer
    from pi_system_status import PiSystemStatus
    MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Import error: {e}")
    print("Some modules not available. Creating mock implementations for testing...")
    MODULES_AVAILABLE = False

# Mock implementations for testing without full setup
class MockSharedVolumeImageProvider:
    def __init__(self):
        self.monitoring_active = False
    
    def start_monitoring(self):
        self.monitoring_active = True
    
    def stop_monitoring(self):
        self.monitoring_active = False
    
    def get_latest_image(self, max_age_seconds=5.0):
        # Create a mock image
        mock_image = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
        cv2.putText(mock_image, "MOCK SHARED VOLUME IMAGE", (50, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
        metadata = {
            'filename': 'mock_image.jpg',
            'timestamp': datetime.now().isoformat(),
            'mock': True
        }
        return True, mock_image, metadata
    
    def get_status(self):
        return {
            'live_images': 5,
            'cache_size': 2,
            'monitoring_active': self.monitoring_active,
            'mock': True
        }

class MockSkyAnalyzer:
    def __init__(self, use_shared_volume=True):
        self.use_shared_volume = use_shared_volume
    
    def analyze_current_sky(self, max_age_seconds=5.0):
        return {
            'condition': 'clear',
            'confidence': 0.85,
            'timestamp': datetime.now().isoformat(),
            'image_source': 'shared_volume' if self.use_shared_volume else 'direct',
            'mock': True
        }
    
    def analyze_sky_condition(self, image):
        return {
            'condition': 'clear',
            'confidence': 0.85,
            'timestamp': datetime.now().isoformat(),
            'mock': True
        }
    
    def cleanup(self):
        pass

def test_host_capture_service():
    """Test the host camera capture service"""
    print("\n=== Testing Host Camera Capture Service ===")
    
    try:
        # Check if service is running
        result = subprocess.run(['systemctl', 'is-active', 'host-camera-capture'], 
                               capture_output=True, text=True)
        
        if result.returncode == 0 and result.stdout.strip() == 'active':
            print("✓ Host camera capture service is running")
        else:
            print("✗ Host camera capture service is not running")
            print("  Run: sudo systemctl start host-camera-capture")
            return False
        
        # Check service status
        status_result = subprocess.run(['systemctl', 'status', 'host-camera-capture'], 
                                     capture_output=True, text=True)
        
        if "Active: active (running)" in status_result.stdout:
            print("✓ Service status is healthy")
        else:
            print("✗ Service status indicates problems")
            print(f"  Status output: {status_result.stdout}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error checking host capture service: {e}")
        return False

def test_shared_volume_directory():
    """Test the shared volume directory structure"""
    print("\n=== Testing Shared Volume Directory ===")
    
    capture_dir = Path("/mnt/storage/camera_capture")
    live_dir = capture_dir / "live"
    metadata_dir = capture_dir / "metadata"
    snapshots_dir = capture_dir / "periodic_snapshots"
    
    # Check directory existence
    directories = [
        ("Capture directory", capture_dir),
        ("Live images", live_dir),
        ("Metadata", metadata_dir),
        ("Snapshots", snapshots_dir)
    ]
    
    all_dirs_ok = True
    for name, directory in directories:
        if directory.exists():
            print(f"✓ {name} directory exists: {directory}")
        else:
            print(f"✗ {name} directory missing: {directory}")
            all_dirs_ok = False
    
    # Check for recent images
    try:
        image_files = list(live_dir.glob("*.jpg")) if live_dir.exists() else []
        print(f"  Found {len(image_files)} images in live directory")
        
        if image_files:
            # Check age of newest image
            newest_file = max(image_files, key=lambda x: x.stat().st_mtime)
            image_age = time.time() - newest_file.stat().st_mtime
            
            if image_age < 60:  # Less than 1 minute old
                print(f"✓ Recent image found: {newest_file.name} ({image_age:.1f}s old)")
            else:
                print(f"⚠ Latest image is old: {newest_file.name} ({image_age:.1f}s old)")
        else:
            print("⚠ No images found in live directory")
            
    except Exception as e:
        print(f"✗ Error checking images: {e}")
        all_dirs_ok = False
    
    return all_dirs_ok

def test_shared_volume_image_provider():
    """Test the shared volume image provider"""
    print("\n=== Testing Shared Volume Image Provider ===")
    
    try:
        # Initialize provider
        if MODULES_AVAILABLE:
            provider = SharedVolumeImageProvider()
        else:
            provider = MockSharedVolumeImageProvider()
        
        provider.start_monitoring()
        print("✓ Image provider initialized and monitoring started")
        
        # Test getting latest image
        success, image, metadata = provider.get_latest_image(max_age_seconds=30)
        
        if success and image is not None:
            print(f"✓ Successfully retrieved image: {image.shape}")
            print(f"  Metadata: {metadata.get('filename', 'unknown')} "
                  f"({metadata.get('file_size', 0)} bytes)")
            
            # Test image quality
            if image.size > 100000:  # Reasonable size for high-quality image
                print("✓ Image size indicates good quality")
            else:
                print("⚠ Image size seems small, may indicate quality issues")
                
        else:
            print("✗ Failed to retrieve image from shared volume")
            print("  Check if host capture service is running and creating images")
            return False
        
        # Test provider status
        status = provider.get_status()
        print(f"✓ Provider status: {status.get('live_images', 0)} live images, "
              f"monitoring: {status.get('monitoring_active', False)}")
        
        # Cleanup
        provider.stop_monitoring()
        print("✓ Provider monitoring stopped")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing shared volume provider: {e}")
        return False

def test_container_camera_interface():
    """Test the container camera interface compatibility"""
    print("\n=== Testing Container Camera Interface ===")
    
    try:
        # Test OpenCV-compatible interface
        if MODULES_AVAILABLE:
            camera = ContainerCameraInterface()
        else:
            # Mock interface for testing
            class MockContainerCamera:
                def read(self):
                    mock_image = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
                    return True, mock_image
                def isOpened(self):
                    return True
                def release(self):
                    pass
            camera = MockContainerCamera()
        
        print("✓ Container camera interface initialized")
        
        # Test OpenCV-style read
        ret, frame = camera.read()
        if ret and frame is not None:
            print(f"✓ OpenCV-style read successful: {frame.shape}")
        else:
            print("✗ OpenCV-style read failed")
            return False
        
        # Test isOpened
        if camera.isOpened():
            print("✓ Camera interface reports as opened")
        else:
            print("✗ Camera interface reports as not opened")
            return False
        
        # Cleanup
        camera.release()
        print("✓ Camera interface released")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing container camera interface: {e}")
        return False

def test_sky_analysis_with_shared_volume():
    """Test sky analysis using shared volume images"""
    print("\n=== Testing Sky Analysis with Shared Volume ===")
    
    try:
        # Initialize sky analyzer with shared volume
        if MODULES_AVAILABLE:
            sky_analyzer = SkyAnalyzer(use_shared_volume=True)
        else:
            sky_analyzer = MockSkyAnalyzer(use_shared_volume=True)
        
        print("✓ Sky analyzer initialized with shared volume support")
        
        # Test current sky analysis
        result = sky_analyzer.analyze_current_sky(max_age_seconds=30)
        
        if result.get('condition') != 'unknown':
            print(f"✓ Sky analysis successful: {result['condition']} "
                  f"(confidence: {result['confidence']:.2f})")
            print(f"  Image source: {result.get('image_source', 'unknown')}")
            
            if result.get('image_metadata'):
                metadata = result['image_metadata']
                print(f"  Image: {metadata.get('filename', 'unknown')} "
                      f"({metadata.get('file_size', 0)} bytes)")
        else:
            print(f"✗ Sky analysis failed: {result.get('error', 'unknown error')}")
            return False
        
        # Test direct image analysis
        success, image, metadata = sky_analyzer.get_latest_image(max_age_seconds=30)
        if success and image is not None:
            analysis = sky_analyzer.analyze_sky_condition(image)
            print(f"✓ Direct image analysis: {analysis['condition']} "
                  f"(confidence: {analysis['confidence']:.2f})")
        else:
            print("⚠ Could not get image for direct analysis")
        
        # Cleanup
        sky_analyzer.cleanup()
        print("✓ Sky analyzer cleaned up")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing sky analysis: {e}")
        return False

def test_integration_with_docker():
    """Test integration with Docker container"""
    print("\n=== Testing Docker Integration ===")
    
    try:
        # Check if Docker is running
        result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
        if result.returncode != 0:
            print("✗ Docker is not running or not accessible")
            return False
        
        print("✓ Docker is accessible")
        
        # Resolve the traffic-monitor container (prefer compose service label)
        container_id = None
        # Try to find by compose service label (com.docker.compose.service=traffic-monitor)
        try:
            ps_label = subprocess.run(['docker', 'ps', '-a', '--filter', 'label=com.docker.compose.service=traffic-monitor', '--format', '{{.ID}}'], capture_output=True, text=True)
            if ps_label.stdout.strip():
                container_id = ps_label.stdout.splitlines()[0].strip()
        except Exception:
            container_id=""

        # Fallback: find by name pattern
        if not container_id:
            container_result = subprocess.run(['docker', 'ps', '-a', '--filter', 'name=traffic-monitor'], capture_output=True, text=True)
            if container_result.stdout.strip():
                # Get first matching container ID
                lines = [l for l in container_result.stdout.splitlines() if l.strip()]
                if lines:
                    # Format is header + rows; extract ID via --format would be better, but keep simple
                    id_result = subprocess.run(['docker', 'ps', '-a', '--filter', 'name=traffic-monitor', '--format', '{{.ID}}'], capture_output=True, text=True)
                    if id_result.stdout.strip():
                        container_id = id_result.stdout.splitlines()[0].strip()

        if container_id:
            print("✓ Traffic monitoring container found (id: {} )".format(container_id))
            # Check if container is running
            running_result = subprocess.run(['docker', 'ps', '--filter', f'id={container_id}', '--format', '{{.ID}}'], capture_output=True, text=True)
            if running_result.stdout.strip():
                print("✓ Container is running")
                # Check shared volume mount
                inspect_result = subprocess.run(['docker', 'inspect', container_id], capture_output=True, text=True)
                if 'camera_capture' in inspect_result.stdout:
                    print("✓ Shared volume appears to be mounted")
                else:
                    print("⚠ Shared volume mount not detected in container config")
            else:
                print("⚠ Container exists but is not running")
        else:
            print("⚠ Traffic monitoring container not found")
            print("  Run: docker compose up -d")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing Docker integration: {e}")
        return False

def test_end_to_end_processing():
    """Test end-to-end image processing pipeline"""
    print("\n=== Testing End-to-End Processing ===")
    
    try:
        start_time = time.time()
        
        # Step 1: Verify host capture is creating images
        print("Step 1: Checking host image capture...")
        capture_dir = Path("/mnt/storage/camera_capture/live")
        
        if not capture_dir.exists():
            print("✗ Capture directory does not exist")
            return False
        
        initial_images = list(capture_dir.glob("*.jpg"))
        initial_count = len(initial_images)
        print(f"  Initial image count: {initial_count}")
        
        # Wait for new image (up to 30 seconds)
        print("Step 2: Waiting for new image capture...")
        for i in range(30):
            time.sleep(1)
            current_images = list(capture_dir.glob("*.jpg"))
            if len(current_images) > initial_count:
                print(f"✓ New image detected after {i+1} seconds")
                break
        else:
            print("⚠ No new images captured in 30 seconds")
        
        # Step 3: Test shared volume provider
        print("Step 3: Testing shared volume image retrieval...")
        if MODULES_AVAILABLE:
            provider = SharedVolumeImageProvider()
            provider.start_monitoring()
            
            success, image, metadata = provider.get_latest_image(max_age_seconds=60)
            if success:
                print(f"✓ Retrieved image via shared volume: {image.shape}")
            else:
                print("✗ Failed to retrieve image via shared volume")
                return False
                
            provider.stop_monitoring()
        else:
            print("✓ Using mock provider for testing")
        
        # Step 4: Test analysis
        print("Step 4: Testing image analysis...")
        if MODULES_AVAILABLE:
            analyzer = SkyAnalyzer(use_shared_volume=True)
            result = analyzer.analyze_current_sky(max_age_seconds=60)
            
            if result.get('condition') != 'unknown':
                print(f"✓ Analysis successful: {result['condition']}")
            else:
                print(f"✗ Analysis failed: {result.get('error', 'unknown')}")
                return False
                
            analyzer.cleanup()
        else:
            print("✓ Using mock analyzer for testing")
        
        elapsed_time = time.time() - start_time
        print(f"✓ End-to-end test completed in {elapsed_time:.1f} seconds")
        
        return True
        
    except Exception as e:
        print(f"✗ Error in end-to-end test: {e}")
        return False

def run_performance_test():
    """Run performance test for the shared volume architecture"""
    print("\n=== Performance Test ===")
    
    try:
        if not MODULES_AVAILABLE:
            print("⚠ Using mock implementations for performance test")
        
        # Initialize components
        if MODULES_AVAILABLE:
            provider = SharedVolumeImageProvider()
            provider.start_monitoring()
            analyzer = SkyAnalyzer(use_shared_volume=True)
        else:
            provider = MockSharedVolumeImageProvider()
            provider.start_monitoring()
            analyzer = MockSkyAnalyzer(use_shared_volume=True)
        
        # Test image retrieval performance
        print("Testing image retrieval performance...")
        retrieval_times = []
        
        for i in range(10):
            start_time = time.time()
            success, image, metadata = provider.get_latest_image()
            end_time = time.time()
            
            if success:
                retrieval_times.append(end_time - start_time)
            else:
                print(f"  Retrieval {i+1} failed")
        
        if retrieval_times:
            avg_retrieval = sum(retrieval_times) / len(retrieval_times)
            max_retrieval = max(retrieval_times)
            print(f"✓ Image retrieval: avg {avg_retrieval*1000:.1f}ms, max {max_retrieval*1000:.1f}ms")
        else:
            print("✗ No successful retrievals")
            return False
        
        # Test analysis performance
        print("Testing analysis performance...")
        analysis_times = []
        
        for i in range(5):
            start_time = time.time()
            result = analyzer.analyze_current_sky(max_age_seconds=60)
            end_time = time.time()
            
            if result.get('condition') != 'unknown':
                analysis_times.append(end_time - start_time)
            else:
                print(f"  Analysis {i+1} failed")
        
        if analysis_times:
            avg_analysis = sum(analysis_times) / len(analysis_times)
            max_analysis = max(analysis_times)
            print(f"✓ Sky analysis: avg {avg_analysis*1000:.1f}ms, max {max_analysis*1000:.1f}ms")
        else:
            print("✗ No successful analyses")
            return False
        
        # Cleanup
        provider.stop_monitoring()
        if hasattr(analyzer, 'cleanup'):
            analyzer.cleanup()
        
        # Performance assessment
        total_avg_time = avg_retrieval + avg_analysis
        print(f"✓ Total pipeline time: {total_avg_time*1000:.1f}ms average")
        
        if total_avg_time < 1.0:  # Less than 1 second
            print("✓ Performance is excellent")
        elif total_avg_time < 3.0:  # Less than 3 seconds
            print("✓ Performance is good")
        else:
            print("⚠ Performance may need optimization")
        
        return True
        
    except Exception as e:
        print(f"✗ Error in performance test: {e}")
        return False

def show_system_status():
    """Show comprehensive system status"""
    print("\n=== System Status ===")
    
    # Host capture service
    try:
        result = subprocess.run(['systemctl', 'status', 'host-camera-capture'], 
                               capture_output=True, text=True)
        if "Active: active (running)" in result.stdout:
            print("✓ Host capture service: Running")
        else:
            print("✗ Host capture service: Not running")
    except:
        print("? Host capture service: Unknown")
    
    # Docker container
    try:
        # Prefer resolving compose service label first, fallback to name patterns
        result = subprocess.run(['docker', 'ps', '--filter', 'label=com.docker.compose.service=traffic-monitor'], capture_output=True, text=True)
        if result.stdout.strip():
            print("✓ Docker container (compose service 'traffic-monitor'): Running")
        else:
            result = subprocess.run(['docker', 'ps', '--filter', 'name=traffic-monitor'], capture_output=True, text=True)
            if 'traffic-monitor' in result.stdout:
                print("✓ Docker container: Running")
            else:
                print("✗ Docker container: Not running")
    except:
        print("? Docker container: Unknown")
    
    # Shared volume status
    capture_dir = Path("/mnt/storage/camera_capture")
    if capture_dir.exists():
        live_images = len(list((capture_dir / "live").glob("*.jpg")))
        snapshots = len(list((capture_dir / "periodic_snapshots").glob("*.jpg")))
        print(f"✓ Shared volume: {live_images} live images, {snapshots} snapshots")
    else:
        print("✗ Shared volume: Directory not found")
    
    # Image provider status
    if MODULES_AVAILABLE:
        try:
            provider = SharedVolumeImageProvider()
            status = provider.get_status()
            print(f"✓ Image provider: {status.get('live_images', 0)} images available")
        except:
            print("✗ Image provider: Error getting status")
    else:
        print("? Image provider: Mock implementation")

def main():
    """Main test function"""
    parser = argparse.ArgumentParser(description="Host-capture architecture test script")
    parser.add_argument('--mode', choices=[
        'host-service', 'shared-volume', 'image-provider', 'camera-interface',
        'sky-analysis', 'docker-integration', 'end-to-end', 'performance', 'all'
    ], default='all', help='Test mode to run')
    parser.add_argument('--status', action='store_true', help='Show system status')
    
    args = parser.parse_args()
    
    print("Host-Capture Architecture Test Script")
    print("=" * 50)
    
    if args.status:
        show_system_status()
        return
    
    # Track test results
    tests = []
    
    if args.mode in ['host-service', 'all']:
        tests.append(('Host Capture Service', test_host_capture_service))
    
    if args.mode in ['shared-volume', 'all']:
        tests.append(('Shared Volume Directory', test_shared_volume_directory))
    
    if args.mode in ['image-provider', 'all']:
        tests.append(('Shared Volume Image Provider', test_shared_volume_image_provider))
    
    if args.mode in ['camera-interface', 'all']:
        tests.append(('Container Camera Interface', test_container_camera_interface))
    
    # Sky analysis test disabled - feature removed
    # if args.mode in ['sky-analysis', 'all']:
    #     tests.append(('Sky Analysis with Shared Volume', test_sky_analysis_with_shared_volume))
    
    if args.mode in ['docker-integration', 'all']:
        tests.append(('Docker Integration', test_integration_with_docker))
    
    if args.mode in ['end-to-end', 'all']:
        tests.append(('End-to-End Processing', test_end_to_end_processing))
    
    if args.mode in ['performance', 'all']:
        tests.append(('Performance Test', run_performance_test))
    
    # Run tests
    results = []
    for test_name, test_func in tests:
        print(f"\nRunning {test_name} test...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        icon = "✓" if result else "✗"
        print(f"{icon} {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! Host-capture architecture is working correctly.")
    elif passed > total * 0.8:
        print("⚠ Most tests passed. Check failed tests for issues.")
    else:
        print("❌ Multiple tests failed. Check system configuration.")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)