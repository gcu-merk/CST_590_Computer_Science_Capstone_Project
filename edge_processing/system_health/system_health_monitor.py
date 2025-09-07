#!/usr/bin/env python3
"""
System Health Monitor
Monitors system performance, hardware status, and service health
Optimized for Raspberry Pi 5 with GPU monitoring
"""

import psutil
import time
import logging
import threading
import json
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from collections import deque

# Try to import GPU monitoring
try:
    import gpustat
    GPU_MONITORING_AVAILABLE = True
except ImportError:
    GPU_MONITORING_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """System performance metrics including GPU monitoring"""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    temperature: Optional[float] = None
    gpu_temp: Optional[float] = None
    network_bytes_sent: int = 0
    network_bytes_recv: int = 0
    gpu_usage: Optional[float] = None  # GPU utilization percentage
    gpu_memory: Optional[float] = None  # GPU memory usage percentage

@dataclass
class ServiceStatus:
    """Individual service status"""
    name: str
    is_running: bool
    last_update: float
    error_count: int = 0
    performance_metrics: Dict = field(default_factory=dict)

class SystemHealthMonitor:
    """
    Comprehensive system health monitoring for Raspberry Pi 5
    """
    
    def __init__(self, update_interval=10.0):
        self.update_interval = update_interval
        self.is_running = False
        
        # Metrics storage
        self.metrics_history = deque(maxlen=360)  # 1 hour at 10s intervals
        self.service_statuses = {}
        
        # Thresholds for alerts
        self.cpu_threshold = 80.0  # percent
        self.memory_threshold = 85.0  # percent
        self.disk_threshold = 90.0  # percent
        self.temp_threshold = 70.0  # Celsius
        
        # Alert tracking
        self.alerts = deque(maxlen=100)
        self.alert_cooldown = {}  # Alert type -> last alert time
        
    def start_monitoring(self):
        """Start system health monitoring"""
        self.is_running = True
        monitor_thread = threading.Thread(target=self._monitoring_loop)
        monitor_thread.daemon = True
        monitor_thread.start()
        logger.info("System health monitoring started")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_running:
            try:
                # Collect system metrics
                metrics = self._collect_system_metrics()
                self.metrics_history.append(metrics)
                
                # Check for alerts
                self._check_system_alerts(metrics)
                
                # Log periodic status
                if len(self.metrics_history) % 6 == 0:  # Every minute
                    self._log_system_status(metrics)
                
                time.sleep(self.update_interval)
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                time.sleep(self.update_interval)
    
    def _collect_system_metrics(self):
        """Collect current system metrics including GPU when available"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage (all mounted disks)
            disk_info = self._get_all_disk_info()
            disk_percent = disk_info.get('/', {}).get('percent', 0)
            
            # Network I/O
            network = psutil.net_io_counters()
            
            # Temperature (Raspberry Pi specific)
            temperature = self._get_cpu_temperature()
            gpu_temp = self._get_gpu_temperature()
            
            # GPU metrics (if available)
            gpu_usage = self._get_gpu_usage()
            gpu_memory = self._get_gpu_memory()
            
            return SystemMetrics(
                timestamp=time.time(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_percent=disk_percent,
                temperature=temperature,
                gpu_temp=gpu_temp,
                network_bytes_sent=network.bytes_sent,
                network_bytes_recv=network.bytes_recv,
                gpu_usage=gpu_usage,
                gpu_memory=gpu_memory
            )
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return SystemMetrics(
                timestamp=time.time(),
                cpu_percent=0.0,
                memory_percent=0.0,
                disk_percent=0.0
            )
    
    def _get_all_disk_info(self):
        """Get information about all mounted disks"""
        disk_info = {}
        try:
            partitions = psutil.disk_partitions(all=True)
            for partition in partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_info[partition.mountpoint] = {
                        'device': partition.device,
                        'mountpoint': partition.mountpoint,
                        'fstype': partition.fstype,
                        'total_gb': round(usage.total / (1024**3), 1),
                        'used_gb': round(usage.used / (1024**3), 1),
                        'free_gb': round(usage.free / (1024**3), 1),
                        'percent': usage.percent
                    }
                except (PermissionError, OSError):
                    # Skip partitions we can't access
                    continue
        except Exception as e:
            logger.error(f"Error getting disk info: {e}")
        
        return disk_info
    
    def _get_cpu_temperature(self):
        """Get CPU temperature (Raspberry Pi specific)"""
        try:
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp = float(f.read().strip()) / 1000.0
                return temp
        except Exception:
            return None
    
    def _get_gpu_temperature(self):
        """Get GPU temperature (Raspberry Pi specific)"""
        try:
            import subprocess
            result = subprocess.run(['vcgencmd', 'measure_temp'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                temp_str = result.stdout.strip()
                # Extract temperature from "temp=XX.X'C"
                temp = float(temp_str.split('=')[1].split("'")[0])
                return temp
        except Exception:
            return None
    
    def _get_gpu_usage(self):
        """Get GPU usage percentage"""
        try:
            if GPU_MONITORING_AVAILABLE:
                gpu_stats = gpustat.GPUStatCollection.new_query()
                if gpu_stats.gpus:
                    # For Pi 5, typically one GPU
                    return gpu_stats.gpus[0].utilization
            
            # Fallback: try to read from Pi-specific location
            import subprocess
            result = subprocess.run(['vcgencmd', 'get_mem', 'gpu'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                # This gives GPU memory allocation, not usage
                # For actual usage, would need more sophisticated monitoring
                return None
                
        except Exception:
            return None
    
    def _get_gpu_memory(self):
        """Get GPU memory usage percentage"""
        try:
            if GPU_MONITORING_AVAILABLE:
                gpu_stats = gpustat.GPUStatCollection.new_query()
                if gpu_stats.gpus:
                    gpu = gpu_stats.gpus[0]
                    if gpu.memory_total > 0:
                        return (gpu.memory_used / gpu.memory_total) * 100
            
            # Fallback for Pi 5: GPU memory is shared with system
            # No separate GPU memory to monitor
            return None
            
        except Exception:
            return None
    
    def _check_system_alerts(self, metrics):
        """Check system metrics against thresholds and generate alerts"""
        current_time = time.time()
        
        # CPU alert
        if metrics.cpu_percent > self.cpu_threshold:
            self._create_alert('cpu_high', f"High CPU usage: {metrics.cpu_percent:.1f}%", current_time)
        
        # Memory alert
        if metrics.memory_percent > self.memory_threshold:
            self._create_alert('memory_high', f"High memory usage: {metrics.memory_percent:.1f}%", current_time)
        
        # Disk alert
        if metrics.disk_percent > self.disk_threshold:
            self._create_alert('disk_high', f"High disk usage: {metrics.disk_percent:.1f}%", current_time)
        
        # Temperature alert
        if metrics.temperature and metrics.temperature > self.temp_threshold:
            self._create_alert('temp_high', f"High CPU temperature: {metrics.temperature:.1f}°C", current_time)
    
    def _create_alert(self, alert_type, message, timestamp):
        """Create system alert with cooldown"""
        cooldown_period = 300  # 5 minutes
        
        if alert_type in self.alert_cooldown:
            if timestamp - self.alert_cooldown[alert_type] < cooldown_period:
                return  # Still in cooldown
        
        alert = {
            'type': alert_type,
            'message': message,
            'timestamp': timestamp,
            'datetime': datetime.fromtimestamp(timestamp).isoformat()
        }
        
        self.alerts.append(alert)
        self.alert_cooldown[alert_type] = timestamp
        logger.warning(f"SYSTEM ALERT: {message}")
    
    def _log_system_status(self, metrics):
        """Log periodic system status"""
        logger.info(f"System Status - CPU: {metrics.cpu_percent:.1f}%, "
                   f"Memory: {metrics.memory_percent:.1f}%, "
                   f"Disk: {metrics.disk_percent:.1f}%, "
                   f"Temp: {metrics.temperature:.1f}°C" if metrics.temperature else "Temp: N/A")
    
    def register_service(self, service_name, service_ref=None):
        """Register a service for health monitoring"""
        self.service_statuses[service_name] = ServiceStatus(
            name=service_name,
            is_running=False,
            last_update=time.time()
        )
        logger.info(f"Registered service for monitoring: {service_name}")
    
    def update_service_status(self, service_name, is_running, performance_data=None):
        """Update service status"""
        if service_name in self.service_statuses:
            status = self.service_statuses[service_name]
            status.is_running = is_running
            status.last_update = time.time()
            
            if performance_data:
                status.performance_metrics.update(performance_data)
    
    def report_service_error(self, service_name, error_message):
        """Report service error"""
        if service_name in self.service_statuses:
            status = self.service_statuses[service_name]
            status.error_count += 1
            
            logger.warning(f"Service error - {service_name}: {error_message}")
    
    def get_system_metrics(self):
        """Get current system metrics"""
        if not self.metrics_history:
            return {}
        
        latest = self.metrics_history[-1]
        
        return {
            'cpu_percent': latest.cpu_percent,
            'memory_percent': latest.memory_percent,
            'disk_percent': latest.disk_percent,
            'temperature': latest.temperature,
            'gpu_temperature': latest.gpu_temp,
            'timestamp': latest.timestamp,
            'uptime_seconds': time.time() - (self.metrics_history[0].timestamp if self.metrics_history else time.time()),
            'disk_info': self._get_all_disk_info()  # Add detailed disk information
        }
    
    def get_service_statuses(self):
        """Get all service statuses"""
        return {
            name: {
                'name': status.name,
                'is_running': status.is_running,
                'last_update': status.last_update,
                'error_count': status.error_count,
                'performance_metrics': status.performance_metrics
            }
            for name, status in self.service_statuses.items()
        }
    
    def get_recent_alerts(self, minutes=60):
        """Get alerts from the last N minutes"""
        cutoff_time = time.time() - (minutes * 60)
        return [
            alert for alert in self.alerts
            if alert['timestamp'] > cutoff_time
        ]
    
    def get_performance_summary(self, minutes=30):
        """Get performance summary for the last N minutes"""
        cutoff_time = time.time() - (minutes * 60)
        recent_metrics = [
            m for m in self.metrics_history
            if m.timestamp > cutoff_time
        ]
        
        if not recent_metrics:
            return {}
        
        return {
            'timespan_minutes': minutes,
            'sample_count': len(recent_metrics),
            'cpu': {
                'avg': sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics),
                'max': max(m.cpu_percent for m in recent_metrics),
                'min': min(m.cpu_percent for m in recent_metrics)
            },
            'memory': {
                'avg': sum(m.memory_percent for m in recent_metrics) / len(recent_metrics),
                'max': max(m.memory_percent for m in recent_metrics),
                'min': min(m.memory_percent for m in recent_metrics)
            },
            'temperature': {
                'avg': sum(m.temperature for m in recent_metrics if m.temperature) / len([m for m in recent_metrics if m.temperature]),
                'max': max(m.temperature for m in recent_metrics if m.temperature),
                'min': min(m.temperature for m in recent_metrics if m.temperature)
            } if any(m.temperature for m in recent_metrics) else None
        }
    
    def get_health_score(self):
        """Calculate overall system health score (0-100)"""
        if not self.metrics_history:
            return 0
        
        latest = self.metrics_history[-1]
        score = 100
        
        # Deduct points for high resource usage
        if latest.cpu_percent > 50:
            score -= (latest.cpu_percent - 50) * 0.5
        
        if latest.memory_percent > 60:
            score -= (latest.memory_percent - 60) * 0.5
        
        if latest.disk_percent > 70:
            score -= (latest.disk_percent - 70) * 0.3
        
        # Deduct points for high temperature
        if latest.temperature and latest.temperature > 50:
            score -= (latest.temperature - 50) * 1.0
        
        # Deduct points for service errors
        for status in self.service_statuses.values():
            if not status.is_running:
                score -= 10
            if status.error_count > 0:
                score -= min(status.error_count * 2, 20)
        
        # Deduct points for recent alerts
        recent_alerts = self.get_recent_alerts(30)
        score -= len(recent_alerts) * 5
        
        return max(0, min(100, score))
    
    def stop_monitoring(self):
        """Stop system health monitoring"""
        self.is_running = False
        logger.info("System health monitoring stopped")

if __name__ == "__main__":
    # Test the system health monitor
    monitor = SystemHealthMonitor(update_interval=5.0)
    
    try:
        monitor.start_monitoring()
        
        # Register some test services
        monitor.register_service("vehicle_detection")
        monitor.register_service("speed_analysis")
        
        # Run for a while
        time.sleep(60)
        
        # Print summary
        metrics = monitor.get_system_metrics()
        health_score = monitor.get_health_score()
        
        logger.info(f"System metrics: {metrics}")
        logger.info(f"Health score: {health_score}")
        
    finally:
        monitor.stop_monitoring()
