#!/usr/bin/env python3
"""
Main Edge Application Orchestrator
Coordinates all edge processing services for the traffic monitoring system
"""

import time
import logging
import signal
import sys
import threading
import argparse
from pathlib import Path

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add edge processing modules to path
sys.path.append(str(Path(__file__).parent / "edge_processing"))
sys.path.append(str(Path(__file__).parent / "edge_api"))

# Import edge processing services
from edge_processing.vehicle_detection.vehicle_detection_service import VehicleDetectionService
from edge_processing.speed_analysis.speed_analysis_service import SpeedAnalysisService
from edge_processing.data_fusion.data_fusion_engine import DataFusionEngine
from edge_processing.system_health.system_health_monitor import SystemHealthMonitor

# Import Swagger-enabled API gateway (fallback to original if not available)
try:
    from edge_api.swagger_api_gateway import SwaggerAPIGateway as EdgeAPIGateway
    logger.info("Using Swagger-enabled API gateway with interactive documentation")
    SWAGGER_ENABLED = True
except ImportError:
    from edge_api.edge_api_gateway import EdgeAPIGateway
    logger.warning("Swagger API gateway not available, using original API gateway")
    SWAGGER_ENABLED = False

# Weather analysis imports
try:
    from edge_processing.weather_analysis.sky_analysis_service import SkyAnalysisService
    from edge_api.pi_system_status import PiSystemStatus
    WEATHER_ANALYSIS_AVAILABLE = True
except ImportError as e:
    WEATHER_ANALYSIS_AVAILABLE = False

# Log weather analysis availability
if not WEATHER_ANALYSIS_AVAILABLE:
    logger.warning("Weather analysis modules not available - running without sky condition detection")

