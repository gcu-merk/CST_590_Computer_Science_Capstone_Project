"""
Edge Processing Package
Core edge processing services for the Raspberry Pi 5 Traffic Monitoring System
"""

__version__ = "1.0.0"
__author__ = "Traffic Monitoring Team"

# Import main services
from .vehicle_detection.vehicle_detection_service import VehicleDetectionService
from .speed_analysis.speed_analysis_service import SpeedAnalysisService, OPS243CRadar
from .data_fusion.data_fusion_engine import DataFusionEngine
from .system_health.system_health_monitor import SystemHealthMonitor

# Define available exports
__all__ = [
    'VehicleDetectionService',
    'SpeedAnalysisService', 
    'OPS243CRadar',
    'DataFusionEngine',
    'SystemHealthMonitor'
]
