#!/usr/bin/env python3
"""
Test script for the modernized API with best practices architecture
"""

import sys
import logging
from datetime import datetime
import requests
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_api_endpoints(base_url="http://100.121.231.16:5000"):
    """Test the main API endpoints with the new service layer"""
    
    logger.info(f"Testing API endpoints at {base_url}")
    
    endpoints_to_test = [
        {
            'name': 'System Health',
            'path': '/api/system/health',
            'method': 'GET'
        },
        {
            'name': 'Vehicle Detections',
            'path': '/api/detections?seconds=3600',
            'method': 'GET'
        },
        {
            'name': 'Speed Analysis', 
            'path': '/api/speeds?seconds=3600',
            'method': 'GET'
        },
        {
            'name': 'Traffic Analytics',
            'path': '/api/analytics?period=hour',
            'method': 'GET'
        },
        {
            'name': 'Swagger Documentation',
            'path': '/swagger',
            'method': 'GET'
        }
    ]
    
    results = {}
    
    for endpoint in endpoints_to_test:
        name = endpoint['name']
        url = f"{base_url}{endpoint['path']}"
        
        try:
            logger.info(f"Testing {name}: {url}")
            
            start_time = time.time()
            response = requests.get(url, timeout=10)
            response_time = time.time() - start_time
            
            results[name] = {
                'url': url,
                'status_code': response.status_code,
                'response_time': round(response_time, 3),
                'success': response.status_code == 200
            }
            
            if response.status_code == 200:
                logger.info(f"✅ {name} - Status: {response.status_code}, Time: {response_time:.3f}s")
                
                # Log response size and basic structure
                try:
                    if 'application/json' in response.headers.get('content-type', ''):
                        json_data = response.json()
                        if isinstance(json_data, dict):
                            logger.info(f"   Response keys: {list(json_data.keys())}")
                            if 'count' in json_data:
                                logger.info(f"   Count: {json_data['count']}")
                        elif isinstance(json_data, list):
                            logger.info(f"   Response list length: {len(json_data)}")
                    else:
                        logger.info(f"   Response size: {len(response.content)} bytes")
                except Exception as e:
                    logger.info(f"   Response parsing error: {e}")
                    
            else:
                logger.error(f"❌ {name} - Status: {response.status_code}, Time: {response_time:.3f}s")
                logger.error(f"   Error: {response.text[:200]}")
                
        except requests.exceptions.Timeout:
            logger.error(f"❌ {name} - Request timed out after 10 seconds")
            results[name] = {
                'url': url,
                'status_code': 'timeout',
                'response_time': 'timeout',
                'success': False
            }
            
        except requests.exceptions.ConnectionError:
            logger.error(f"❌ {name} - Connection error (API server not running?)")
            results[name] = {
                'url': url,
                'status_code': 'connection_error',
                'response_time': 'connection_error', 
                'success': False
            }
            
        except Exception as e:
            logger.error(f"❌ {name} - Unexpected error: {e}")
            results[name] = {
                'url': url,
                'status_code': 'error',
                'response_time': 'error',
                'success': False
            }
        
        # Small delay between requests
        time.sleep(0.5)
    
    # Print summary
    print("\n" + "="*60)
    print("API TEST SUMMARY")
    print("="*60)
    
    total_tests = len(results)
    successful_tests = sum(1 for r in results.values() if r['success'])
    
    for name, result in results.items():
        status_icon = "✅" if result['success'] else "❌"
        print(f"{status_icon} {name:<25} {result['status_code']:<15} {result['response_time']}s")
    
    print(f"\nSUCCESS RATE: {successful_tests}/{total_tests} ({successful_tests/total_tests*100:.1f}%)")
    
    if successful_tests == total_tests:
        print("🎉 All API endpoints are working correctly!")
    elif successful_tests > 0:
        print("⚠️  Some API endpoints have issues")
    else:
        print("🚨 API server appears to be down or unreachable")
    
    print(f"\nTest completed at {datetime.now().isoformat()}")
    return results


def test_radar_data_access():
    """Test direct Redis data access to verify radar stream processing"""
    logger.info("Testing radar data access...")
    
    try:
        import redis
        r = redis.Redis(host='100.121.231.16', port=6379, db=0, decode_responses=True)
        
        # Test Redis connection
        r.ping()
        logger.info("✅ Redis connection successful")
        
        # Check radar stream length
        try:
            stream_length = r.xlen('radar_data')
            logger.info(f"✅ Radar stream length: {stream_length:,} entries")
            
            if stream_length > 0:
                # Get latest entry
                latest_entries = r.xrevrange('radar_data', count=1)
                if latest_entries:
                    entry_id, fields = latest_entries[0]
                    logger.info(f"✅ Latest radar entry: {entry_id} -> {fields}")
                    
                # Get stream info
                info = r.xinfo_stream('radar_data')
                logger.info(f"✅ Radar stream info - Length: {info['length']}, Groups: {info['groups']}")
                
            else:
                logger.warning("⚠️  Radar stream is empty - no data being collected")
                
        except Exception as e:
            logger.error(f"❌ Radar stream access error: {e}")
            
        return True
        
    except ImportError:
        logger.error("❌ Redis module not available")
        return False
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        return False


def main():
    """Run all API tests"""
    print("Traffic Monitoring API Test Suite")
    print("=" * 50)
    
    # Test radar data access first
    redis_ok = test_radar_data_access()
    print()
    
    # Test API endpoints
    api_results = test_api_endpoints()
    
    # Overall assessment
    print("\n" + "="*60)
    print("OVERALL ASSESSMENT")
    print("="*60)
    
    if redis_ok and all(r['success'] for r in api_results.values()):
        print("🎉 EXCELLENT: All systems operational - best practices architecture working!")
        return 0
    elif redis_ok and any(r['success'] for r in api_results.values()):
        print("⚠️  GOOD: Core systems working, some API issues need attention")
        return 1
    elif redis_ok:
        print("🔧 PARTIAL: Data collection working, but API server needs fixing")
        return 2
    else:
        print("🚨 CRITICAL: Core data systems unavailable")
        return 3


if __name__ == '__main__':
    sys.exit(main())