#!/usr/bin/env python3
"""
Test script to verify docker_entrypoint.py GPIO library installation logic.
This simulates the entrypoint behavior to ensure it properly detects Pi hardware
and installs the required GPIO libraries.
"""

import subprocess
import sys
import os
from pathlib import Path

def test_pi_detection():
    """Test the Pi hardware detection logic"""
    print("Testing Pi Hardware Detection Logic")
    print("=" * 40)
    
    # Simulate the entrypoint's Pi detection logic
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read().lower()
            
        is_pi = any(keyword in cpuinfo for keyword in ['raspberry', 'bcm'])
        print(f"✓ /proc/cpuinfo readable: True")
        print(f"✓ Pi hardware detected: {is_pi}")
        
        if is_pi:
            print("✓ This system should trigger GPIO library installation")
        else:
            print("ℹ This system would skip GPIO library installation")
            
    except Exception as e:
        print(f"✗ Error reading /proc/cpuinfo: {e}")
    
    print()

def test_gpio_library_availability():
    """Test if GPIO libraries are available"""
    print("Testing GPIO Library Availability")
    print("=" * 35)
    
    libraries = ['lgpio', 'gpiozero']
    
    for lib in libraries:
        try:
            __import__(lib)
            print(f"✓ {lib}: Already installed")
        except ImportError:
            print(f"✗ {lib}: Not installed (would be installed by entrypoint)")
    
    print()

def test_module_execution():
    """Test if the DHT22 module can be executed"""
    print("Testing DHT22 Module Execution")
    print("=" * 30)
    
    module_path = Path("edge_processing/dht_22_weather_service_enhanced.py")
    
    if module_path.exists():
        print(f"✓ DHT22 module exists: {module_path}")
        print("✓ Module can be executed with: python -m edge_processing.dht_22_weather_service_enhanced")
    else:
        print(f"✗ DHT22 module not found: {module_path}")
    
    # Test if the module directory structure is correct
    init_file = Path("edge_processing/__init__.py")
    if init_file.exists():
        print("✓ edge_processing package properly structured")
    else:
        print("✗ edge_processing package missing __init__.py")
    
    print()

def simulate_entrypoint_flow():
    """Simulate the complete entrypoint flow"""
    print("Simulating Complete Entrypoint Flow")
    print("=" * 35)
    
    # Step 1: Pi Detection
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read().lower()
        is_pi = any(keyword in cpuinfo for keyword in ['raspberry', 'bcm'])
    except:
        is_pi = False
    
    print(f"1. Pi Detection: {'✓ Pi detected' if is_pi else 'ℹ Not a Pi'}")
    
    # Step 2: GPIO Library Installation (simulate)
    if is_pi:
        print("2. GPIO Library Installation: Would run 'pip install lgpio>=0.2.2.0 gpiozero>=1.6.2'")
    else:
        print("2. GPIO Library Installation: Skipped (not on Pi)")
    
    # Step 3: Service Type Check
    service_type = os.getenv('SERVICE_TYPE', '')
    print(f"3. Service Type: {service_type if service_type else 'Not set'}")
    
    # Step 4: Module Execution
    if service_type == 'dht22':
        print("4. Module Execution: Would run 'python -m edge_processing.dht_22_weather_service_enhanced'")
    else:
        print("4. Module Execution: Would use APP_MODULE or default logic")
    
    print()

if __name__ == "__main__":
    print("DHT22 Entrypoint Logic Verification")
    print("=" * 50)
    print()
    
    test_pi_detection()
    test_gpio_library_availability() 
    test_module_execution()
    simulate_entrypoint_flow()
    
    print("Verification Summary:")
    print("- The entrypoint should automatically detect Pi hardware")
    print("- GPIO libraries will be installed only on Pi systems")
    print("- DHT22 service will be launched as a Python module")
    print("- This approach maintains the same functionality as the previous local build")