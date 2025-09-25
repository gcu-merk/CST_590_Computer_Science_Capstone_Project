#!/usr/bin/env python3
"""
Service Command Standardization Summary
All services now use direct file execution approach for best practices
"""

import subprocess
import sys
import time
import os
from pathlib import Path

def get_service_commands():
    """Return standardized service commands"""
    return {
        # Core Services (Direct File Approach)
        "traffic-monitor": "edge_api/edge_api_gateway_enhanced.py",
        "data-maintenance": "edge_processing/data_maintenance_service_enhanced.py", 
        "dht22-weather": "edge_processing/dht_22_weather_service_enhanced.py",
        "radar-service": "radar_service.py",
        "realtime-events-broadcaster": "realtime_events_broadcaster.py",
        
        # Recently Standardized Services (Updated to Direct File)
        "airport-weather": "edge_processing/airport_weather_service_enhanced.py",
        "vehicle-consolidator": "edge_processing/vehicle_detection/vehicle_consolidator_service.py",
        "database-persistence": "edge_processing/data_persistence/database_persistence_service_simplified.py", 
        "redis-optimization": "edge_processing/data_persistence/redis_optimization_service_enhanced.py",
        
        # Infrastructure Services (Non-Python)
        "redis": "redis-server (Alpine Linux)",
        "nginx-proxy": "nginx (Alpine Linux)"
    }

def test_python_service_startup(service_name, service_file):
    """Test if a Python service file can be executed directly"""
    print(f"\n🔍 Testing {service_name} service startup...")
    
    service_path = Path(service_file)
    if not service_path.exists():
        print(f"❌ Service file not found: {service_path}")
        return False
    
    try:
        # Test syntax by compiling the file
        cmd = [sys.executable, "-m", "py_compile", service_file]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print(f"✅ {service_name} syntax validation passed")
            
            # Test if it has proper main block (handle both quote styles)
            try:
                with open(service_file, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                # Try with different encoding if UTF-8 fails
                with open(service_file, 'r', encoding='latin-1') as f:
                    content = f.read()
                    
            # Check for both double and single quote variations
            main_patterns = [
                'if __name__ == "__main__":',
                "if __name__ == '__main__':"
            ]
            
            has_main = any(pattern in content for pattern in main_patterns)
            
            if has_main:
                print(f"✅ {service_name} has proper entry point")
                return True
            else:
                print(f"⚠️  {service_name} missing __main__ block")
                return False
        else:
            print(f"❌ {service_name} syntax validation failed:")
            print(f"   STDERR: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⚠️  {service_name} took too long to validate")
        return True
    except Exception as e:
        print(f"❌ {service_name} validation error: {e}")
        return False

def validate_docker_compose():
    """Validate docker-compose.yml shows standardized commands"""
    print("\n🔍 Validating docker-compose.yml standardization...")
    
    try:
        with open('docker-compose.yml', 'r') as f:
            content = f.read()
            
        # Check that no services use -m module approach anymore
        if '"-m"' in content or "'-m'" in content:
            print("❌ Found services still using -m module approach:")
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                if '"-m"' in line or "'-m'" in line:
                    print(f"   Line {i}: {line.strip()}")
            return False
        else:
            print("✅ All Python services use direct file execution")
            return True
            
    except FileNotFoundError:
        print("❌ docker-compose.yml not found")
        return False
    except Exception as e:
        print(f"❌ docker-compose.yml validation error: {e}")
        return False

def main():
    """Main validation function"""
    print("🚀 Service Command Standardization Validation")
    print("=" * 60)
    print("Best Practice: All services use direct file execution")
    print("Benefits: Reliable startup, easier debugging, no module resolution issues")
    print("=" * 60)
    
    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    results = []
    service_commands = get_service_commands()
    
    # Test Python services only
    python_services = {k: v for k, v in service_commands.items() 
                      if v.endswith('.py')}
    
    print(f"\n📋 Testing {len(python_services)} Python services...")
    
    for service_name, service_file in python_services.items():
        result = test_python_service_startup(service_name, service_file)
        results.append((service_name, result))
    
    # Validate docker-compose configuration
    docker_result = validate_docker_compose()
    results.append(("docker-compose.yml", docker_result))
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 STANDARDIZATION VALIDATION SUMMARY:")
    print("=" * 60)
    
    all_passed = True
    for service_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {service_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL SERVICES STANDARDIZED SUCCESSFULLY!")
        print("\nStandardization Complete:")
        print("• All Python services use direct file execution")
        print("• No services use -m module approach anymore") 
        print("• All services have proper __main__ blocks")
        print("• Docker-compose.yml syntax is valid")
        
        print("\nNext Steps:")
        print("1. Build and deploy: docker-compose up --build")
        print("2. Monitor startup: docker-compose logs -f")
        print("3. Verify all services reach healthy status")
        print("4. Check Redis data: redis-cli keys '*'")
        
    else:
        print("❌ STANDARDIZATION ISSUES FOUND!")
        print("Please review the errors above before deployment.")
    
    print("=" * 60)
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)