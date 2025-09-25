#!/usr/bin/env python3
"""
Docker Container Entry Point
Replaces shell scripts with native Python orchestration
Follows Docker best practices for container initialization
"""

import os
import sys
import time
import signal
import logging
import subprocess
import multiprocessing
from pathlib import Path
from typing import List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("docker-entrypoint")

class ContainerOrchestrator:
    """Manages container processes without external shell scripts"""
    
    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        self.running = True
        
        # Set up signal handlers
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)
    
    def _handle_shutdown(self, signum, frame):
        """Handle graceful shutdown"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        self._cleanup_processes()
        sys.exit(0)
    
    def _cleanup_processes(self):
        """Clean up all managed processes"""
        for process in self.processes:
            if process.poll() is None:
                logger.info(f"Terminating process {process.pid}")
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    logger.warning(f"Force killing process {process.pid}")
                    process.kill()
    
    def _ensure_directories(self):
        """Create required directories"""
        directories = [
            "/mnt/storage/logs/applications",
            "/mnt/storage/logs/maintenance", 
            "/mnt/storage/scripts",
            "/mnt/storage/data",
            "/mnt/storage/config"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            logger.info(f"Ensured directory: {directory}")
    
    def _install_runtime_packages(self):
        """Install hardware-specific packages at runtime on Pi"""
        logger.info("Installing runtime-specific packages...")
        
        # Check package availability flags from build time
        flags_dir = Path("/tmp/package-flags")
        
        # Packages that need to be installed on actual Pi hardware
        pi_packages = [
            "opencv-python>=4.5.0",
            "scikit-image>=0.19.0"
        ]
        
        # Only install Pi-specific GPIO packages if we're on Pi hardware
        try:
            # Check if we're on a Raspberry Pi
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
            if 'Raspberry Pi' in cpuinfo or 'BCM' in cpuinfo:
                logger.info("Detected Raspberry Pi hardware, installing GPIO packages...")
                
                # Install picamera2 if not available from build time
                if not (flags_dir / "picamera2-available").exists():
                    pi_packages.append("picamera2>=0.3.12")
                else:
                    logger.info("picamera2 already installed during build")
                
                # Add other Pi-specific packages
                pi_packages.extend([
                    "gpiozero>=1.6.2", 
                    "RPi.GPIO>=0.7.1",
                    "lgpio>=0.2.2.0",
                    "gpustat>=1.1.1"
                ])
        except FileNotFoundError:
            logger.info("Not running on Pi hardware, skipping GPIO packages")
        
        # Install packages with error handling
        for package in pi_packages:
            try:
                logger.info(f"Installing {package}...")
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install", "--no-cache-dir", package
                ], capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    logger.info(f"Successfully installed {package}")
                else:
                    logger.warning(f"Failed to install {package}: {result.stderr}")
            except subprocess.TimeoutExpired:
                logger.warning(f"Timeout installing {package}")
            except Exception as e:
                logger.warning(f"Error installing {package}: {e}")
    
    def _wait_for_dependencies(self):
        """Wait for required services to be available"""
        logger.info("Waiting for system initialization...")
        
        # Wait for Redis if required
        redis_host = os.getenv('REDIS_HOST', 'redis')
        if redis_host:
            max_attempts = 30
            for attempt in range(max_attempts):
                try:
                    import redis
                    r = redis.Redis(host=redis_host, port=6379, decode_responses=True)
                    r.ping()
                    logger.info("Redis connection established")
                    break
                except Exception as e:
                    if attempt < max_attempts - 1:
                        logger.info(f"Waiting for Redis... (attempt {attempt + 1}/{max_attempts})")
                        time.sleep(2)
                    else:
                        logger.warning("Redis not available, continuing without it")
    
    def start_maintenance_daemon(self) -> Optional[subprocess.Popen]:
        """Start maintenance daemon if needed"""
        if os.getenv('ENABLE_MAINTENANCE', 'false').lower() == 'true':
            logger.info("Starting maintenance daemon...")
            try:
                process = subprocess.Popen([
                    sys.executable, 
                    "/app/scripts/container-maintenance.py", 
                    "--daemon"
                ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                self.processes.append(process)
                logger.info(f"Maintenance daemon started with PID {process.pid}")
                return process
            except Exception as e:
                logger.error(f"Failed to start maintenance daemon: {e}")
                return None
        return None
    
    def start_main_application(self):
        """Start the main application"""
        app_module = os.getenv('APP_MODULE', 'main_edge_app')
        service_type = os.getenv('SERVICE_TYPE', 'main')
        
        logger.info(f"Starting {service_type} application: {app_module}")
        
        try:
            if service_type == 'api':
                # Start API service
                process = subprocess.Popen([
                    sys.executable, 
                    f"/app/edge_api/edge_api_gateway_enhanced.py"
                ])
            elif service_type == 'consolidator':
                # Start vehicle consolidator
                process = subprocess.Popen([
                    sys.executable, 
                    "-m", 
                    "edge_processing.vehicle_detection.vehicle_consolidator_service"
                ])
            elif service_type == 'persistence':
                # Start database persistence
                process = subprocess.Popen([
                    sys.executable, 
                    "-m", 
                    "edge_processing.data_persistence.database_persistence_service_simplified"
                ])
            elif service_type == 'radar':
                # Start radar service
                process = subprocess.Popen([
                    sys.executable, 
                    "/app/radar_service.py"
                ])
            else:
                # Start main edge application
                process = subprocess.Popen([
                    sys.executable, 
                    f"/app/{app_module}.py"
                ])
            
            self.processes.append(process)
            logger.info(f"Main application started with PID {process.pid}")
            return process
            
        except Exception as e:
            logger.error(f"Failed to start main application: {e}")
            raise
    
    def run(self):
        """Main orchestration logic"""
        try:
            logger.info("Container orchestrator starting...")
            
            # Initialize environment
            self._ensure_directories()
            self._install_runtime_packages()
            self._wait_for_dependencies()
            
            # Start maintenance daemon if enabled
            maintenance_process = self.start_maintenance_daemon()
            
            # Start main application
            main_process = self.start_main_application()
            
            # Wait for main process to complete
            if main_process:
                logger.info("Waiting for main application to complete...")
                while self.running:
                    if main_process.poll() is not None:
                        logger.info("Main application exited")
                        break
                    time.sleep(1)
            
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"Container orchestrator error: {e}")
            raise
        finally:
            self._cleanup_processes()

def main():
    """Entry point for Docker container"""
    # Set PYTHONPATH
    sys.path.insert(0, '/app')
    
    # Start orchestrator
    orchestrator = ContainerOrchestrator()
    orchestrator.run()

if __name__ == "__main__":
    main()