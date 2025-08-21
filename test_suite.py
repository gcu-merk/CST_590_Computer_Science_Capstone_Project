#!/usr/bin/env python3
"""
Traffic Monitoring System - Comprehensive Test Suite
Validates Pi 5 optimizations and recommended technology improvements
"""

import unittest
import asyncio
import os
import sys
import time
import json
import tempfile
import sqlite3
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

class TestHardwareIntegration(unittest.TestCase):
    """Test hardware integration improvements"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        
    def test_picamera2_integration(self):
        """Test picamera2 integration with fallback"""
        with patch('importlib.import_module') as mock_import:
            # Test picamera2 available
            mock_picamera2 = MagicMock()
            mock_import.return_value = mock_picamera2
            
            from edge_processing.vehicle_detection_service import VehicleDetectionService
            
            service = VehicleDetectionService()
            self.assertIsNotNone(service.camera)
            
            # Test fallback to OpenCV
            mock_import.side_effect = ImportError("picamera2 not available")
            service_fallback = VehicleDetectionService()
            self.assertIsNotNone(service_fallback.camera)
    
    def test_tflite_optimization(self):
        """Test TensorFlow Lite optimization"""
        with patch('tflite_runtime.interpreter.Interpreter') as mock_interpreter:
            mock_interp = MagicMock()
            mock_interpreter.return_value = mock_interp
            
            from edge_processing.vehicle_detection_service import VehicleDetectionService
            
            service = VehicleDetectionService()
            # Should use TFLite by default on Pi
            self.assertTrue(service.use_tflite)
    
    def test_gpio_radar_integration(self):
        """Test GPIO and radar integration"""
        with patch('gpiozero.Device.pin_factory'), \
             patch('serial.Serial') as mock_serial:
            
            mock_serial_instance = MagicMock()
            mock_serial.return_value = mock_serial_instance
            
            from edge_processing.speed_analysis_service import SpeedAnalysisService
            
            service = SpeedAnalysisService()
            self.assertIsNotNone(service.radar_sensor)
    
    def test_gpu_monitoring(self):
        """Test GPU monitoring capabilities"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.stdout = "temp=45.2'C"
            
            from edge_processing.system_health_monitor import SystemHealthMonitor
            
            monitor = SystemHealthMonitor()
            metrics = monitor.get_gpu_metrics()
            self.assertIn('temperature', metrics)

class TestEdgeProcessingServices(unittest.TestCase):
    """Test edge processing service functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
    
    def test_vehicle_detection_service(self):
        """Test vehicle detection service"""
        with patch('cv2.VideoCapture'), \
             patch('tflite_runtime.interpreter.Interpreter'):
            
            from edge_processing.vehicle_detection_service import VehicleDetectionService
            
            service = VehicleDetectionService()
            
            # Test detection with mock frame
            mock_frame = Mock()
            detections = service.detect_vehicles(mock_frame)
            self.assertIsInstance(detections, list)
    
    def test_speed_analysis_service(self):
        """Test speed analysis service"""
        with patch('serial.Serial'), \
             patch('gpiozero.Device.pin_factory'):
            
            from edge_processing.speed_analysis_service import SpeedAnalysisService
            
            service = SpeedAnalysisService()
            
            # Test speed calculation
            speed = service.calculate_speed(10.0)  # Mock doppler frequency
            self.assertIsInstance(speed, float)
            self.assertGreaterEqual(speed, 0)
    
    def test_data_fusion_engine(self):
        """Test data fusion engine"""
        from edge_processing.data_fusion_engine import DataFusionEngine
        
        engine = DataFusionEngine()
        
        # Test data fusion
        camera_data = {
            'vehicles': [{'id': 1, 'bbox': [100, 100, 200, 200], 'confidence': 0.8}],
            'timestamp': time.time()
        }
        
        radar_data = {
            'speed': 25.5,
            'timestamp': time.time()
        }
        
        fused_data = engine.fuse_data(camera_data, radar_data)
        self.assertIn('vehicles', fused_data)
        self.assertIn('speed', fused_data)
    
    def test_system_health_monitor(self):
        """Test system health monitoring"""
        with patch('psutil.cpu_percent', return_value=45.0), \
             patch('psutil.virtual_memory') as mock_memory, \
             patch('subprocess.run') as mock_run:
            
            mock_memory.return_value.percent = 60.0
            mock_run.return_value.stdout = "temp=50.1'C"
            
            from edge_processing.system_health_monitor import SystemHealthMonitor
            
            monitor = SystemHealthMonitor()
            health = monitor.get_system_health()
            
            self.assertIn('cpu_usage', health)
            self.assertIn('memory_usage', health)
            self.assertIn('gpu_temperature', health)

class TestAPIGateway(unittest.TestCase):
    """Test API gateway functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
    
    def test_flask_socketio_integration(self):
        """Test Flask-SocketIO integration"""
        with patch('flask_socketio.SocketIO'):
            from edge_api.edge_api_gateway import EdgeAPIGateway
            
            gateway = EdgeAPIGateway()
            self.assertIsNotNone(gateway.app)
            self.assertIsNotNone(gateway.socketio)
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        with patch('flask_socketio.SocketIO'):
            from edge_api.edge_api_gateway import EdgeAPIGateway
            
            gateway = EdgeAPIGateway()
            
            with gateway.app.test_client() as client:
                response = client.get('/health')
                self.assertEqual(response.status_code, 200)
                data = json.loads(response.data)
                self.assertIn('status', data)
    
    def test_detection_endpoint(self):
        """Test detection endpoint"""
        with patch('flask_socketio.SocketIO'):
            from edge_api.edge_api_gateway import EdgeAPIGateway
            
            gateway = EdgeAPIGateway()
            
            with gateway.app.test_client() as client:
                response = client.get('/api/detections')
                self.assertEqual(response.status_code, 200)