class EdgeOrchestrator:
    """
    Main orchestrator for all edge processing services
    """
    
    def __init__(self, sensors_enabled=True, weather_analysis_enabled=True):
        self.services = {}
        self.is_running = False
        self.sensors_enabled = sensors_enabled
        self.weather_analysis_enabled = weather_analysis_enabled and WEATHER_ANALYSIS_AVAILABLE
        
        # Weather analysis components
        if self.weather_analysis_enabled:
            self.sky_analyzer = SkyAnalysisService()
            self.system_status = PiSystemStatus()
            logger.info("Weather analysis enabled with enhanced sky analysis service")
        else:
            self.sky_analyzer = None
            self.system_status = None
            logger.info("Weather analysis disabled")
        
        # Initialize services
        self._initialize_services()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _initialize_services(self):
        """Initialize all edge processing services"""
        try:
            logger.info("Initializing edge processing services...")
            
            # 1. System Health Monitor (start first to monitor everything)
            self.services['health_monitor'] = SystemHealthMonitor(update_interval=10.0)
            
            if self.sensors_enabled:
                # 2. Vehicle Detection Service
                import os
                # Allow override of snapshot interval/path through env vars
                env_interval = os.getenv("SNAPSHOT_INTERVAL_MINUTES")
                snapshot_interval = int(env_interval) if env_interval else 5
                snapshot_path = os.getenv("PERIODIC_SNAPSHOT_PATH", "/mnt/storage/periodic_snapshots")
                self.services['vehicle_detection'] = VehicleDetectionService(
                    camera_index=0,  # Sony IMX500 AI Camera
                    model_path=None,  # Use default model
                    periodic_snapshots=True,  # Enable periodic snapshots
                    snapshot_interval_minutes=snapshot_interval,  # Interval (env overrideable)
                    periodic_snapshot_path=snapshot_path  # Save to SSD or override
                )
                
                # 3. Speed Analysis Service
                self.services['speed_analysis'] = SpeedAnalysisService(
                    radar_port='/dev/ttyACM0'  # OPS243-C Radar
                )
                
                # 4. Data Fusion Engine
                self.services['data_fusion'] = DataFusionEngine(
                    vehicle_detection_service=self.services['vehicle_detection'],
                    speed_analysis_service=self.services['speed_analysis']
                )
            
            # 5. Edge API Gateway
            self.services['api_gateway'] = EdgeAPIGateway(
                host='0.0.0.0',
                port=5000
            )
            
            # Log API gateway type
            if SWAGGER_ENABLED:
                logger.info("🚀 Swagger-enabled API gateway initialized")
                logger.info("📖 Interactive documentation will be available at: http://0.0.0.0:5000/docs/")
            else:
                logger.info("🚀 Standard API gateway initialized")
            
            # Set service references in API gateway
            self.services['api_gateway'].set_services(
                vehicle_detection=self.services.get('vehicle_detection'),
                speed_analysis=self.services.get('speed_analysis'),
                data_fusion=self.services.get('data_fusion'),
                system_health=self.services['health_monitor'],
                sky_analyzer=self.sky_analyzer,
                system_status=self.system_status
            )
            
            logger.info("All services initialized successfully")
            if self.weather_analysis_enabled:
                logger.info("Weather analysis integration enabled")
            
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            raise
    
    def start_all_services(self):
        """Start all edge processing services"""
        try:
            logger.info("Starting edge processing services...")
            self.is_running = True
            
            # Start system health monitoring first
            logger.info("Starting system health monitor...")
            self.services['health_monitor'].start_monitoring()
            
            # Register services with health monitor
            health_monitor = self.services['health_monitor']
            health_monitor.register_service('api_gateway')
            if self.sensors_enabled:
                health_monitor.register_service('vehicle_detection')
                health_monitor.register_service('speed_analysis')
                health_monitor.register_service('data_fusion')
                
                # Start vehicle detection service
                logger.info("Starting vehicle detection service...")
                if self.services['vehicle_detection'].start_detection():
                    health_monitor.update_service_status('vehicle_detection', True)
                    logger.info("✓ Vehicle detection service started")
                else:
                    logger.error("✗ Failed to start vehicle detection service")
                    health_monitor.update_service_status('vehicle_detection', False)
                
                # Start speed analysis service
                logger.info("Starting speed analysis service...")
                if self.services['speed_analysis'].start_analysis():
                    health_monitor.update_service_status('speed_analysis', True)
                    logger.info("✓ Speed analysis service started")
                else:
                    logger.error("✗ Failed to start speed analysis service")
                    health_monitor.update_service_status('speed_analysis', False)
                
                # Start data fusion engine
                logger.info("Starting data fusion engine...")
                self.services['data_fusion'].start_fusion()
                health_monitor.update_service_status('data_fusion', True)
                logger.info("✓ Data fusion engine started")
            
            # Start API gateway (this will block)
            logger.info("Starting Edge API Gateway...")
            health_monitor.update_service_status('api_gateway', True)
            logger.info("✓ All services started successfully")
            logger.info("=" * 50)
            logger.info("EDGE TRAFFIC MONITORING SYSTEM READY")
            logger.info("API available at: http://localhost:5000")
            logger.info("Health check: http://localhost:5000/api/health")
            logger.info("=" * 50)
            
            # Start API gateway in separate thread so we can monitor
            def start_api_server():
                """Wrapper function to start API server with error handling"""
                try:
                    logger.info("🚀 API server thread starting...")
                    logger.info("📋 Starting Swagger API gateway server...")
                    self.services['api_gateway'].start_server()
                    logger.info("✅ API server started successfully")
                except Exception as e:
                    logger.error(f"❌ API server thread failed: {e}")
                    import traceback
                    logger.error(f"🔥 API server traceback: {traceback.format_exc()}")
            
            logger.info("🧵 Creating API server thread...")
            api_thread = threading.Thread(
                target=start_api_server,
                daemon=False,
                name="APIServerThread"
            )
            logger.info("🔄 Starting API server thread...")
            api_thread.start()
            logger.info("✅ API server thread launched successfully")
            
            # Give the API server a moment to start
            import time
            time.sleep(2)
            logger.info("🔍 Checking if API server thread is alive...")
            if api_thread.is_alive():
                logger.info("✅ API server thread is running")
            else:
                logger.error("❌ API server thread died immediately")
            
            # Keep main thread alive for monitoring
            self._monitoring_loop()
            
        except Exception as e:
            logger.error(f"Failed to start services: {e}")
            self.stop_all_services()
    
    def _monitoring_loop(self):
        """Main monitoring loop to check service health"""
        while self.is_running:
            try:
                # Update service health statuses
                health_monitor = self.services['health_monitor']
                
                # Check each service and update health monitor
                for service_name, service in self.services.items():
                    if service_name == 'health_monitor':
                        continue
                        
                    is_running = getattr(service, 'is_running', False)
                    health_monitor.update_service_status(service_name, is_running)
                
                # Log system health periodically
                if int(time.time()) % 60 == 0:  # Every minute
                    health_score = health_monitor.get_health_score()
                    metrics = health_monitor.get_system_metrics()
                    logger.info(f"System Health Score: {health_score}/100 - "
                              f"CPU: {metrics.get('cpu_percent', 0):.1f}% - "
                              f"Memory: {metrics.get('memory_percent', 0):.1f}% - "
                              f"Temp: {metrics.get('temperature', 0):.1f}°C")
                
                # Weather analysis integration
                self._update_weather_conditions()
                
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                time.sleep(10)
    
    def _update_weather_conditions(self):
        """Update weather conditions and adjust system parameters accordingly"""
        if not self.weather_analysis_enabled or not self.sky_analyzer:
            return
        
        try:
            # Get current frame from vehicle detection service if available
            current_frame = None
            if 'vehicle_detection' in self.services:
                vehicle_service = self.services['vehicle_detection']
                if hasattr(vehicle_service, 'get_current_frame'):
                    current_frame = vehicle_service.get_current_frame()
            
            if current_frame is not None:
                # Analyze sky conditions
                sky_result = self.sky_analyzer.analyze_sky_condition(current_frame)
                weather_metrics = self.system_status.get_weather_metrics(current_frame)
                
                # Store latest weather data for API access
                self._latest_weather_data = {
                    'sky_condition': sky_result,
                    'weather_metrics': weather_metrics,
                    'timestamp': sky_result.get('timestamp'),
                    'visibility_estimate': self.sky_analyzer.get_visibility_estimate(
                        sky_result.get('condition', 'unknown'),
                        sky_result.get('confidence', 0)
                    )
                }
                
                
                # Adjust detection sensitivity based on weather
                self._adjust_detection_sensitivity(sky_result)
                
                # Update vehicle detection service with weather context
                if 'vehicle_detection' in self.services:
                    vehicle_service = self.services['vehicle_detection']
                    if hasattr(vehicle_service, 'update_weather_context'):
                        vehicle_service.update_weather_context(self._latest_weather_data)
                
                # Log weather updates every 5 minutes
                current_time = time.time()
                if not hasattr(self, '_last_weather_log') or (current_time - self._last_weather_log) > 300:
                    logger.info(f"Weather Update: Sky={sky_result.get('condition', 'unknown')} "
                              f"(confidence: {sky_result.get('confidence', 0):.2f}), "
                              f"Visibility={self._latest_weather_data['visibility_estimate']}")
                    self._last_weather_log = current_time
                    
        except Exception as e:
            logger.warning(f"Weather analysis error: {e}")
    
    def _adjust_detection_sensitivity(self, sky_result):
        """Adjust vehicle detection sensitivity based on weather conditions"""
        if 'vehicle_detection' not in self.services:
            return
        
        try:
            condition = sky_result.get('condition', 'unknown')
            confidence = sky_result.get('confidence', 0)
            
            # Calculate detection threshold based on weather
            if condition == 'clear' and confidence > 0.8:
                detection_threshold = 0.5  # Standard threshold for clear conditions
            elif condition == 'partly_cloudy':
                detection_threshold = 0.4  # Slightly lower for partly cloudy
            elif condition == 'cloudy' and confidence > 0.7:
                detection_threshold = 0.3  # Lower threshold for poor visibility
            else:
                detection_threshold = 0.4  # Default medium threshold
            
            # Apply threshold to vehicle detection service
            vehicle_service = self.services['vehicle_detection']
            if hasattr(vehicle_service, 'set_detection_threshold'):
                vehicle_service.set_detection_threshold(detection_threshold)
            
            # Store current detection parameters
            self._current_detection_params = {
                'threshold': detection_threshold,
                'weather_condition': condition,
                'weather_confidence': confidence,
                'adjusted_at': time.time()
            }
            
        except Exception as e:
            logger.warning(f"Error adjusting detection sensitivity: {e}")
    
    def get_current_weather_data(self):
        """Get the latest weather analysis data"""
        return getattr(self, '_latest_weather_data', {
            'sky_condition': {'condition': 'unavailable', 'confidence': 0},
            'weather_metrics': {},
            'visibility_estimate': 'unknown',
            'timestamp': None
        })
    
    def get_detection_parameters(self):
        """Get current detection parameters influenced by weather"""
        return getattr(self, '_current_detection_params', {
            'threshold': 0.5,
            'weather_condition': 'unknown',
            'weather_confidence': 0,
            'adjusted_at': None
        })
    
    def stop_all_services(self):
        """Stop all edge processing services"""
        logger.info("Stopping edge processing services...")
        self.is_running = False
        
        try:
            # Stop services in reverse order
            if 'api_gateway' in self.services:
                logger.info("Stopping API gateway...")
                self.services['api_gateway'].stop_server()
            
            if 'data_fusion' in self.services:
                logger.info("Stopping data fusion engine...")
                self.services['data_fusion'].stop_fusion()
            
            if 'speed_analysis' in self.services:
                logger.info("Stopping speed analysis service...")
                self.services['speed_analysis'].stop_analysis()
            
            if 'vehicle_detection' in self.services:
                logger.info("Stopping vehicle detection service...")
                self.services['vehicle_detection'].stop_detection()
            
            if 'health_monitor' in self.services:
                logger.info("Stopping system health monitor...")
                self.services['health_monitor'].stop_monitoring()
            
            logger.info("All services stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping services: {e}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.stop_all_services()
        sys.exit(0)
    
    def get_system_status(self):
        """Get overall system status"""
        if 'health_monitor' in self.services:
            return {
                'system_metrics': self.services['health_monitor'].get_system_metrics(),
                'service_statuses': self.services['health_monitor'].get_service_statuses(),
                'health_score': self.services['health_monitor'].get_health_score(),
                'recent_alerts': self.services['health_monitor'].get_recent_alerts(30)
            }
        return {}

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Raspberry Pi Edge Traffic Monitoring System')
    parser.add_argument('--api-only', action='store_true', help='Run API server only (no sensors)')
    parser.add_argument('--no-weather', action='store_true', help='Disable weather analysis')
    parser.add_argument('--weather-only', action='store_true', help='Test weather analysis only')
    args = parser.parse_args()
    
    if args.weather_only:
        # Weather analysis test mode
        logger.info("Starting weather analysis test mode")
        logger.info("=" * 60)
        
        if not WEATHER_ANALYSIS_AVAILABLE:
            logger.error("Weather analysis modules not available!")
            return
        
        try:
            # Run standalone weather test
            import subprocess
            import sys
            test_script_path = Path(__file__).parent / "test_sky_analysis.py"
            subprocess.run([sys.executable, str(test_script_path), "--mode", "camera"])
        except Exception as e:
            logger.error(f"Weather test error: {e}")
        return
    
    if args.api_only:
        # API-only mode for local testing
        logger.info("Starting API-only mode for local testing")
        logger.info("=" * 60)
        
        # Initialize only health monitor and API
        health_monitor = SystemHealthMonitor(update_interval=10.0)
        api_gateway = EdgeAPIGateway(host='0.0.0.0', port=5000)
        api_gateway.set_services(system_health=health_monitor)
        
        # Start health monitor
        health_monitor.start_monitoring()
        
        try:
            # Start API server (this will block)
            logger.info("API available at: http://0.0.0.0:5000")
            logger.info("Health check: http://0.0.0.0:5000/api/health")
            api_gateway.start_server()
        except KeyboardInterrupt:
            logger.info("Shutdown requested by user")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        finally:
            health_monitor.stop_monitoring()
        return
    
    # Full orchestrator mode
    logger.info("Starting Raspberry Pi 5 Edge ML Traffic Monitoring System")
    logger.info("=" * 60)
    
    # Create orchestrator with weather analysis setting
    weather_enabled = not args.no_weather
    orchestrator = EdgeOrchestrator(sensors_enabled=True, weather_analysis_enabled=weather_enabled)
    
    try:
        orchestrator.start_all_services()
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        orchestrator.stop_all_services()

if __name__ == "__main__":
    main()
