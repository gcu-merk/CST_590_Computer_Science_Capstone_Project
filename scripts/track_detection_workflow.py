#!/usr/bin/env python3
"""
Detection Workflow Tracker

This script tracks the complete workflow of vehicle detection from radar input
to final API output by analyzing logs from all services in the traffic monitoring system.

Workflow Steps Tracked:
1. Radar Service -> Detects vehicle and publishes to Redis
2. Vehicle Consolidator -> Receives radar data and requests camera processing
3. Camera Service -> Processes handshake request and captures/classifies vehicle
4. Database Persistence -> Stores correlated detection data
5. API -> Makes data available via endpoints

Author: GitHub Copilot
Date: September 29, 2025
"""

import subprocess
import json
import re
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time

class DetectionWorkflowTracker:
    def __init__(self, ssh_host: str = "merk@100.121.231.16"):
        self.ssh_host = ssh_host
        self.findings = []
        self.workflow_steps = {
            "radar_detection": {"status": "pending", "timestamp": None, "details": []},
            "consolidator_processing": {"status": "pending", "timestamp": None, "details": []},
            "camera_handshake_request": {"status": "pending", "timestamp": None, "details": []},
            "camera_processing": {"status": "pending", "timestamp": None, "details": []},
            "camera_handshake_response": {"status": "pending", "timestamp": None, "details": []},
            "database_storage": {"status": "pending", "timestamp": None, "details": []},
            "api_availability": {"status": "pending", "timestamp": None, "details": []}
        }
    
    def run_ssh_command(self, command: str) -> Tuple[str, int]:
        """Execute SSH command and return output and exit code"""
        try:
            full_command = f'ssh {self.ssh_host} "{command}"'
            result = subprocess.run(
                full_command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            return result.stdout.strip(), result.returncode
        except subprocess.TimeoutExpired:
            return "TIMEOUT", 1
        except Exception as e:
            return f"ERROR: {str(e)}", 1
    
    def log_finding(self, step: str, status: str, message: str, timestamp: str = None):
        """Log a finding for a workflow step"""
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        finding = {
            "step": step,
            "status": status,
            "timestamp": timestamp,
            "message": message
        }
        self.findings.append(finding)
        
        # Update workflow step status
        if step in self.workflow_steps:
            self.workflow_steps[step]["status"] = status
            self.workflow_steps[step]["timestamp"] = timestamp
            self.workflow_steps[step]["details"].append(message)
    
    def track_radar_service(self, since_minutes: int = 10) -> bool:
        """Track radar service detection"""
        print("🔍 Step 1: Checking Radar Service...")
        
        # Check if radar service container is running using simple grep
        output, exit_code = self.run_ssh_command("docker ps | grep radar-service")
        if exit_code != 0 or not output.strip():
            self.log_finding("radar_detection", "failed", f"Radar service container not running")
            return False
        
        # Check container health
        if "healthy" in output or "Up" in output:
            self.log_finding("radar_detection", "success", "Radar service container is running and healthy")
        else:
            self.log_finding("radar_detection", "warning", f"Radar service status: {output}")
        
        # Check radar service logs for recent activity
        command = "docker logs radar-service --tail 20"
        output, exit_code = self.run_ssh_command(command)
        
        if exit_code == 0 and output:
            lines = output.split('\n')
            detection_count = len([line for line in lines if any(keyword in line.lower() for keyword in ['detection', 'speed', 'direction', 'vehicle', 'radar', 'mph'])])
            
            if detection_count > 0:
                self.log_finding("radar_detection", "success", f"Found {detection_count} radar-related log entries")
                # Show recent radar activity
                for line in lines[-5:]:
                    if line.strip() and any(keyword in line.lower() for keyword in ['detection', 'speed', 'direction', 'vehicle', 'radar']):
                        self.log_finding("radar_detection", "info", f"Radar activity: {line.strip()[:100]}")
                return True
            else:
                self.log_finding("radar_detection", "warning", f"Radar service running but no recent detection activity found")
                # Show last few log lines anyway
                for line in lines[-3:]:
                    if line.strip():
                        self.log_finding("radar_detection", "info", f"Recent log: {line.strip()[:100]}")
                return False
        else:
            self.log_finding("radar_detection", "warning", f"Cannot access radar service logs")
            return False
    
    def track_consolidator_processing(self, since_minutes: int = 10) -> bool:
        """Track vehicle consolidator processing"""
        print("🔍 Step 2: Checking Vehicle Consolidator...")
        
        # Check consolidator container status using simple grep
        output, exit_code = self.run_ssh_command("docker ps | grep vehicle-consolidator")
        if exit_code != 0 or not output.strip():
            self.log_finding("consolidator_processing", "failed", "Vehicle consolidator container not running")
            return False
        
        # Check container health
        if "healthy" in output or "Up" in output:
            self.log_finding("consolidator_processing", "success", "Vehicle consolidator container is running and healthy")
        else:
            self.log_finding("consolidator_processing", "warning", f"Consolidator status: {output}")
        
        # Check consolidator logs for radar processing
        command = "docker logs vehicle-consolidator --tail 30"
        output, exit_code = self.run_ssh_command(command)
        
        if exit_code == 0:
            lines = output.split('\n')
            
            # Look for radar processing
            radar_processed = False
            errors = []
            handshake_requests = []
            nonetype_errors = []
            
            for line in lines:
                if "radar_detection_processed" in line:
                    radar_processed = True
                    self.log_finding("consolidator_processing", "success", "Radar detection processed by consolidator")
                
                if "Error" in line or "ERROR" in line:
                    errors.append(line.strip())
                    if "NoneType" in line:
                        nonetype_errors.append(line.strip())
                
                if "camera_request" in line.lower() or "handshake" in line.lower():
                    handshake_requests.append(line.strip())
                
                # Look for specific handshake protocol messages
                if "camera processing request" in line.lower() or "requesting camera" in line.lower():
                    self.log_finding("camera_handshake_request", "success", f"Camera request sent: {line.strip()[:100]}")
            
            # Log critical NoneType errors first
            if nonetype_errors:
                self.log_finding("consolidator_processing", "error", f"CRITICAL: {len(nonetype_errors)} NoneType errors preventing handshake protocol")
                for error in nonetype_errors[-2:]:  # Show last 2 NoneType errors
                    self.log_finding("consolidator_processing", "error", f"NoneType error: {error[:150]}")
            
            # Log other errors
            for error in [e for e in errors if "NoneType" not in e][-2:]:  # Last 2 non-NoneType errors
                self.log_finding("consolidator_processing", "error", f"Other error: {error[:150]}")
            
            # Log handshake requests if found
            if handshake_requests:
                self.log_finding("camera_handshake_request", "success", f"Found {len(handshake_requests)} camera handshake requests")
                for request in handshake_requests[-2:]:
                    self.log_finding("camera_handshake_request", "info", f"Request: {request[:100]}")
            else:
                self.log_finding("camera_handshake_request", "warning", "No camera handshake requests found in consolidator logs")
            
            # Determine success based on radar processing vs errors
            if radar_processed and len(nonetype_errors) == 0:
                return True
            elif radar_processed and len(nonetype_errors) > 0:
                self.log_finding("consolidator_processing", "warning", f"Radar processed but {len(nonetype_errors)} NoneType errors block handshake")
                return False
            elif len(nonetype_errors) > 0:
                self.log_finding("consolidator_processing", "failed", f"Consolidator has {len(nonetype_errors)} NoneType errors preventing processing")
                return False
            else:
                self.log_finding("consolidator_processing", "warning", "No recent radar processing activity found")
                return False
        else:
            self.log_finding("consolidator_processing", "failed", "Cannot access consolidator logs")
            return False
    
    def track_camera_service(self, since_minutes: int = 10) -> bool:
        """Track camera service handshake processing"""
        print("🔍 Step 3: Checking Camera Service...")
        
        # Check camera service status (this runs as systemd service, not Docker)
        output, exit_code = self.run_ssh_command("systemctl is-active imx500-ai-capture.service")
        if exit_code != 0 or "active" not in output:
            self.log_finding("camera_processing", "failed", f"Camera service not active: {output}")
            return False
        
        self.log_finding("camera_processing", "success", "Camera service (systemd) is active")
        
        # Check camera service mode and recent activity
        command = f"journalctl -u imx500-ai-capture.service --since '1 hour ago' --no-pager | grep -E '(Mode:|camera_requests|handshake|HANDSHAKE|RADAR-TRIGGERED)' | tail -10"
        output, exit_code = self.run_ssh_command(command)
        
        handshake_mode = False
        camera_requests_received = False
        
        if exit_code == 0 and output:
            for line in output.split('\n'):
                if line.strip():
                    if "HANDSHAKE-TRIGGERED" in line:
                        handshake_mode = True
                        self.log_finding("camera_processing", "success", "✅ Camera service running in HANDSHAKE mode")
                    elif "RADAR-TRIGGERED" in line and "traffic_events" in line:
                        self.log_finding("camera_processing", "error", "❌ Camera service still in old RADAR-TRIGGERED mode")
                    elif "camera_requests" in line.lower():
                        camera_requests_received = True
                        self.log_finding("camera_handshake_request", "success", f"Camera request activity: {line.strip()[:100]}")
                    elif "handshake" in line.lower():
                        self.log_finding("camera_processing", "info", f"Handshake activity: {line.strip()[:100]}")
        
        # Check for recent camera processing activity  
        command = f"journalctl -u imx500-ai-capture.service --since '{since_minutes} minutes ago' --no-pager | grep -E '(Processing|request|response|vehicle|classification)' | tail -10"
        output, exit_code = self.run_ssh_command(command)
        
        if exit_code == 0 and output:
            processing_lines = [line for line in output.split('\n') if line.strip()]
            if processing_lines:
                self.log_finding("camera_processing", "success", f"Found {len(processing_lines)} camera processing entries in last {since_minutes} minutes")
                
                for line in processing_lines[-3:]:
                    if line.strip():
                        self.log_finding("camera_processing", "info", f"Camera activity: {line.strip()[:120]}")
                        
                        # Look for successful vehicle classifications
                        if any(vehicle_type in line.lower() for vehicle_type in ['car', 'truck', 'motorcycle', 'bus', 'van']):
                            self.log_finding("camera_processing", "success", f"Vehicle classified: {line.strip()[:100]}")
            else:
                self.log_finding("camera_processing", "warning", f"No camera processing activity in last {since_minutes} minutes")
        
        # Check if camera is receiving handshake requests
        if handshake_mode and not camera_requests_received:
            self.log_finding("camera_handshake_request", "warning", "Camera in handshake mode but no requests received")
        elif not handshake_mode:
            self.log_finding("camera_processing", "failed", "Camera not in handshake mode - may be using old code")
        
        return handshake_mode
    
    def track_database_storage(self, since_minutes: int = 10) -> bool:
        """Track database storage of detections"""
        print("🔍 Step 4: Checking Database Storage...")
        
        # Check database container status using simple grep
        output, exit_code = self.run_ssh_command("docker ps | grep database-persistence")
        if exit_code != 0 or not output.strip():
            self.log_finding("database_storage", "failed", "Database persistence container not running")
            return False
        
        # Check container health
        if "healthy" in output or "Up" in output:
            self.log_finding("database_storage", "success", "Database persistence container is running and healthy")
        else:
            self.log_finding("database_storage", "warning", f"Database status: {output}")
        
        # Check recent detections in database
        sql_query = "SELECT COUNT(*) as recent_count FROM traffic_detections WHERE timestamp > strftime('%s', 'now', '-10 minutes');"
        command = f"docker exec database-persistence sqlite3 /app/data/traffic_data.db \"{sql_query}\""
        output, exit_code = self.run_ssh_command(command)
        
        if exit_code == 0:
            try:
                recent_count = int(output.strip())
                self.log_finding("database_storage", "success", f"Found {recent_count} detections in database from last 10 minutes")
                
                # Get latest detection details with vehicle classifications
                detail_query = "SELECT t.timestamp, c.vehicle_types, r.speed_mph, r.direction, datetime(t.timestamp, 'unixepoch', 'localtime') as readable_time FROM traffic_detections t LEFT JOIN camera_detections c ON t.id = c.detection_id LEFT JOIN radar_detections r ON t.id = r.detection_id ORDER BY t.timestamp DESC LIMIT 5;"
                command = f"docker exec database-persistence sqlite3 /app/data/traffic_data.db \"{detail_query}\""
                output, exit_code = self.run_ssh_command(command)
                
                if exit_code == 0 and output:
                    unknown_count = 0
                    classified_count = 0
                    
                    for line in output.split('\n'):
                        if line.strip():
                            parts = line.split('|')
                            if len(parts) >= 5:
                                timestamp, vehicle_types, speed, direction, readable_time = parts[0], parts[1], parts[2], parts[3], parts[4]
                                
                                # Count classifications
                                if vehicle_types and 'unknown' in vehicle_types.lower():
                                    unknown_count += 1
                                    self.log_finding("database_storage", "warning", f"UNKNOWN classification: {speed} mph {direction} at {readable_time}")
                                elif vehicle_types and vehicle_types != '[]':
                                    classified_count += 1
                                    self.log_finding("database_storage", "success", f"CLASSIFIED: {vehicle_types} at {speed} mph {direction} at {readable_time}")
                                else:
                                    self.log_finding("database_storage", "info", f"Detection: {speed} mph {direction} at {readable_time}")
                    
                    # Summary of classification success
                    if classified_count > 0:
                        self.log_finding("database_storage", "success", f"✅ {classified_count} properly classified detections found")
                    if unknown_count > 0:
                        self.log_finding("database_storage", "error", f"❌ {unknown_count} 'unknown' classifications indicate handshake protocol failure")
                
                return recent_count > 0
            except ValueError:
                self.log_finding("database_storage", "error", f"Invalid database response: {output}")
                return False
        else:
            self.log_finding("database_storage", "failed", f"Cannot query database: {output}")
            return False
    
    def track_api_availability(self) -> bool:
        """Track API availability of detection data"""
        print("🔍 Step 5: Checking API Availability...")
        
        # Check API container status using simple grep
        output, exit_code = self.run_ssh_command("docker ps | grep traffic-monitor")
        if exit_code != 0 or not output.strip():
            self.log_finding("api_availability", "failed", "Traffic monitor API container not running")
            return False
        
        # Check container health
        if "healthy" in output or "Up" in output:
            self.log_finding("api_availability", "success", "Traffic monitor API container is running and healthy")
        else:
            self.log_finding("api_availability", "warning", f"API status: {output}")
        
        # Test API health endpoint
        command = "curl -s --connect-timeout 5 http://localhost:5000/health"
        output, exit_code = self.run_ssh_command(command)
        
        if exit_code == 0 and "healthy" in output.lower():
            self.log_finding("api_availability", "success", "API health endpoint responding")
            
            # Test detections endpoint
            command = "curl -s --connect-timeout 5 http://localhost:5000/api/detections?limit=5"
            output, exit_code = self.run_ssh_command(command)
            
            if exit_code == 0:
                try:
                    data = json.loads(output)
                    if isinstance(data, list) and len(data) > 0:
                        self.log_finding("api_availability", "success", f"API returning {len(data)} recent detections")
                        
                        # Analyze detection quality
                        unknown_via_api = 0
                        classified_via_api = 0
                        
                        for detection in data[:3]:  # Check first 3
                            vehicle_type = detection.get('vehicle_types', 'missing')
                            speed = detection.get('speed_mph', 'unknown')
                            timestamp = detection.get('timestamp', 'unknown')
                            
                            if isinstance(vehicle_type, list) and len(vehicle_type) > 0:
                                if 'unknown' in str(vehicle_type[0]).lower():
                                    unknown_via_api += 1
                                    self.log_finding("api_availability", "warning", f"API shows UNKNOWN: {speed} mph at {timestamp}")
                                else:
                                    classified_via_api += 1
                                    self.log_finding("api_availability", "success", f"API shows CLASSIFIED: {vehicle_type} at {speed} mph")
                            else:
                                self.log_finding("api_availability", "info", f"API detection: {speed} mph at {timestamp}")
                        
                        # Summary
                        if classified_via_api > 0:
                            self.log_finding("api_availability", "success", f"✅ {classified_via_api} properly classified detections via API")
                        if unknown_via_api > 0:
                            self.log_finding("api_availability", "error", f"❌ {unknown_via_api} 'unknown' classifications via API indicate handshake failure")
                        
                        return True
                    else:
                        self.log_finding("api_availability", "warning", "API responding but no detection data available")
                        return False
                except json.JSONDecodeError:
                    self.log_finding("api_availability", "error", f"API returned invalid JSON: {output[:200]}")
                    return False
            else:
                self.log_finding("api_availability", "warning", f"API detections endpoint not responding: {output}")
                return False
        else:
            self.log_finding("api_availability", "failed", f"API health check failed: {output}")
            return False
    
    def check_redis_connectivity(self) -> bool:
        """Check Redis connectivity and channels"""
        print("🔍 Checking Redis Connectivity...")
        
        # Check Redis container status using simple grep
        output, exit_code = self.run_ssh_command("docker ps | grep redis")
        if exit_code != 0 or not output.strip():
            self.log_finding("redis_connectivity", "failed", "Redis container not running")
            return False
        
        # Check if Redis container is healthy
        if "healthy" in output or "Up" in output:
            self.log_finding("redis_connectivity", "success", "Redis container is running and healthy")
        else:
            self.log_finding("redis_connectivity", "warning", f"Redis container status unclear: {output}")
            return False
        
        # Test Redis ping
        command = "docker exec redis redis-cli ping"
        output, exit_code = self.run_ssh_command(command)
        
        if exit_code == 0 and "PONG" in output:
            self.log_finding("redis_connectivity", "success", "Redis responding to ping")
            
            # Check active channels
            command = "docker exec redis redis-cli pubsub channels"
            output, exit_code = self.run_ssh_command(command)
            
            if exit_code == 0:
                channels = output.split('\n') if output else []
                self.log_finding("redis_connectivity", "info", f"Active Redis channels: {', '.join(channels) if channels else 'none'}")
                
                # Check for expected channels
                expected_channels = ["traffic:radar", "camera_requests", "camera_responses"]
                for channel in expected_channels:
                    if channel in channels:
                        self.log_finding("redis_connectivity", "success", f"Channel '{channel}' is active")
                    else:
                        self.log_finding("redis_connectivity", "warning", f"Channel '{channel}' not found")
                
                return True
            else:
                self.log_finding("redis_connectivity", "warning", "Cannot check Redis channels")
                return False
        else:
            self.log_finding("redis_connectivity", "failed", f"Redis not responding: {output}")
            return False
    
    def run_full_tracking(self, since_minutes: int = 10) -> Dict:
        """Run complete workflow tracking"""
        print("🚗 Starting Detection Workflow Tracking...")
        print("=" * 50)
        
        start_time = datetime.now()
        
        # Check Redis connectivity first
        self.check_redis_connectivity()
        
        # Track each step of the workflow
        radar_ok = self.track_radar_service(since_minutes)
        consolidator_ok = self.track_consolidator_processing(since_minutes)
        camera_ok = self.track_camera_service(since_minutes)
        database_ok = self.track_database_storage(since_minutes)
        api_ok = self.track_api_availability()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Generate summary
        summary = {
            "tracking_duration_seconds": duration,
            "workflow_steps": self.workflow_steps,
            "findings": self.findings,
            "overall_status": self.get_overall_status(),
            "recommendations": self.get_recommendations()
        }
        
        return summary
    
    def get_overall_status(self) -> str:
        """Determine overall workflow status"""
        failed_steps = [step for step, data in self.workflow_steps.items() if data["status"] == "failed"]
        warning_steps = [step for step, data in self.workflow_steps.items() if data["status"] == "warning"]
        
        if failed_steps:
            return f"FAILED - Issues in: {', '.join(failed_steps)}"
        elif warning_steps:
            return f"WARNING - Concerns in: {', '.join(warning_steps)}"
        else:
            return "HEALTHY - All steps functioning"
    
    def get_recommendations(self) -> List[str]:
        """Generate recommendations based on findings"""
        recommendations = []
        
        # Check for common issues
        error_findings = [f for f in self.findings if f["status"] == "error"]
        failed_findings = [f for f in self.findings if f["status"] == "failed"]
        warning_findings = [f for f in self.findings if f["status"] == "warning"]
        
        # Check for specific issues
        nonetype_errors = [f for f in error_findings if "NoneType" in f["message"]]
        unknown_classifications = [f for f in error_findings + warning_findings if "unknown" in f["message"].lower() and "classification" in f["message"]]
        handshake_issues = [f for f in warning_findings if "handshake" in f["message"].lower()]
        
        # Prioritize recommendations
        if nonetype_errors:
            recommendations.append("🚨 CRITICAL: Fix NoneType errors in vehicle consolidator - this prevents handshake protocol from working")
            recommendations.append("Check consolidator code: radar data format may be incorrect or missing fields")
        
        if unknown_classifications:
            recommendations.append("⚠️  Vehicle classifications showing 'unknown' - handshake protocol not functioning properly")
        
        if handshake_issues:
            recommendations.append("🔄 Camera service in handshake mode but not receiving requests - check consolidator→camera communication")
        
        if any("not active" in f["message"] for f in failed_findings):
            recommendations.append("🔧 Restart failed services using systemctl or docker restart")
        
        if self.workflow_steps["camera_processing"]["status"] == "failed":
            recommendations.append("📸 Camera service needs to be updated to handshake protocol mode")
        
        if self.workflow_steps["consolidator_processing"]["status"] == "failed":
            recommendations.append("🐳 Vehicle consolidator container needs debugging - check Docker logs")
        
        # If no major issues, provide optimization suggestions
        if not nonetype_errors and not unknown_classifications:
            if any("healthy" in f["message"] for f in self.findings):
                recommendations.append("✅ System appears healthy - test with vehicle passage to verify handshake protocol")
            else:
                recommendations.append("🔍 Run additional diagnostics to identify performance bottlenecks")
        
        return recommendations if recommendations else ["🤔 No specific issues identified - system status unclear"]
    
    def print_report(self, summary: Dict):
        """Print formatted tracking report"""
        print("\n" + "=" * 60)
        print("🚗 DETECTION WORKFLOW TRACKING REPORT")
        print("=" * 60)
        
        print(f"\n📊 Overall Status: {summary['overall_status']}")
        print(f"⏱️  Tracking Duration: {summary['tracking_duration_seconds']:.2f} seconds")
        
        print(f"\n🔍 Workflow Steps:")
        for step, data in summary['workflow_steps'].items():
            status_emoji = {"success": "✅", "warning": "⚠️", "failed": "❌", "pending": "⏳"}
            emoji = status_emoji.get(data['status'], "❓")
            print(f"  {emoji} {step.replace('_', ' ').title()}: {data['status'].upper()}")
        
        print(f"\n📋 Detailed Findings ({len(summary['findings'])} total):")
        for finding in summary['findings']:
            status_emoji = {"success": "✅", "warning": "⚠️", "failed": "❌", "error": "🚨", "info": "ℹ️"}
            emoji = status_emoji.get(finding['status'], "❓")
            print(f"  {emoji} [{finding['step']}] {finding['message']}")
        
        print(f"\n💡 Recommendations:")
        for i, rec in enumerate(summary['recommendations'], 1):
            print(f"  {i}. {rec}")
        
        print("\n" + "=" * 60)


def main():
    """Main execution function"""
    if len(sys.argv) > 1:
        try:
            since_minutes = int(sys.argv[1])
        except ValueError:
            print("Usage: python track_detection_workflow.py [minutes_to_check]")
            sys.exit(1)
    else:
        since_minutes = 10
    
    tracker = DetectionWorkflowTracker()
    summary = tracker.run_full_tracking(since_minutes)
    tracker.print_report(summary)
    
    # Save detailed report to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"detection_workflow_report_{timestamp}.json"
    
    try:
        with open(report_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        print(f"\n📄 Detailed report saved to: {report_file}")
    except Exception as e:
        print(f"\n⚠️  Could not save report file: {e}")
    
    # Exit with error code if workflow failed
    if "FAILED" in summary['overall_status']:
        sys.exit(1)
    elif "WARNING" in summary['overall_status']:
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()