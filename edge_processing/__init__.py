"""
Edge Processing Package
Core edge processing services for the Raspberry Pi 5 Traffic Monitoring System
"""

__version__ = "1.0.0"
__author__ = "Traffic Monitoring Team"

# Import main services with conditional imports to handle missing dependencies
from .vehicle_detection.vehicle_detection_service import VehicleDetectionService

# Optional imports - fail gracefully if dependencies missing
try:
    from .speed_analysis.speed_analysis_service import SpeedAnalysisService, OPS243CRadar
except ImportError:
    SpeedAnalysisService = None
    OPS243CRadar = None

try:
    from .data_fusion.data_fusion_engine import DataFusionEngine
except ImportError:
    DataFusionEngine = None

try:
    from .system_health.system_health_monitor import SystemHealthMonitor
except ImportError:
    SystemHealthMonitor = None

# Define available exports
__all__ = [
    'VehicleDetectionService',
    'SpeedAnalysisService', 
    'OPS243CRadar',
    'DataFusionEngine',
    'SystemHealthMonitor'
]
