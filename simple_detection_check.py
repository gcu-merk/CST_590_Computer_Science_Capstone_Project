#!/usr/bin/env python3
"""
Simple Vehicle Detection Status Check
Checks basic system health and recent detections
"""

import subprocess
import sys
import json
import socket
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def is_running_on_pi():
    """Check if script is running on the Pi"""
    try:
        hostname = socket.gethostname()
        return "raspberrypi" in hostname.lower() or "pi" in hostname.lower()
    except (OSError, socket.error) as e:
        logger.warning(f"Could not determine hostname: {e}")
        return False

def run_command(command):
    """Execute command directly or via SSH depending on where we're running"""
    if is_running_on_pi():
        # Running on Pi, execute directly
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            return result.stdout.strip(), result.stderr.strip(), result.returncode
        except subprocess.TimeoutExpired:
            return "", "Command timed out", -1
        except Exception as e:
            return "", f"Error: {str(e)}", -1
    else:
        # Running remotely, use SSH
        full_command = f"ssh merk@100.121.231.16 \"{command}\""
        try:
            result = subprocess.run(full_command, shell=True, capture_output=True, text=True, timeout=30)
            return result.stdout.strip(), result.stderr.strip(), result.returncode
        except subprocess.TimeoutExpired:
            return "", "Command timed out", -1
        except Exception as e:
            return "", f"Error: {str(e)}", -1

def check_containers():
    """Check if Docker containers are running"""
    logger.info("=== Container Status ===")
    
    # Check if docker-compose is running
    stdout, stderr, returncode = run_command("cd /home/merk && docker-compose ps")
    
    if returncode == 0 and stdout:
        logger.info("Docker Compose Status:")
        logger.info(stdout)
        
        # Also check individual containers
        containers = ["redis", "vehicle-consolidator", "realtime-events-broadcaster", "api-gateway"]
        
        for container in containers:
            if container in stdout and "Up" in stdout:
                logger.info(f"✅ {container}: Running")
            else:
                logger.warning(f"❌ {container}: Not found in compose output")
    else:
        logger.error(f"❌ Failed to check docker-compose: {stderr}")

def check_camera_service():
    """Check camera service status"""
    logger.info("=== Camera Service Status ===")
    
    stdout, stderr, returncode = run_command("systemctl is-active imx500-ai-capture")
    if stdout.strip() == "active":
        logger.info("✅ Camera service: Running")
    else:
        logger.warning(f"❌ Camera service: {stdout}")

def check_recent_detections():
    """Check for recent vehicle detections"""
    logger.info("=== Recent Detections (Last 2 Hours) ===")
    
    # Check radar detections using docker exec
    query = """
    SELECT COUNT(*) as count, 
           MIN(detected_at) as first_detection,
           MAX(detected_at) as last_detection
    FROM radar_detections 
    WHERE detected_at > datetime('now', '-2 hours');
    """
    
    stdout, stderr, returncode = run_command(f"cd /opt/vehicle-detection && docker-compose exec -T database-persistence sqlite3 /app/data/traffic_data.db \"{query}\"")
    
    if returncode == 0 and stdout:
        try:
            parts = stdout.split('|')
            count = parts[0]
            first = parts[1] if len(parts) > 1 and parts[1] else "None"
            last = parts[2] if len(parts) > 2 and parts[2] else "None"
            
            logger.info(f"Radar detections: {count}")
            if count != "0":
                logger.info(f"  First: {first}")
                logger.info(f"  Last: {last}")
        except (IndexError, ValueError) as e:
            logger.warning(f"Could not parse radar query result: {e}")
            logger.info(f"Radar query result: {stdout}")
    else:
        logger.error(f"❌ Failed to query radar detections: {stderr}")
    
    # Check traffic detections (final results)
    query2 = """
    SELECT COUNT(*) as count,
           vehicle_type,
           MIN(detected_at) as first_detection,
           MAX(detected_at) as last_detection
    FROM traffic_detections 
    WHERE detected_at > datetime('now', '-2 hours')
    GROUP BY vehicle_type;
    """
    
    stdout2, stderr2, returncode2 = run_command(f"cd /opt/vehicle-detection && docker-compose exec -T database-persistence sqlite3 /app/data/traffic_data.db \"{query2}\"")
    
    if returncode2 == 0 and stdout2:
        logger.info("\nFinal vehicle classifications:")
        if stdout2.strip():
            for line in stdout2.split('\n'):
                if line.strip():
                    try:
                        parts = line.split('|')
                        count = parts[0]
                        vehicle_type = parts[1] if len(parts) > 1 else "unknown"
                        first = parts[2] if len(parts) > 2 else "None"
                        last = parts[3] if len(parts) > 3 else "None"
                        
                        logger.info(f"  {vehicle_type}: {count} detections")
                        if count != "0":
                            logger.info(f"    First: {first}")
                            logger.info(f"    Last: {last}")
                    except (IndexError, ValueError) as e:
                        logger.warning(f"  Could not parse traffic detection line: {e}")
                        logger.info(f"  Raw: {line}")
        else:
            logger.info("  No detections in last 2 hours")
    else:
        logger.error(f"❌ Failed to query traffic detections: {stderr2}")

def check_logs():
    """Check recent logs for errors"""
    logger.info("=== Recent Log Errors ===")
    
    # Check consolidator logs using docker-compose
    stdout, stderr, returncode = run_command("cd /opt/vehicle-detection && docker-compose logs --tail 10 vehicle-consolidator 2>&1 | grep -i error")
    
    if stdout:
        logger.info("Consolidator errors:")
        for line in stdout.split('\n'):
            if line.strip():
                logger.error(f"  {line}")
    else:
        logger.info("✅ No recent consolidator errors found")
    
    # Also check for any recent logs
    stdout2, stderr2, returncode2 = run_command("cd /opt/vehicle-detection && docker-compose logs --tail 5 vehicle-consolidator")
    
    if stdout2:
        logger.info("\nLast 5 consolidator log lines:")
        for line in stdout2.split('\n'):
            if line.strip():
                logger.info(f"  {line}")

def main():
    logger.info("Vehicle Detection System - Simple Status Check")
    logger.info("=" * 50)
    logger.info(f"Check time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    check_containers()
    check_camera_service()
    check_recent_detections()
    check_logs()
    
    logger.info("Check complete!")

if __name__ == "__main__":
    main()