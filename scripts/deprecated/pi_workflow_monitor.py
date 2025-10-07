#!/usr/bin/env python3
"""
Raspberry Pi Vehicle Detection Workflow Monitor
Comprehensive end-to-end monitoring from radar detection to API output
Designed to run directly on the Pi
"""

import subprocess
import json
import time
import sqlite3
import redis
import requests
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import threading
import signal
import sys

@dataclass
class WorkflowStep:
    name: str
    status: str
    timestamp: Optional[str] = None
    details: Optional[str] = None
    error: Optional[str] = None

class WorkflowMonitor:
    def __init__(self):
        self.running = True
        self.redis_client = None
        self.last_radar_detection = None
        self.monitoring_correlation_id = None
        
        # Signal handlers for clean shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
        self.running = False
        
    def run_command(self, command: str) -> tuple[str, str, int]:
        """Execute shell command and return stdout, stderr, returncode"""
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            return result.stdout.strip(), result.stderr.strip(), result.returncode
        except subprocess.TimeoutExpired:
            return "", "Command timed out", -1
        except Exception as e:
            return "", f"Error: {str(e)}", -1
    
    def check_docker_containers(self) -> Dict[str, WorkflowStep]:
        """Check status of all Docker containers in the workflow"""
        steps = {}
        
        # Key containers for the workflow
        containers = {
            "redis": "Redis Message Broker",
            "vehicle-consolidator": "Vehicle Consolidator Service", 
            "database-persistence": "Database Persistence",
            "realtime-events-broadcaster": "Realtime Events Broadcaster",
            "traffic-monitor": "API Gateway",
            "radar-service": "Radar Service",
            "nginx-proxy": "Nginx Proxy"
        }
        
        stdout, stderr, returncode = self.run_command("docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}'")
        
        for container_name, display_name in containers.items():
            if container_name in stdout:
                # Extract status for this container
                for line in stdout.split('\n'):
                    if container_name in line:
                        if "healthy" in line:
                            steps[container_name] = WorkflowStep(
                                display_name, "✅ Healthy", 
                                datetime.now().strftime("%H:%M:%S")
                            )
                        elif "Up" in line:
                            steps[container_name] = WorkflowStep(
                                display_name, "🟡 Running (no health check)",
                                datetime.now().strftime("%H:%M:%S")
                            )
                        else:
                            steps[container_name] = WorkflowStep(
                                display_name, "❌ Unhealthy", 
                                datetime.now().strftime("%H:%M:%S"),
                                error=line
                            )
                        break
            else:
                steps[container_name] = WorkflowStep(
                    display_name, "❌ Not Running", 
                    datetime.now().strftime("%H:%M:%S")
                )
        
        return steps
    
    def check_camera_service(self) -> WorkflowStep:
        """Check status of the camera service running outside Docker"""
        stdout, stderr, returncode = self.run_command("systemctl is-active imx500-ai-capture")
        
        if returncode == 0 and stdout.strip() == "active":
            # Get more details about the service
            stdout2, _, _ = self.run_command("systemctl status imx500-ai-capture --no-pager -l")
            
            return WorkflowStep(
                "Camera Service (IMX500)", "✅ Active",
                datetime.now().strftime("%H:%M:%S"),
                details="Running outside Docker as systemd service"
            )
        else:
            return WorkflowStep(
                "Camera Service (IMX500)", "❌ Inactive",
                datetime.now().strftime("%H:%M:%S"),
                error=f"Status: {stdout}, Error: {stderr}"
            )
    
    def setup_redis_connection(self) -> WorkflowStep:
        """Setup Redis connection for monitoring messages"""
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
            self.redis_client.ping()
            
            return WorkflowStep(
                "Redis Connection", "✅ Connected",
                datetime.now().strftime("%H:%M:%S"),
                details="Ready to monitor message channels"
            )
        except Exception as e:
            return WorkflowStep(
                "Redis Connection", "❌ Failed",
                datetime.now().strftime("%H:%M:%S"),
                error=str(e)
            )
    
    def monitor_radar_detections(self) -> Optional[Dict]:
        """Monitor for new radar detections"""
        if not self.redis_client:
            return None
            
        try:
            # Check for recent radar detections in Redis
            messages = self.redis_client.lrange("traffic:radar", 0, 4)  # Get last 5 messages
            
            if messages:
                latest_message = json.loads(messages[0])
                correlation_id = latest_message.get('correlation_id')
                
                # Check if this is a new detection
                if correlation_id != self.last_radar_detection:
                    self.last_radar_detection = correlation_id
                    self.monitoring_correlation_id = correlation_id
                    
                    return {
                        'correlation_id': correlation_id,
                        'timestamp': latest_message.get('timestamp'),
                        'speed_mph': latest_message.get('speed_mph'),
                        'direction': latest_message.get('direction'),
                        'message': f"New radar detection: {latest_message.get('speed_mph')} mph {latest_message.get('direction')}"
                    }
        except Exception as e:
            print(f"Error monitoring radar: {e}")
            
        return None
    
    def monitor_camera_requests(self) -> Optional[Dict]:
        """Monitor camera request/response handshake"""
        if not self.redis_client or not self.monitoring_correlation_id:
            return None
            
        try:
            # Check camera_requests channel for our correlation ID
            messages = self.redis_client.lrange("camera_requests", 0, 9)  # Last 10 requests
            
            for message in messages:
                try:
                    msg_data = json.loads(message)
                    if msg_data.get('correlation_id') == self.monitoring_correlation_id:
                        return {
                            'correlation_id': self.monitoring_correlation_id,
                            'timestamp': msg_data.get('timestamp'),
                            'message': f"Camera request sent for correlation {self.monitoring_correlation_id}"
                        }
                except json.JSONDecodeError:
                    continue
                    
        except Exception as e:
            print(f"Error monitoring camera requests: {e}")
            
        return None
    
    def monitor_camera_responses(self) -> Optional[Dict]:
        """Monitor camera responses"""
        if not self.redis_client or not self.monitoring_correlation_id:
            return None
            
        try:
            # Check camera_responses channel for our correlation ID
            messages = self.redis_client.lrange("camera_responses", 0, 9)  # Last 10 responses
            
            for message in messages:
                try:
                    msg_data = json.loads(message)
                    if msg_data.get('correlation_id') == self.monitoring_correlation_id:
                        return {
                            'correlation_id': self.monitoring_correlation_id,
                            'timestamp': msg_data.get('timestamp'),
                            'vehicle_types': msg_data.get('vehicle_types', []),
                            'message': f"Camera response: {msg_data.get('vehicle_types', 'unknown')}"
                        }
                except json.JSONDecodeError:
                    continue
                    
        except Exception as e:
            print(f"Error monitoring camera responses: {e}")
            
        return None
    
    def check_database_storage(self) -> Optional[Dict]:
        """Check if detection was stored in database"""
        if not self.monitoring_correlation_id:
            return None
            
        try:
            # Query database for our correlation ID
            stdout, stderr, returncode = self.run_command(
                f"docker exec database-persistence sqlite3 /app/data/traffic_data.db "
                f"\"SELECT t.correlation_id, t.timestamp, t.vehicle_type, r.speed_mph, r.direction "
                f"FROM traffic_detections t "
                f"LEFT JOIN radar_detections r ON t.correlation_id = r.correlation_id "
                f"WHERE t.correlation_id = '{self.monitoring_correlation_id}' "
                f"ORDER BY t.timestamp DESC LIMIT 1;\""
            )
            
            if returncode == 0 and stdout.strip():
                parts = stdout.split('|')
                if len(parts) >= 3:
                    return {
                        'correlation_id': parts[0],
                        'timestamp': parts[1],
                        'vehicle_type': parts[2],
                        'speed_mph': parts[3] if len(parts) > 3 else 'N/A',
                        'direction': parts[4] if len(parts) > 4 else 'N/A',
                        'message': f"Stored in DB: {parts[2]} at {parts[3]} mph"
                    }
                    
        except Exception as e:
            print(f"Error checking database: {e}")
            
        return None
    
    def check_api_endpoint(self) -> Optional[Dict]:
        """Check if detection is available via API"""
        if not self.monitoring_correlation_id:
            return None
            
        try:
            # Check API for recent detections
            response = requests.get("http://localhost/api/recent-detections", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Look for our correlation ID in recent detections
                for detection in data.get('detections', []):
                    if detection.get('correlation_id') == self.monitoring_correlation_id:
                        return {
                            'correlation_id': self.monitoring_correlation_id,
                            'timestamp': detection.get('timestamp'),
                            'vehicle_type': detection.get('vehicle_type'),
                            'api_response': True,
                            'message': f"Available via API: {detection.get('vehicle_type')}"
                        }
                        
                # If not found, still return API status
                return {
                    'api_status': 'healthy',
                    'total_recent': len(data.get('detections', [])),
                    'message': f"API healthy, {len(data.get('detections', []))} recent detections (monitoring ID not yet available)"
                }
            else:
                return {
                    'api_status': 'error',
                    'status_code': response.status_code,
                    'message': f"API error: {response.status_code}"
                }
                
        except Exception as e:
            return {
                'api_status': 'error',
                'error': str(e),
                'message': f"API check failed: {str(e)}"
            }
    
    def print_workflow_status(self, container_steps: Dict, camera_step: WorkflowStep, 
                            redis_step: WorkflowStep, current_monitoring: Dict):
        """Print comprehensive workflow status"""
        
        print("\n" + "="*80)
        print(f"🚗 Vehicle Detection Workflow Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        # System Health
        print("\n📊 SYSTEM HEALTH:")
        print(f"  {redis_step.status} {redis_step.name}")
        print(f"  {camera_step.status} {camera_step.name}")
        
        print("\n🐳 DOCKER CONTAINERS:")
        for container_name, step in container_steps.items():
            print(f"  {step.status} {step.name}")
            if step.error:
                print(f"    ❌ Error: {step.error}")
        
        # Current Monitoring
        if self.monitoring_correlation_id:
            print(f"\n🔍 TRACKING DETECTION: {self.monitoring_correlation_id}")
            
            # Show workflow steps for current detection
            workflow_steps = [
                ("Radar Detection", current_monitoring.get('radar')),
                ("Camera Request", current_monitoring.get('camera_request')),
                ("Camera Response", current_monitoring.get('camera_response')),
                ("Database Storage", current_monitoring.get('database')),
                ("API Availability", current_monitoring.get('api'))
            ]
            
            for step_name, step_data in workflow_steps:
                if step_data:
                    print(f"  ✅ {step_name}: {step_data.get('message', 'Completed')}")
                else:
                    print(f"  ⏳ {step_name}: Waiting...")
        else:
            print("\n🔍 MONITORING: Waiting for new radar detection...")
        
        # Recent Activity Summary
        try:
            stdout, _, _ = self.run_command(
                "docker exec database-persistence sqlite3 /app/data/traffic_data.db "
                "\"SELECT COUNT(*) FROM traffic_detections WHERE timestamp > datetime('now', '-1 hour');\""
            )
            
            if stdout.strip().isdigit():
                hourly_count = int(stdout.strip())
                print(f"\n📈 ACTIVITY: {hourly_count} detections in the last hour")
            
        except (subprocess.SubprocessError, ValueError) as e:
            pass
        
        print("\n" + "="*80)
    
    def run_continuous_monitor(self):
        """Run continuous monitoring loop"""
        print("🚀 Starting Vehicle Detection Workflow Monitor...")
        print("Press Ctrl+C to stop monitoring")
        
        while self.running:
            try:
                # Check system health
                container_steps = self.check_docker_containers()
                camera_step = self.check_camera_service()
                redis_step = self.setup_redis_connection()
                
                # Monitor current workflow
                current_monitoring = {}
                
                # Check for new radar detections
                radar_detection = self.monitor_radar_detections()
                if radar_detection:
                    current_monitoring['radar'] = radar_detection
                
                # If we're tracking a detection, monitor its progress
                if self.monitoring_correlation_id:
                    camera_request = self.monitor_camera_requests()
                    if camera_request:
                        current_monitoring['camera_request'] = camera_request
                    
                    camera_response = self.monitor_camera_responses()
                    if camera_response:
                        current_monitoring['camera_response'] = camera_response
                    
                    database_result = self.check_database_storage()
                    if database_result:
                        current_monitoring['database'] = database_result
                    
                    api_result = self.check_api_endpoint()
                    if api_result:
                        current_monitoring['api'] = api_result
                
                # Print status
                self.print_workflow_status(container_steps, camera_step, redis_step, current_monitoring)
                
                # Wait before next check
                time.sleep(5)
                
            except KeyboardInterrupt:
                self.running = False
                break
            except Exception as e:
                print(f"\n❌ Monitor error: {e}")
                time.sleep(5)
        
        print("\n👋 Workflow monitor stopped")

def main():
    """Main entry point"""
    monitor = WorkflowMonitor()
    monitor.run_continuous_monitor()

if __name__ == "__main__":
    main()