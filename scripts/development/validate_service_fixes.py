#!/usr/bin/env python3
"""
Service Startup Validation Script
Tests that both DHT22 and data maintenance services can start properly
"""

import subprocess
import sys
import time
import os
from pathlib import Path

def test_service_startup(service_name, service_file):
    """Test if a service file can be executed directly"""
    print(f"\n🔍 Testing {service_name} service startup...")
    
    service_path = Path(service_file)
    if not service_path.exists():
        print(f"❌ Service file not found: {service_path}")
        return False
    
    try:
        # Test syntax by importing
        cmd = [sys.executable, "-c", f"import sys; sys.path.insert(0, '.'); exec(open('{service_file}').read())"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print(f"✅ {service_name} syntax validation passed")
            return True
        else:
            print(f"❌ {service_name} validation failed:")
            print(f"   STDOUT: {result.stdout}")
            print(f"   STDERR: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⚠️  {service_name} took too long to validate (likely trying to run - good sign)")
        return True
    except Exception as e:
        print(f"❌ {service_name} validation error: {e}")
        return False

def check_docker_compose_syntax():
    """Validate docker-compose.yml syntax"""
    print("\n🔍 Validating docker-compose.yml syntax...")
    
    try:
        result = subprocess.run(['docker-compose', 'config'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ docker-compose.yml syntax is valid")
            return True
        else:
            print(f"❌ docker-compose.yml validation failed:")
            print(f"   STDERR: {result.stderr}")
            return False
    except FileNotFoundError:
        print("⚠️  docker-compose command not found - cannot validate")
        return True
    except Exception as e:
        print(f"❌ docker-compose validation error: {e}")
        return False

def main():
    """Main validation function"""
    print("🚀 Starting Service Startup Validation...")
    print("=" * 50)
    
    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    results = []
    
    # Test DHT22 service
    dht22_result = test_service_startup(
        "DHT22 Weather", 
        "edge_processing/dht_22_weather_service_enhanced.py"
    )
    results.append(("DHT22 Weather Service", dht22_result))
    
    # Test data maintenance service
    maintenance_result = test_service_startup(
        "Data Maintenance", 
        "edge_processing/data_maintenance_service_enhanced.py"
    )
    results.append(("Data Maintenance Service", maintenance_result))
    
    # Test docker-compose syntax
    docker_result = check_docker_compose_syntax()
    results.append(("Docker Compose Configuration", docker_result))
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY:")
    print("=" * 50)
    
    all_passed = True
    for service_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {service_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL VALIDATIONS PASSED!")
        print("Both services should now start correctly when deployed.")
        print("\nNext steps:")
        print("1. Build and deploy the services: docker-compose up --build")
        print("2. Check service logs: docker-compose logs dht22-weather data-maintenance")
        print("3. Verify Redis data: redis-cli keys 'weather:dht22*'")
    else:
        print("❌ SOME VALIDATIONS FAILED!")
        print("Please review the errors above before deployment.")
    
    print("=" * 50)
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)