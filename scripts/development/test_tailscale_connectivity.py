#!/usr/bin/env python3
"""
Test Tailscale connectivity to Raspberry Pi
Quick verification that we can reach the Pi via Tailscale before deploying
"""

import sys
import socket
import time
import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TAILSCALE_IP = "100.121.231.16"
COMMON_PORTS = [22, 5000, 6379, 80]  # SSH, API, Redis, HTTP


def test_ping():
    """Test basic ping connectivity via Tailscale"""
    logger.info(f"Testing ping to Tailscale IP: {TAILSCALE_IP}")
    
    try:
        # Use ping command (cross-platform)
        cmd = ["ping", "-n", "3", TAILSCALE_IP] if sys.platform == "win32" else ["ping", "-c", "3", TAILSCALE_IP]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            logger.info("✅ Ping successful - Tailscale connectivity confirmed")
            return True
        else:
            logger.error(f"❌ Ping failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("❌ Ping timed out")
        return False
    except Exception as e:
        logger.error(f"❌ Ping error: {e}")
        return False


def test_port_connectivity(port, service_name):
    """Test if a specific port is reachable"""
    logger.info(f"Testing {service_name} (port {port})...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((TAILSCALE_IP, port))
        sock.close()
        
        if result == 0:
            logger.info(f"✅ {service_name} (port {port}) - reachable")
            return True
        else:
            logger.warning(f"⚠️  {service_name} (port {port}) - not reachable (service may be down)")
            return False
            
    except Exception as e:
        logger.error(f"❌ {service_name} (port {port}) - connection error: {e}")
        return False


def test_api_health():
    """Test API health endpoint if available"""
    try:
        import requests
        
        logger.info("Testing API health endpoint...")
        response = requests.get(f"http://{TAILSCALE_IP}:5000/api/system/health", timeout=10)
        
        if response.status_code == 200:
            logger.info("✅ API health check successful")
            logger.info(f"   Response: {response.json()}")
            return True
        else:
            logger.warning(f"⚠️  API health check returned status: {response.status_code}")
            return False
            
    except ImportError:
        logger.info("⚠️  Requests module not available - skipping API health test")
        return None
    except Exception as e:
        logger.warning(f"⚠️  API health check failed: {e}")
        return False


def main():
    """Run all connectivity tests"""
    print("Tailscale Pi Connectivity Test")
    print("=" * 50)
    print(f"Target: {TAILSCALE_IP}")
    print()
    
    # Test results
    results = {
        'ping': False,
        'ssh': False,
        'api': False,
        'redis': False,
        'api_health': None
    }
    
    # Basic ping test
    results['ping'] = test_ping()
    print()
    
    # Port connectivity tests
    port_tests = [
        (22, 'SSH', 'ssh'),
        (5000, 'API Server', 'api'),
        (6379, 'Redis', 'redis'),
    ]
    
    for port, name, key in port_tests:
        results[key] = test_port_connectivity(port, name)
        time.sleep(0.5)
    
    print()
    
    # API health test
    results['api_health'] = test_api_health()
    
    # Summary
    print("\n" + "=" * 50)
    print("CONNECTIVITY SUMMARY")
    print("=" * 50)
    
    status_icons = {True: "✅", False: "❌", None: "⚠️"}
    
    for test_name, result in results.items():
        icon = status_icons.get(result, "❓")
        status = "PASS" if result else ("FAIL" if result is False else "SKIP")
        print(f"{icon} {test_name.upper():<12} {status}")
    
    # Overall assessment
    critical_tests = ['ping', 'ssh']
    critical_passed = all(results[test] for test in critical_tests)
    
    print()
    if critical_passed:
        if results['api'] and results['api_health']:
            print("🎉 EXCELLENT: All systems reachable via Tailscale!")
            print("   Ready for CI/CD deployment and API testing")
            return 0
        elif results['api']:
            print("✅ GOOD: Pi reachable, API port open")
            print("   Ready for deployment - API may need to be started")
            return 0
        else:
            print("🔧 PARTIAL: Pi reachable via Tailscale")
            print("   SSH available for manual deployment if needed")
            return 1
    else:
        print("🚨 CRITICAL: Cannot reach Pi via Tailscale")
        print("   Check Tailscale status on both devices")
        return 2


if __name__ == '__main__':
    sys.exit(main())