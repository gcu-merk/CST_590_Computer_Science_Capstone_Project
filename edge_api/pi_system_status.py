import psutil
import platform
import socket
from datetime import datetime

class PiSystemStatus:
    """Collects system status info for Raspberry Pi"""
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