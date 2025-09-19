#!/usr/bin/env python3
"""
Simple maintenance status check script for health monitoring
Returns exit code 0 if maintenance service is healthy, 1 if not
"""

import sys
import subprocess
import json
import logging

def check_maintenance_status():
    """Check if maintenance service is running and healthy"""
    try:
        # Run the maintenance status command
        result = subprocess.run([
            'python3', '/app/scripts/container-maintenance.py', '--status'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            print(f"Maintenance script failed with exit code {result.returncode}")
            print(f"Error: {result.stderr}")
            return False
        
        # Parse the JSON output
        try:
            status = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            print(f"Failed to parse maintenance status JSON: {e}")
            return False
        
        # Check if the status looks healthy
        if 'health' not in status:
            print("No health information in maintenance status")
            return False
        
        health = status['health']
        
        # Check disk usage
        if 'disk_usage' in health:
            disk_usage = health['disk_usage']
            if disk_usage.get('used_percent', 0) > 95:
                print(f"Disk usage critical: {disk_usage.get('used_percent', 0)}%")
                return False
        
        # Check for emergency cleanup needs
        if health.get('needs_emergency_cleanup', False):
            print("Emergency cleanup needed")
            return False
        
        print("Maintenance service is healthy")
        return True
        
    except subprocess.TimeoutExpired:
        print("Maintenance status check timed out")
        return False
    except Exception as e:
        print(f"Error checking maintenance status: {e}")
        return False

def main():
    """Main function"""
    if check_maintenance_status():
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()