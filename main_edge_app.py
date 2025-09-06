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
from pathlib import Path

# Add edge processing modules to path
sys.path.append(str(Path(__file__).parent / "edge_processing"))
sys.path.append(str(Path(__file__).parent / "edge_api"))

from edge_processing.vehicle_detection.vehicle_detection_service import VehicleDetectionService
from edge_processing.speed_analysis.speed_analysis_service import SpeedAnalysisService
from edge_processing.data_fusion.data_fusion_engine import DataFusionEngine
from edge_processing.system_health.system_health_monitor import SystemHealthMonitor
from edge_api.edge_api_gateway import EdgeAPIGateway

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EdgeOrchestrator:
    """
    Main orchestrator for all edge processing services
    """
    
    def __init__(self, sensors_enabled=True):
        self.services = {}
        self.is_running = False
        self.sensors_enabled = sensors_enabled
        
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
                self.services['vehicle_detection'] = VehicleDetectionService(
                    camera_index=0,  # Sony IMX500 AI Camera
                    model_path=None  # Use default model
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
            
            # Set service references in API gateway
            self.services['api_gateway'].set_services(
                vehicle_detection=self.services.get('vehicle_detection'),
                speed_analysis=self.services.get('speed_analysis'),
                data_fusion=self.services.get('data_fusion'),
                system_health=self.services['health_monitor']
            )
            
            logger.info("All services initialized successfully")
            
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
            api_thread = threading.Thread(
                target=self.services['api_gateway'].start_server,
                daemon=True
            )
            api_thread.start()
            
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
                
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                time.sleep(10)
    
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
    logger.info("Starting Raspberry Pi 5 Edge ML Traffic Monitoring System")
    logger.info("=" * 60)
    
    orchestrator = EdgeOrchestrator(sensors_enabled=False)
    
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
