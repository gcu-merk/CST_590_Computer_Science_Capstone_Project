import psutil
import platform
import socket
from datetime import datetime
import sys
import os

# Add path for weather analysis module
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'edge_processing'))

try:
    from weather_analysis.sky_analyzer import SkyAnalyzer
    SKY_ANALYSIS_AVAILABLE = True
except ImportError:
    SKY_ANALYSIS_AVAILABLE = False

class PiSystemStatus:
    """Collects system status info for Raspberry Pi"""
    
    def __init__(self):
        self.sky_analyzer = SkyAnalyzer() if SKY_ANALYSIS_AVAILABLE else None
    def get_system_metrics(self):
        metrics = {}
        metrics['hostname'] = socket.gethostname()
        metrics['os'] = platform.platform()
        metrics['cpu_percent'] = psutil.cpu_percent(interval=1)
        metrics['cpu_count'] = psutil.cpu_count()
        metrics['memory'] = {
            'total': psutil.virtual_memory().total,
            'available': psutil.virtual_memory().available,
            'used': psutil.virtual_memory().used,
            'percent': psutil.virtual_memory().percent
        }
        metrics['disk'] = {
            'total': psutil.disk_usage('/').total,
            'used': psutil.disk_usage('/').used,
            'free': psutil.disk_usage('/').free,
            'percent': psutil.disk_usage('/').percent
        }
        metrics['boot_time'] = datetime.fromtimestamp(psutil.boot_time()).isoformat()
        metrics['uptime_seconds'] = int(datetime.now().timestamp() - psutil.boot_time())
        return metrics
    
    def get_weather_metrics(self, camera_image=None):
        """Get weather-related metrics including sky condition analysis"""
        weather_metrics = {}
        
        # Basic system-based weather indicators
        weather_metrics['timestamp'] = datetime.now().isoformat()
        
        # Sky condition analysis if camera image provided
        if camera_image is not None and self.sky_analyzer:
            try:
                sky_analysis = self.sky_analyzer.analyze_sky_condition(camera_image)
                weather_metrics['sky_condition'] = sky_analysis
                weather_metrics['visibility_estimate'] = self.sky_analyzer.get_visibility_estimate(
                    sky_analysis['condition'], sky_analysis['confidence']
                )
            except Exception as e:
                weather_metrics['sky_condition'] = {
                    'condition': 'unknown',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
        else:
            weather_metrics['sky_condition'] = {
                'condition': 'unavailable',
                'reason': 'No camera image provided or sky analyzer not available'
            }
        
        # Add system temperature (can indicate environmental conditions)
        try:
            # Try to read CPU temperature as environmental indicator
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                cpu_temp = float(f.read()) / 1000.0
            weather_metrics['system_temperature_c'] = cpu_temp
        except:
            weather_metrics['system_temperature_c'] = None
            
        return weather_metrics
    
    def get_enhanced_metrics(self, camera_image=None):
        """Get combined system and weather metrics"""
        metrics = self.get_system_metrics()
        weather_data = self.get_weather_metrics(camera_image)
        
        metrics['weather'] = weather_data
        return metrics