class TestDatabaseIntegration(unittest.TestCase):
    """Test SQLite database integration"""
    
    def setUp(self):
        """Set up test database"""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()
    
    def tearDown(self):
        """Clean up test database"""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_database_creation(self):
        """Test database creation"""
        from data_collection.data_persister.data_persister import DataPersister
        
        persister = DataPersister(db_path=self.db_path)
        persister.initialize_database()
        
        # Check if tables exist
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        self.assertIn('vehicle_detections', tables)
        self.assertIn('speed_measurements', tables)
    
    def test_data_insertion(self):
        """Test data insertion into SQLite"""
        from data_collection.data_persister.data_persister import DataPersister
        
        persister = DataPersister(db_path=self.db_path)
        persister.initialize_database()
        
        # Test vehicle detection insertion
        detection_data = {
            'timestamp': time.time(),
            'vehicle_id': 'test_001',
            'bbox': [100, 100, 200, 200],
            'confidence': 0.85,
            'vehicle_type': 'car'
        }
        
        result = persister.store_vehicle_detection(detection_data)
        self.assertTrue(result)

class TestContainerDeployment(unittest.TestCase):
    """Test Docker container deployment"""
    
    def test_dockerfile_exists(self):
        """Test Dockerfile exists and is valid"""
        dockerfile_path = Path(__file__).parent / 'Dockerfile'
        self.assertTrue(dockerfile_path.exists())
        
        with open(dockerfile_path) as f:
            content = f.read()
            self.assertIn('FROM python:', content)
            self.assertIn('RUN apt-get update', content)
    
    def test_docker_compose_exists(self):
        """Test docker-compose.yml exists and is valid"""
        compose_path = Path(__file__).parent / 'docker-compose.yml'
        self.assertTrue(compose_path.exists())
        
        with open(compose_path) as f:
            content = f.read()
            self.assertIn('version:', content)
            self.assertIn('services:', content)

class TestPerformanceOptimizations(unittest.TestCase):
    """Test performance optimizations"""
    
    def test_memory_usage(self):
        """Test memory usage is reasonable"""
        import psutil
        
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        
        # Should use less than 500MB for edge deployment
        self.assertLess(memory_mb, 500)
    
    def test_inference_speed(self):
        """Test inference speed with TFLite"""
        with patch('tflite_runtime.interpreter.Interpreter') as mock_interpreter:
            mock_interp = MagicMock()
            mock_interpreter.return_value = mock_interp
            
            from edge_processing.vehicle_detection_service import VehicleDetectionService
            
            service = VehicleDetectionService()
            
            # Mock frame processing
            start_time = time.time()
            mock_frame = Mock()
            service.detect_vehicles(mock_frame)
            inference_time = time.time() - start_time
            
            # Should be fast for edge inference
            self.assertLess(inference_time, 0.1)

class TestMultiVehicleTracking(unittest.TestCase):
    """Test multi-vehicle tracking service"""
    
    def test_tracking_initialization(self):
        """Test tracking service initialization"""
        # This will be implemented when multi-vehicle tracking is added
        pass
    
    def test_sort_algorithm_integration(self):
        """Test SORT algorithm integration"""
        # This will be implemented when SORT tracking is added
        pass

class TestSystemIntegration(unittest.TestCase):
    """Test complete system integration"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.temp_dir = tempfile.mkdtemp()
    
    @patch('edge_processing.vehicle_detection_service.VehicleDetectionService')
    @patch('edge_processing.speed_analysis_service.SpeedAnalysisService')
    @patch('edge_processing.data_fusion_engine.DataFusionEngine')
    @patch('edge_processing.system_health_monitor.SystemHealthMonitor')
    def test_edge_orchestrator(self, mock_health, mock_fusion, mock_speed, mock_detection):
        """Test edge orchestrator coordination"""
        from main_edge_app import EdgeOrchestrator
        
        orchestrator = EdgeOrchestrator()
        
        # Test service initialization
        self.assertTrue(orchestrator.initialize_services())
        
        # Test graceful shutdown
        orchestrator.shutdown()

if __name__ == '__main__':
    # Configure test runner
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test cases
    test_classes = [
        TestHardwareIntegration,
        TestEdgeProcessingServices,
        TestAPIGateway,
        TestDatabaseIntegration,
        TestContainerDeployment,
        TestPerformanceOptimizations,
        TestMultiVehicleTracking,
        TestSystemIntegration
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print(f"{'='*60}")
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
