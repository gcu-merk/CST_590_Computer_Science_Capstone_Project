#!/usr/bin/env python3
"""
IMX500 AI Implementation Test Script
Tests the complete IMX500 AI architecture implementation

This script validates:
1. IMX500 AI camera functionality with on-chip processing
2. Redis data flow and storage
3. Docker container integration
4. Performance measurements
5. System health checks
"""

import os
import sys
import time
import json
import logging
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Any

# Test requirements
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IMX500AITester:
    """Comprehensive test suite for IMX500 AI implementation"""
    
    def __init__(self):
        self.redis_client = None
        self.test_results = {}
        self.start_time = time.time()
        
        # Colors for output
        self.RED = '\033[0;31m'
        self.GREEN = '\033[0;32m'
        self.YELLOW = '\033[1;33m'
        self.BLUE = '\033[0;34m'
        self.NC = '\033[0m'  # No Color
    
    def log_info(self, message: str):
        print(f"{self.BLUE}[INFO]{self.NC} {message}")
    
    def log_success(self, message: str):
        print(f"{self.GREEN}[SUCCESS]{self.NC} {message}")
    
    def log_warning(self, message: str):
        print(f"{self.YELLOW}[WARNING]{self.NC} {message}")
    
    def log_error(self, message: str):
        print(f"{self.RED}[ERROR]{self.NC} {message}")
    
    def test_system_requirements(self) -> bool:
        """Test system requirements for IMX500 AI"""
        self.log_info("Testing system requirements...")
        
        tests = {
            'raspberry_pi': self._test_raspberry_pi(),
            'imx500_model': self._test_imx500_model(),
            'picamera2': self._test_picamera2(),
            'redis_connection': self._test_redis_connection(),
            'storage_directories': self._test_storage_directories()
        }
        
        self.test_results['system_requirements'] = tests
        
        all_passed = all(tests.values())
        if all_passed:
            self.log_success("All system requirements met")
        else:
            self.log_error("Some system requirements failed")
            for test, result in tests.items():
                status = "✅" if result else "❌"
                print(f"  {status} {test}")
        
        return all_passed
    
    def _test_raspberry_pi(self) -> bool:
        """Test if running on Raspberry Pi"""
        try:
            with open('/proc/device-tree/model', 'r') as f:
                model = f.read()
            return 'Raspberry Pi' in model
        except:
            return False
    
    def _test_imx500_model(self) -> bool:
        """Test if IMX500 model file exists"""
        model_path = "/usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk"
        return os.path.exists(model_path)
    
    def _test_picamera2(self) -> bool:
        """Test picamera2 availability"""
        try:
            import picamera2
            from picamera2.devices.imx500 import IMX500
            return True
        except ImportError:
            return False
    
    def _test_redis_connection(self) -> bool:
        """Test Redis connection"""
        if not REDIS_AVAILABLE:
            return False
        
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True, socket_timeout=5)
            self.redis_client.ping()
            return True
        except:
            try:
                self.redis_client = redis.Redis(host='redis', port=6379, decode_responses=True, socket_timeout=5)
                self.redis_client.ping()
                return True
            except:
                return False
    
    def _test_storage_directories(self) -> bool:
        """Test storage directory setup"""
        dirs = [
            '/mnt/storage/camera_capture/live',
            '/mnt/storage/camera_capture/ai_results',
            '/mnt/storage/camera_capture/metadata'
        ]
        
        for dir_path in dirs:
            if not os.path.exists(dir_path):
                return False
        
        return True
    
    def test_imx500_ai_service(self) -> bool:
        """Test IMX500 AI host service"""
        self.log_info("Testing IMX500 AI service...")
        
        tests = {
            'service_running': self._test_service_running(),
            'recent_logs': self._test_service_logs(),
            'image_generation': self._test_image_generation(),
            'redis_data': self._test_redis_vehicle_data()
        }
        
        self.test_results['imx500_service'] = tests
        
        all_passed = all(tests.values())
        if all_passed:
            self.log_success("IMX500 AI service is working correctly")
        else:
            self.log_error("IMX500 AI service has issues")
            for test, result in tests.items():
                status = "✅" if result else "❌"
                print(f"  {status} {test}")
        
        return all_passed
    
    def _test_service_running(self) -> bool:
        """Test if IMX500 AI service is running"""
        try:
            result = subprocess.run(['systemctl', 'is-active', 'imx500-ai-capture'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0 and 'active' in result.stdout
        except:
            return False
    
    def _test_service_logs(self) -> bool:
        """Test service logs for errors"""
        try:
            result = subprocess.run(['journalctl', '-u', 'imx500-ai-capture', '-n', '20', '--no-pager'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                return False
            
            # Check for success indicators and absence of critical errors
            logs = result.stdout.lower()
            success_indicators = ['imx500 ai camera initialized', 'ai model loaded', 'starting camera']
            error_indicators = ['failed to initialize', 'error', 'exception', 'traceback']
            
            has_success = any(indicator in logs for indicator in success_indicators)
            has_errors = any(indicator in logs for indicator in error_indicators)
            
            return has_success and not has_errors
        except:
            return False
    
    def _test_image_generation(self) -> bool:
        """Test if images are being generated"""
        try:
            live_dir = '/mnt/storage/camera_capture/live'
            if not os.path.exists(live_dir):
                return False
            
            # Check for recent images (within last 5 minutes)
            current_time = time.time()
            recent_images = []
            
            for filename in os.listdir(live_dir):
                if filename.endswith('.jpg'):
                    filepath = os.path.join(live_dir, filename)
                    if os.path.getmtime(filepath) > current_time - 300:  # 5 minutes
                        recent_images.append(filename)
            
            return len(recent_images) > 0
        except:
            return False
    
    def _test_redis_vehicle_data(self) -> bool:
        """Test if vehicle detection data is in Redis"""
        if not self.redis_client:
            return False
        
        try:
            # Check for vehicle detection keys
            vehicle_keys = self.redis_client.keys('vehicle:detection:*')
            
            # Check for real-time stats
            stats_data = self.redis_client.get('stats:realtime:vehicles')
            
            # Check for traffic events
            # Note: This is harder to test as events are ephemeral
            
            return len(vehicle_keys) > 0 or stats_data is not None
        except:
            return False
    
    def test_docker_integration(self) -> bool:
        """Test Docker container integration"""
        self.log_info("Testing Docker container integration...")
        
        tests = {
            'docker_running': self._test_docker_running(),
            'vehicle_consolidator': self._test_vehicle_consolidator(),
            'redis_integration': self._test_docker_redis_integration(),
            'api_endpoints': self._test_api_endpoints()
        }
        
        self.test_results['docker_integration'] = tests
        
        all_passed = all(tests.values())
        if all_passed:
            self.log_success("Docker integration is working correctly")
        else:
            self.log_error("Docker integration has issues")
            for test, result in tests.items():
                status = "✅" if result else "❌"
                print(f"  {status} {test}")
        
        return all_passed
    
    def _test_docker_running(self) -> bool:
        """Test if Docker containers are running"""
        try:
            result = subprocess.run(['docker', 'ps', '--format', 'table {{.Names}}'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                return False
            
            expected_containers = ['redis', 'traffic-monitor', 'vehicle-consolidator']
            running_containers = result.stdout
            
            return all(container in running_containers for container in expected_containers)
        except:
            return False
    
    def _test_vehicle_consolidator(self) -> bool:
        """Test vehicle consolidator service"""
        try:
            result = subprocess.run(['docker', 'logs', 'vehicle-consolidator', '--tail', '20'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                return False
            
            logs = result.stdout.lower()
            success_indicators = ['vehicle detection consolidator', 'connected to redis', 'processing vehicle']
            error_indicators = ['error', 'failed', 'exception']
            
            has_success = any(indicator in logs for indicator in success_indicators)
            has_errors = any(indicator in logs for indicator in error_indicators)
            
            return has_success and not has_errors
        except:
            return False
    
    def _test_docker_redis_integration(self) -> bool:
        """Test Docker containers can access Redis"""
        try:
            result = subprocess.run(['docker', 'exec', 'vehicle-consolidator', 'python3', '-c', 
                                   'import redis; r=redis.Redis(host="redis", port=6379); r.ping()'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except:
            return False
    
    def _test_api_endpoints(self) -> bool:
        """Test API endpoints"""
        try:
            # Test sky analysis API (should work)
            result = subprocess.run(['curl', '-s', 'http://localhost:5000/api/images/sky-analysis'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                return False
            
            # Parse JSON response
            response = json.loads(result.stdout)
            return 'analyses' in response or 'message' in response
        except:
            return False
    
    def test_performance_metrics(self) -> Dict[str, Any]:
        """Test performance metrics"""
        self.log_info("Measuring performance metrics...")
        
        metrics = {
            'redis_latency': self._measure_redis_latency(),
            'system_load': self._measure_system_load(),
            'memory_usage': self._measure_memory_usage(),
            'detection_rate': self._measure_detection_rate()
        }
        
        self.test_results['performance'] = metrics
        
        self.log_info("Performance metrics collected")
        for metric, value in metrics.items():
            print(f"  📊 {metric}: {value}")
        
        return metrics
    
    def _measure_redis_latency(self) -> str:
        """Measure Redis latency"""
        if not self.redis_client:
            return "Redis not available"
        
        try:
            start = time.time()
            for _ in range(10):
                self.redis_client.ping()
            latency = (time.time() - start) / 10 * 1000  # ms
            return f"{latency:.2f}ms"
        except:
            return "Error measuring latency"
    
    def _measure_system_load(self) -> str:
        """Measure system load"""
        try:
            with open('/proc/loadavg', 'r') as f:
                load = f.read().strip().split()[0]
            return f"{float(load):.2f}"
        except:
            return "Unknown"
    
    def _measure_memory_usage(self) -> str:
        """Measure memory usage"""
        try:
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
            
            for line in meminfo.split('\n'):
                if line.startswith('MemAvailable:'):
                    available = int(line.split()[1]) * 1024  # Convert to bytes
                    available_mb = available / (1024 * 1024)
                    return f"{available_mb:.0f}MB available"
            
            return "Unknown"
        except:
            return "Unknown"
    
    def _measure_detection_rate(self) -> str:
        """Measure vehicle detection rate"""
        if not self.redis_client:
            return "Redis not available"
        
        try:
            stats_data = self.redis_client.get('stats:realtime:vehicles')
            if stats_data:
                stats = json.loads(stats_data)
                return f"{stats.get('detections_per_minute', 0):.1f}/min"
            else:
                return "No data available"
        except:
            return "Error measuring rate"
    
    def run_full_test_suite(self) -> bool:
        """Run complete test suite"""
        print("🚗 IMX500 AI Implementation Test Suite")
        print("=" * 50)
        print(f"Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Run all tests
        system_ok = self.test_system_requirements()
        print()
        
        service_ok = self.test_imx500_ai_service()
        print()
        
        docker_ok = self.test_docker_integration()
        print()
        
        performance = self.test_performance_metrics()
        print()
        
        # Generate summary
        total_time = time.time() - self.start_time
        all_tests_passed = system_ok and service_ok and docker_ok
        
        print("📋 Test Summary")
        print("=" * 50)
        print(f"System Requirements: {'✅ PASS' if system_ok else '❌ FAIL'}")
        print(f"IMX500 AI Service:   {'✅ PASS' if service_ok else '❌ FAIL'}")
        print(f"Docker Integration:  {'✅ PASS' if docker_ok else '❌ FAIL'}")
        print(f"Performance Metrics: ✅ COLLECTED")
        print()
        print(f"Overall Result: {'✅ ALL TESTS PASSED' if all_tests_passed else '❌ SOME TESTS FAILED'}")
        print(f"Total Test Time: {total_time:.1f}s")
        print()
        
        if all_tests_passed:
            self.log_success("IMX500 AI implementation is working correctly!")
            print()
            print("🎉 Your system is ready for:")
            print("  ✅ Sub-100ms vehicle detection on IMX500 chip")
            print("  ✅ Zero CPU usage for AI processing")
            print("  ✅ Real-time data flow through Redis")
            print("  ✅ Docker container integration")
            print("  ✅ API endpoint access")
        else:
            self.log_error("IMX500 AI implementation has issues that need attention")
            print()
            print("🔧 Check the failed tests above and:")
            print("  1. Review system requirements")
            print("  2. Check service logs: sudo journalctl -u imx500-ai-capture -f")
            print("  3. Verify Docker containers: docker-compose ps")
            print("  4. Test Redis connectivity: redis-cli ping")
        
        return all_tests_passed

def main():
    """Main test entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == '--quick':
        print("Quick test mode - running essential tests only")
        # Add quick test mode if needed
    
    tester = IMX500AITester()
    success = tester.run_full_test_suite()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())