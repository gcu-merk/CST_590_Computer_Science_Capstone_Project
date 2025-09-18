#!/usr/bin/env python3
"""
Edge API Gateway
Flask-SocketIO server providing real-time API endpoints for the traffic monitoring system
"""

from flask import Flask, jsonify, request, send_file
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import time
import logging
import threading
import json
import os
import subprocess
import socket
import platform
import sys
from datetime import datetime
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EdgeAPIGateway:
    """
    Main API gateway for edge processing services
    Provides REST endpoints and WebSocket communication
    """
    
    def __init__(self, host='0.0.0.0', port=5000):
        self.host = host
        self.port = port
        
        # Initialize Flask app
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'traffic_monitoring_edge_api'
        
        # Enable CORS for cross-origin requests
        CORS(self.app)
        
        # Initialize SocketIO
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # Service references
        self.vehicle_detection_service = None
        self.speed_analysis_service = None
        self.data_fusion_engine = None
        self.system_health_monitor = None
        self.sky_analyzer = None
        self.system_status = None
        self.weather_storage = None
        
        # Runtime state
        self.is_running = False
        self.client_count = 0
        
        # Initialize Redis client with error handling
        self.redis_client = None
        try:
            import redis
            # Use Docker hostname for Redis if available
            redis_host = os.environ.get('REDIS_HOST', 'redis')
            self.redis_client = redis.Redis(host=redis_host, port=6379, db=0, decode_responses=True)
            # Test connection
            self.redis_client.ping()
            logger.info(f"Redis connection established to host: {redis_host}")
        except ImportError:
            logger.warning("Redis not available - weather:latest endpoint will not work")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e} - weather:latest endpoint will not work")
        
        # Setup routes
        self._setup_routes()
        self._setup_websocket_events()
    
    def set_services(self, vehicle_detection=None, speed_analysis=None, 
                    data_fusion=None, system_health=None, sky_analyzer=None, 
                    system_status=None, weather_storage=None):
        """Set references to edge processing services"""
        self.vehicle_detection_service = vehicle_detection
        self.speed_analysis_service = speed_analysis
        self.data_fusion_engine = data_fusion
        self.system_health_monitor = system_health
        self.sky_analyzer = sky_analyzer
        self.system_status = system_status
        self.weather_storage = weather_storage
    
    def _convert_performance_temps(self, perf_summary):
        """Convert temperature values in performance summary from Celsius to Fahrenheit"""
        try:
            # Check if perf_summary is a valid dictionary
            if not isinstance(perf_summary, dict):
                logger.warning(f"Performance summary is not a dictionary: {type(perf_summary)}")
                return perf_summary
            
            if not perf_summary or 'temperature' not in perf_summary or perf_summary['temperature'] is None:
                return perf_summary
            
            temp_data = perf_summary['temperature']
            
            # Check if temp_data is a valid dictionary
            if not isinstance(temp_data, dict):
                logger.warning(f"Temperature data is not a dictionary: {type(temp_data)}")
                return perf_summary
            
            # Check if required temperature keys exist
            required_keys = ['avg', 'max', 'min']
            if not all(key in temp_data for key in required_keys):
                logger.warning(f"Temperature data missing required keys: {temp_data.keys()}")
                return perf_summary
            
            converted = perf_summary.copy()
            converted['temperature'] = {
                'avg': round((temp_data['avg'] * 9/5) + 32, 1),
                'max': round((temp_data['max'] * 9/5) + 32, 1),
                'min': round((temp_data['min'] * 9/5) + 32, 1),
                'avg_celsius': temp_data['avg'],
                'max_celsius': temp_data['max'],
                'min_celsius': temp_data['min']
            }
            
            return converted
        except Exception as e:
            logger.error(f"Error converting performance temperatures: {e}")
            return perf_summary
    
    def _setup_routes(self):
        """Setup REST API routes"""
        
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """Enhanced system health check endpoint"""
            try:
                health_data = {
                    'status': 'healthy',
                    'timestamp': datetime.now().isoformat(),
                    'services': {
                        'vehicle_detection': self.vehicle_detection_service is not None,
                        'speed_analysis': self.speed_analysis_service is not None,
                        'data_fusion': self.data_fusion_engine is not None,
                        'system_health': self.system_health_monitor is not None,
                        'weather_analysis': self.sky_analyzer is not None,
                        'redis': self.redis_client is not None
                    },
                    'client_count': self.client_count
                }
                
                if self.system_health_monitor:
                    # Basic system metrics
                    try:
                        basic_metrics = self.system_health_monitor.get_system_metrics()
                        
                        # Convert temperature from Celsius to Fahrenheit
                        if isinstance(basic_metrics, dict) and 'temperature' in basic_metrics and basic_metrics['temperature'] is not None:
                            celsius_temp = basic_metrics['temperature']
                            if isinstance(celsius_temp, (int, float)):
                                fahrenheit_temp = round((celsius_temp * 9/5) + 32, 1)
                                basic_metrics['temperature'] = fahrenheit_temp  # Replace with Fahrenheit
                                basic_metrics['temperature_celsius'] = celsius_temp  # Keep Celsius for reference
                        
                        health_data.update(basic_metrics if isinstance(basic_metrics, dict) else {})
                        
                        # Enhanced health information with error handling
                        try:
                            health_score = self.system_health_monitor.get_health_score()
                            health_data['health_score'] = health_score if isinstance(health_score, (int, float)) else None
                        except Exception as e:
                            logger.warning(f"Error getting health score: {e}")
                            health_data['health_score'] = None
                        
                        try:
                            service_details = self.system_health_monitor.get_service_statuses()
                            health_data['service_details'] = service_details if isinstance(service_details, dict) else {}
                        except Exception as e:
                            logger.warning(f"Error getting service details: {e}")
                            health_data['service_details'] = {}
                        
                        try:
                            recent_alerts = self.system_health_monitor.get_recent_alerts(30)
                            health_data['recent_alerts'] = recent_alerts if isinstance(recent_alerts, list) else []
                        except Exception as e:
                            logger.warning(f"Error getting recent alerts: {e}")
                            health_data['recent_alerts'] = []
                        
                        try:
                            performance_summary = self.system_health_monitor.get_performance_summary(30)
                            health_data['performance_summary'] = self._convert_performance_temps(performance_summary) if isinstance(performance_summary, dict) else {}
                        except Exception as e:
                            logger.warning(f"Error getting performance summary: {e}")
                            health_data['performance_summary'] = {}
                        
                        health_data.update({
                            'system_info': {
                                'hostname': socket.gethostname(),
                                'python_version': sys.version.split()[0],
                                'platform': platform.platform(),
                                'uptime': basic_metrics.get('uptime_seconds', 0) if isinstance(basic_metrics, dict) else 0
                            },
                            'docker_info': self._get_docker_info(),
                            'camera_snapshot': self._get_latest_camera_snapshot()
                        })
                    except Exception as e:
                        logger.error(f"Error getting system health data: {e}")
                        health_data['system_health_error'] = str(e)
                
                return jsonify(health_data)
            except Exception as e:
                logger.error(f"Health check error: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @self.app.route('/', methods=['GET'])
        def hello_world():
            """Simple hello world endpoint"""
            return jsonify({
                'message': 'Hello World!',
                'service': 'Raspberry Pi Edge Traffic Monitoring API',
                'timestamp': datetime.now().isoformat(),
                'status': 'running'
            })

        @self.app.route('/api/weather/latest', methods=['GET'])
        def get_weather_latest():
            """Get latest weather data from Redis key 'weather:latest'"""
            try:
                if not self.redis_client:
                    return jsonify({'error': 'Redis not available', 'key': 'weather:latest'}), 503
                
                value = self.redis_client.get('weather:latest')
                if value is None:
                    return jsonify({'error': 'No latest weather data found', 'key': 'weather:latest'}), 404
                
                # Try to parse as JSON, fallback to string
                try:
                    data = json.loads(value)
                except json.JSONDecodeError:
                    data = {'value': value}
                
                return jsonify({'weather_latest': data, 'key': 'weather:latest'})
            except Exception as e:
                logger.error(f"Error reading weather:latest from Redis: {e}")
                return jsonify({'error': str(e), 'key': 'weather:latest'}), 500

        @self.app.route('/api/weather/dht22', methods=['GET'])
        def get_weather_dht22():
            """Get latest DHT22 weather data from Redis key 'weather:dht22:latest'"""
            try:
                if not self.redis_client:
                    return jsonify({'error': 'Redis not available', 'key': 'weather:dht22:latest'}), 503
                value = self.redis_client.get('weather:dht22:latest')
                if value is None:
                    return jsonify({'error': 'No latest DHT22 weather data found', 'key': 'weather:dht22:latest'}), 404
                try:
                    data = json.loads(value)
                except json.JSONDecodeError:
                    data = {'value': value}
                return jsonify({'weather_dht22': data, 'key': 'weather:dht22:latest'})
            except Exception as e:
                logger.error(f"Error reading weather:dht22:latest from Redis: {e}")
                return jsonify({'error': str(e), 'key': 'weather:dht22:latest'}), 500

        @self.app.route('/api/weather/airport', methods=['GET'])
        def get_weather_airport():
            """Get latest airport weather data from Redis key 'weather:airport:latest'"""
            try:
                if not self.redis_client:
                    return jsonify({'error': 'Redis not available', 'key': 'weather:airport:latest'}), 503
                value = self.redis_client.get('weather:airport:latest')
                if value is None:
                    return jsonify({'error': 'No latest airport weather data found', 'key': 'weather:airport:latest'}), 404
                try:
                    data = json.loads(value)
                except json.JSONDecodeError:
                    data = {'value': value}
                return jsonify({'weather_airport': data, 'key': 'weather:airport:latest'})
            except Exception as e:
                logger.error(f"Error reading weather:airport:latest from Redis: {e}")
                return jsonify({'error': str(e), 'key': 'weather:airport:latest'}), 500
        
        @self.app.route('/hello', methods=['GET'])
        def hello():
            """Alternative hello endpoint"""
            return jsonify({'message': 'Hello from Raspberry Pi Edge API!'})
        
        @self.app.route('/api/detections', methods=['GET'])
        def get_detections():
            """Get recent vehicle detections"""
            try:
                seconds = request.args.get('seconds', 10, type=int)
                detections = []
                
                if self.vehicle_detection_service:
                    try:
                        camera_detections = self.vehicle_detection_service.get_recent_detections(seconds)
                        detections.extend([
                            {
                                'id': d.detection_id,
                                'timestamp': d.timestamp,
                                'bbox': d.bbox,
                                'confidence': d.confidence,
                                'vehicle_type': d.vehicle_type,
                                'source': 'camera'
                            }
                            for d in camera_detections
                        ])
                    except AttributeError as e:
                        logger.warning(f"Detection service method missing: {e}")
                
                return jsonify({
                    'detections': detections,
                    'count': len(detections),
                    'timespan_seconds': seconds
                })
            except Exception as e:
                logger.error(f"Detections endpoint error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/speeds', methods=['GET'])
        def get_speeds():
            """Get recent speed measurements"""
            try:
                seconds = request.args.get('seconds', 60, type=int)
                speeds = []
                
                if self.speed_analysis_service:
                    try:
                        speed_detections = self.speed_analysis_service.get_recent_detections(seconds)
                        speeds.extend([
                            {
                                'id': s.detection_id,
                                'start_time': s.start_time,
                                'end_time': s.end_time,
                                'avg_speed_mps': s.avg_speed_mps,
                                'max_speed_mps': s.max_speed_mps,
                                'direction': s.direction,
                                'confidence': s.confidence
                            }
                            for s in speed_detections
                        ])
                    except AttributeError as e:
                        logger.warning(f"Speed service method missing: {e}")
                
                return jsonify({
                    'speeds': speeds,
                    'count': len(speeds),
                    'timespan_seconds': seconds
                })
            except Exception as e:
                logger.error(f"Speeds endpoint error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/tracks', methods=['GET'])
        def get_tracks():
            """Get active vehicle tracks from data fusion"""
            try:
                tracks = []
                
                if self.data_fusion_engine:
                    try:
                        active_tracks = self.data_fusion_engine.get_active_tracks()
                        tracks = [
                            {
                                'id': t.track_id,
                                'start_time': t.start_time,
                                'last_update': t.last_update,
                                'current_bbox': t.current_bbox,
                                'current_speed': t.current_speed,
                                'position_estimate': t.position_estimate,
                                'velocity_estimate': t.velocity_estimate,
                                'vehicle_type': t.vehicle_type,
                                'confidence': t.confidence
                            }
                            for t in active_tracks
                        ]
                    except AttributeError as e:
                        logger.warning(f"Data fusion service method missing: {e}")
                
                return jsonify({
                    'tracks': tracks,
                    'count': len(tracks)
                })
            except Exception as e:
                logger.error(f"Tracks endpoint error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/analytics', methods=['GET'])
        def get_analytics():
            """Get traffic analytics summary"""
            try:
                period = request.args.get('period', 'hour')  # hour, day, week
                
                analytics = {
                    'period': period,
                    'timestamp': datetime.now().isoformat(),
                    'vehicle_count': 0,
                    'avg_speed': 0.0,
                    'speed_violations': 0,
                    'detection_rate': 0.0
                }
                
                # Calculate analytics from recent data
                if self.data_fusion_engine:
                    try:
                        fusion_stats = self.data_fusion_engine.get_track_statistics()
                        if isinstance(fusion_stats, dict):
                            analytics.update(fusion_stats)
                    except AttributeError as e:
                        logger.warning(f"Data fusion statistics method missing: {e}")
                
                return jsonify(analytics)
            except Exception as e:
                logger.error(f"Analytics endpoint error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/camera/snapshot/<filename>', methods=['GET'])
        def get_camera_snapshot(filename):
            """Serve camera snapshot images"""
            try:
                # Check multiple possible locations for snapshots
                possible_paths = [
                    "/mnt/storage/periodic_snapshots",  # Primary SSD location
                    "/tmp/periodic_snapshots",          # Fallback temp location
                    "/app/periodic_snapshots",          # Docker app directory
                    os.path.join(os.getcwd(), "periodic_snapshots")  # Current working directory
                ]
                
                file_path = None
                for snapshot_path in possible_paths:
                    potential_path = os.path.join(snapshot_path, filename)
                    if os.path.exists(potential_path):
                        file_path = potential_path
                        break
                
                # Security check - only allow access to snapshot files
                if not (filename.startswith('periodic_snapshot_') or filename.startswith('traffic_')) or not filename.endswith('.jpg'):
                    return jsonify({'error': 'Invalid filename'}), 400
                
                if not file_path or not os.path.exists(file_path):
                    return jsonify({'error': 'Snapshot not found in any location'}), 404
                
                return send_file(file_path, mimetype='image/jpeg')
                
            except Exception as e:
                logger.error(f"Camera snapshot endpoint error: {e}")
                return jsonify({'error': str(e)}), 500
        
        # Weather analysis endpoints
        @self.app.route('/api/weather', methods=['GET'])
        def get_weather_data():
            """Get current weather conditions and sky analysis"""
            try:
                if not self.sky_analyzer or not self.system_status:
                    return jsonify({
                        'error': 'Weather analysis not available',
                        'weather_enabled': False
                    }), 503
                
                # Use host-capture architecture - analyze current sky from shared volume
                # This gets images captured on the host and analyzes them in the container
                max_age = request.args.get('max_age_seconds', 10.0, type=float)
                
                try:
                    sky_result = self.sky_analyzer.analyze_current_sky(max_age_seconds=max_age)
                except AttributeError as e:
                    logger.warning(f"Sky analyzer method missing: {e}")
                    sky_result = {'error': 'Sky analyzer not properly initialized'}
                
                # Check if we got a valid analysis result
                if 'error' in sky_result:
                    # Try to get basic system metrics without camera image
                    try:
                        weather_metrics = self.system_status.get_weather_metrics(camera_image=None)
                    except AttributeError as e:
                        logger.warning(f"System status method missing: {e}")
                        weather_metrics = {}
                    
                    return jsonify({
                        'weather_enabled': True,
                        'timestamp': datetime.now().isoformat(),
                        'sky_condition': sky_result,
                        'weather_metrics': weather_metrics,
                        'visibility_estimate': 'unknown',
                        'camera_available': False,
                        'image_source': 'shared_volume_failed',
                        'max_age_seconds': max_age
                    })
                
                # Get enhanced system metrics (without passing camera image since we already analyzed it)
                try:
                    weather_metrics = self.system_status.get_weather_metrics(camera_image=None)
                except AttributeError as e:
                    logger.warning(f"System status method missing: {e}")
                    weather_metrics = {}
                
                # Update weather metrics with our sky analysis
                weather_metrics['sky_condition'] = sky_result
                
                try:
                    visibility_estimate = self.sky_analyzer.get_visibility_estimate(
                        sky_result.get('condition', 'unknown'),
                        sky_result.get('confidence', 0)
                    )
                except AttributeError:
                    visibility_estimate = 'unknown'
                
                weather_metrics['visibility_estimate'] = visibility_estimate
                
                return jsonify({
                    'weather_enabled': True,
                    'timestamp': datetime.now().isoformat(),
                    'sky_condition': sky_result,
                    'weather_metrics': weather_metrics,
                    'visibility_estimate': visibility_estimate,
                    'camera_available': True,
                    'image_source': sky_result.get('image_source', 'shared_volume'),
                    'image_age_seconds': sky_result.get('image_age_seconds'),
                    'max_age_seconds': max_age
                })
                
            except Exception as e:
                logger.error(f"Weather endpoint error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/weather/history', methods=['GET'])
        def get_weather_history():
            """Get weather analysis history"""
            try:
                if not self.weather_storage:
                    return jsonify({
                        'error': 'Weather storage not available',
                        'weather_enabled': bool(self.sky_analyzer)
                    }), 503
                
                # Get query parameters
                hours = request.args.get('hours', 24, type=int)
                limit = request.args.get('limit', 100, type=int)
                
                # Validate parameters
                hours = max(1, min(hours, 168))  # 1 hour to 7 days
                limit = max(1, min(limit, 1000))  # 1 to 1000 records
                
                try:
                    history = self.weather_storage.get_weather_history(hours=hours, limit=limit)
                except AttributeError as e:
                    logger.warning(f"Weather storage method missing: {e}")
                    history = []
                
                return jsonify({
                    'weather_enabled': True,
                    'storage_available': True,
                    'history': history,
                    'query_parameters': {
                        'hours': hours,
                        'limit': limit,
                        'returned_records': len(history)
                    }
                })
                
            except Exception as e:
                logger.error(f"Weather history endpoint error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/detection-sensitivity', methods=['GET'])
        def get_detection_sensitivity():
            """Get current detection sensitivity parameters (weather-influenced)"""
            try:
                # Get weather-adjusted detection parameters from orchestrator
                # This would need to be passed down from the main orchestrator
                
                base_response = {
                    'timestamp': datetime.now().isoformat(),
                    'default_threshold': 0.5,
                    'current_threshold': 0.5,
                    'weather_influence': 'none',
                    'weather_condition': 'unknown'
                }
                
                # If we have access to weather-adjusted parameters
                # (This would need orchestrator reference to work fully)
                return jsonify(base_response)
                
            except Exception as e:
                logger.error(f"Detection sensitivity endpoint error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/weather/correlation', methods=['GET'])
        def get_weather_traffic_correlation():
            """Get weather-traffic correlation analysis"""
            try:
                if not self.weather_storage:
                    return jsonify({
                        'error': 'Weather storage not available for correlation analysis',
                        'weather_enabled': bool(self.sky_analyzer)
                    }), 503
                
                hours = request.args.get('hours', 24, type=int)
                hours = max(1, min(hours, 168))  # 1 hour to 7 days
                
                try:
                    correlation_data = self.weather_storage.get_weather_traffic_correlation(hours=hours)
                except AttributeError as e:
                    logger.warning(f"Weather storage correlation method missing: {e}")
                    correlation_data = {}
                
                return jsonify({
                    'weather_enabled': True,
                    'storage_available': True,
                    'correlation_data': correlation_data
                })
                
            except Exception as e:
                logger.error(f"Weather correlation endpoint error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/weather/stats', methods=['GET'])
        def get_weather_database_stats():
            """Get weather database statistics"""
            try:
                if not self.weather_storage:
                    return jsonify({
                        'error': 'Weather storage not available',
                        'weather_enabled': bool(self.sky_analyzer)
                    }), 503
                
                try:
                    stats = self.weather_storage.get_database_stats()
                except AttributeError as e:
                    logger.warning(f"Weather storage stats method missing: {e}")
                    stats = {}
                
                return jsonify({
                    'weather_enabled': True,
                    'storage_available': True,
                    'database_stats': stats
                })
                
            except Exception as e:
                logger.error(f"Weather stats endpoint error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/endpoints', methods=['GET'])
        def list_api_endpoints():
            """List all available API endpoints grouped by category"""
            try:
                base_url = request.url_root.rstrip('/')
                
                endpoints = {
                    "api_info": {
                        "title": "Traffic Monitoring Edge API",
                        "version": "1.0.0",
                        "description": "Real-time traffic monitoring with vehicle detection, speed analysis, and weather integration",
                        "base_url": base_url,
                        "timestamp": datetime.now().isoformat()
                    },
                    "endpoints": {
                        "system": {
                            "description": "System health and status endpoints",
                            "endpoints": [
                                {
                                    "path": "/api/health",
                                    "method": "GET",
                                    "description": "System health check with service status and metrics",
                                    "url": f"{base_url}/api/health"
                                },
                                {
                                    "path": "/hello",
                                    "method": "GET", 
                                    "description": "Simple hello endpoint for testing connectivity",
                                    "url": f"{base_url}/hello"
                                },
                                {
                                    "path": "/api/endpoints",
                                    "method": "GET",
                                    "description": "This endpoint - lists all available API endpoints",
                                    "url": f"{base_url}/api/endpoints"
                                }
                            ]
                        },
                        "vehicle_detection": {
                            "description": "Vehicle detection and tracking endpoints",
                            "endpoints": [
                                {
                                    "path": "/api/detections",
                                    "method": "GET",
                                    "description": "Get recent vehicle detections",
                                    "parameters": "?seconds=10 (optional)",
                                    "url": f"{base_url}/api/detections"
                                },
                                {
                                    "path": "/api/tracks",
                                    "method": "GET",
                                    "description": "Get active vehicle tracks from data fusion",
                                    "url": f"{base_url}/api/tracks"
                                },
                                {
                                    "path": "/api/detection-sensitivity",
                                    "method": "GET",
                                    "description": "Get current detection sensitivity parameters (weather-influenced)",
                                    "url": f"{base_url}/api/detection-sensitivity"
                                }
                            ]
                        },
                        "speed_analysis": {
                            "description": "Speed measurement and analysis endpoints", 
                            "endpoints": [
                                {
                                    "path": "/api/speeds",
                                    "method": "GET",
                                    "description": "Get recent speed measurements",
                                    "parameters": "?seconds=60 (optional)",
                                    "url": f"{base_url}/api/speeds"
                                }
                            ]
                        },
                        "analytics": {
                            "description": "Traffic analytics and insights endpoints",
                            "endpoints": [
                                {
                                    "path": "/api/analytics", 
                                    "method": "GET",
                                    "description": "Get traffic analytics and performance insights",
                                    "url": f"{base_url}/api/analytics"
                                }
                            ]
                        },
                        "weather": {
                            "description": "Weather analysis and sky condition endpoints",
                            "endpoints": [
                                {
                                    "path": "/api/weather",
                                    "method": "GET", 
                                    "description": "Get current weather conditions and sky analysis",
                                    "url": f"{base_url}/api/weather"
                                },
                                {
                                    "path": "/api/weather/latest",
                                    "method": "GET",
                                    "description": "Get latest weather data from Redis",
                                    "url": f"{base_url}/api/weather/latest"
                                },
                                {
                                    "path": "/api/weather/dht22",
                                    "method": "GET",
                                    "description": "Get latest DHT22 weather data from Redis",
                                    "url": f"{base_url}/api/weather/dht22"
                                },
                                {
                                    "path": "/api/weather/airport",
                                    "method": "GET",
                                    "description": "Get latest airport weather data from Redis",
                                    "url": f"{base_url}/api/weather/airport"
                                },
                                {
                                    "path": "/api/weather/history",
                                    "method": "GET",
                                    "description": "Get weather analysis history", 
                                    "parameters": "?hours=24&limit=100 (optional)",
                                    "url": f"{base_url}/api/weather/history"
                                },
                                {
                                    "path": "/api/weather/correlation",
                                    "method": "GET",
                                    "description": "Get weather-traffic correlation analysis",
                                    "parameters": "?hours=24 (optional)", 
                                    "url": f"{base_url}/api/weather/correlation"
                                },
                                {
                                    "path": "/api/weather/stats",
                                    "method": "GET",
                                    "description": "Get weather database statistics",
                                    "url": f"{base_url}/api/weather/stats"
                                }
                            ]
                        },
                        "camera": {
                            "description": "Camera and image endpoints",
                            "endpoints": [
                                {
                                    "path": "/api/camera/snapshot/<filename>",
                                    "method": "GET",
                                    "description": "Serve camera snapshot images",
                                    "url": f"{base_url}/api/camera/snapshot/[filename]"
                                }
                            ]
                        }
                    },
                    "websocket": {
                        "description": "Real-time WebSocket endpoints for live data streaming",
                        "url": f"{base_url}",
                        "events": [
                            "connect - Connect to WebSocket",
                            "disconnect - Disconnect from WebSocket", 
                            "subscribe_detections - Subscribe to vehicle detection updates",
                            "subscribe_speeds - Subscribe to speed analysis updates",
                            "subscribe_tracks - Subscribe to tracking updates",
                            "subscribe_weather - Subscribe to weather updates",
                            "subscribe_analytics - Subscribe to analytics updates"
                        ]
                    },
                    "usage_examples": {
                        "curl_examples": [
                            f"curl {base_url}/api/health",
                            f"curl {base_url}/api/detections?seconds=30",
                            f"curl {base_url}/api/weather",
                            f"curl {base_url}/api/weather/history?hours=6&limit=50",
                            f"curl {base_url}/api/analytics"
                        ]
                    }
                }
                
                return jsonify(endpoints)
                
            except Exception as e:
                logger.error(f"Endpoints listing error: {e}")
                return jsonify({'error': str(e)}), 500
    
    def _setup_websocket_events(self):
        """Setup WebSocket event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Client connected"""
            self.client_count += 1
            logger.info(f"Client connected. Total clients: {self.client_count}")
            emit('status', {'message': 'Connected to Edge API'})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Client disconnected"""
            self.client_count = max(0, self.client_count - 1)  # Prevent negative count
            logger.info(f"Client disconnected. Total clients: {self.client_count}")
        
        @self.socketio.on('subscribe_detections')
        def handle_subscribe_detections():
            """Subscribe to real-time detection updates"""
            emit('status', {'message': 'Subscribed to detection updates'})
            # Client will receive updates via broadcast_detection_update
        
        @self.socketio.on('subscribe_speeds')
        def handle_subscribe_speeds():
            """Subscribe to real-time speed updates"""
            emit('status', {'message': 'Subscribed to speed updates'})
            # Client will receive updates via broadcast_speed_update
        
        @self.socketio.on('subscribe_weather')
        def handle_subscribe_weather():
            """Subscribe to real-time weather updates"""
            emit('status', {'message': 'Subscribed to weather updates'})
            # Client will receive updates via broadcast_weather_update
        
        @self.socketio.on('subscribe_tracks')
        def handle_subscribe_tracks():
            """Subscribe to real-time track updates"""
            emit('status', {'message': 'Subscribed to track updates'})
            # Client will receive updates via broadcast_track_update
        
        @self.socketio.on('subscribe_analytics')
        def handle_subscribe_analytics():
            """Subscribe to real-time analytics updates"""
            emit('status', {'message': 'Subscribed to analytics updates'})
            # Client will receive updates via broadcast methods
    
    def broadcast_detection_update(self, detection_data):
        """Broadcast detection update to all connected clients"""
        try:
            if self.client_count > 0:
                self.socketio.emit('detection_update', detection_data)
        except Exception as e:
            logger.error(f"Error broadcasting detection update: {e}")
    
    def broadcast_speed_update(self, speed_data):
        """Broadcast speed update to all connected clients"""
        try:
            if self.client_count > 0:
                self.socketio.emit('speed_update', speed_data)
        except Exception as e:
            logger.error(f"Error broadcasting speed update: {e}")
    
    def broadcast_weather_update(self, weather_data):
        """Broadcast weather update to all connected clients"""
        try:
            if self.client_count > 0:
                self.socketio.emit('weather_update', weather_data)
        except Exception as e:
            logger.error(f"Error broadcasting weather update: {e}")
    
    def broadcast_track_update(self, track_data):
        """Broadcast track update to all connected clients"""
        try:
            if self.client_count > 0:
                self.socketio.emit('track_update', track_data)
        except Exception as e:
            logger.error(f"Error broadcasting track update: {e}")
    
    def broadcast_analytics_update(self, analytics_data):
        """Broadcast analytics update to all connected clients"""
        try:
            if self.client_count > 0:
                self.socketio.emit('analytics_update', analytics_data)
        except Exception as e:
            logger.error(f"Error broadcasting analytics update: {e}")
    
    def start_server(self):
        """Start the API server"""
        try:
            self.is_running = True
            logger.info(f"Starting Edge API Gateway on {self.host}:{self.port}")
            
            # Start background update broadcaster
            update_thread = threading.Thread(target=self._update_broadcaster, daemon=True)
            update_thread.start()
            
            # Start the server
            self.socketio.run(
                self.app,
                host=self.host,
                port=self.port,
                debug=False,
                allow_unsafe_werkzeug=True
            )
        except Exception as e:
            logger.error(f"Failed to start API server: {e}")
            self.is_running = False
            raise
    
    def _update_broadcaster(self):
        """Background thread to broadcast periodic updates"""
        last_detection_count = 0
        last_speed_count = 0
        last_track_count = 0
        
        while self.is_running:
            try:
                if self.client_count > 0:
                    # Broadcast recent detections (only new ones)
                    if self.vehicle_detection_service:
                        try:
                            recent_detections = self.vehicle_detection_service.get_recent_detections(2)
                            if len(recent_detections) > last_detection_count:
                                for detection in recent_detections[last_detection_count:]:
                                    self.broadcast_detection_update({
                                        'id': detection.detection_id,
                                        'timestamp': detection.timestamp,
                                        'bbox': detection.bbox,
                                        'confidence': detection.confidence,
                                        'vehicle_type': detection.vehicle_type
                                    })
                                last_detection_count = len(recent_detections)
                        except AttributeError:
                            pass  # Service method not available
                    
                    # Broadcast recent speeds (only new ones)
                    if self.speed_analysis_service:
                        try:
                            recent_speeds = self.speed_analysis_service.get_recent_detections(2)
                            if len(recent_speeds) > last_speed_count:
                                for speed in recent_speeds[last_speed_count:]:
                                    self.broadcast_speed_update({
                                        'id': speed.detection_id,
                                        'avg_speed_mps': speed.avg_speed_mps,
                                        'direction': speed.direction,
                                        'confidence': speed.confidence
                                    })
                                last_speed_count = len(recent_speeds)
                        except AttributeError:
                            pass  # Service method not available
                    
                    # Broadcast track updates (only when count changes)
                    if self.data_fusion_engine:
                        try:
                            active_tracks = self.data_fusion_engine.get_active_tracks()
                            if len(active_tracks) != last_track_count:
                                self.broadcast_track_update({
                                    'active_track_count': len(active_tracks),
                                    'timestamp': datetime.now().isoformat()
                                })
                                last_track_count = len(active_tracks)
                        except AttributeError:
                            pass  # Service method not available
                
                time.sleep(2)  # Broadcast every 2 seconds to reduce load
                
            except Exception as e:
                logger.error(f"Update broadcaster error: {e}")
                time.sleep(5)  # Wait longer on error
    
    def stop_server(self):
        """Stop the API server"""
        self.is_running = False
        logger.info("Edge API Gateway stopped")
    
    def _get_docker_info(self):
        """Get Docker container information if running in a container"""
        docker_info = {
            'running_in_container': False,
            'container_id': None,
            'image_name': None,
            'container_name': None,
            'created_at': None,
            'uptime': None
        }
        
        try:
            # Check if running in a Docker container
            if os.path.exists('/.dockerenv') or os.path.exists('/proc/1/cgroup'):
                docker_info['running_in_container'] = True
                
                # Try to get container ID from hostname (often used in Docker)
                try:
                    hostname = socket.gethostname()
                    # In Docker, hostname is often the container ID (first 12 chars)
                    if len(hostname) == 12 and all(c in '0123456789abcdef' for c in hostname):
                        docker_info['container_id'] = hostname
                except Exception:
                    pass
                
                # Try multiple methods to get Docker container information
                
                # Method 1: Check /proc/self/cgroup for container ID
                try:
                    with open('/proc/self/cgroup', 'r') as f:
                        for line in f:
                            if 'docker' in line:
                                # Extract container ID from cgroup path
                                parts = line.strip().split('/')
                                for part in parts:
                                    if len(part) == 64 and all(c in '0123456789abcdef' for c in part):
                                        docker_info['container_id'] = part[:12]  # Short form
                                        break
                except (FileNotFoundError, PermissionError):
                    pass
                
                # Method 2: Try to get image name from environment variables or common locations
                image_sources = [
                    os.environ.get('DOCKER_IMAGE'),
                    os.environ.get('IMAGE_NAME'),
                    os.environ.get('CONTAINER_IMAGE'),
                    'gcumerk/cst590-capstone-public:latest'  # Known default for this project
                ]
                
                for source in image_sources:
                    if source and source != 'unknown':
                        docker_info['image_name'] = source
                        break
                
                # Method 3: Try to get uptime from /proc/1/stat (PID 1 in container)
                try:
                    with open('/proc/1/stat', 'r') as f:
                        stat_data = f.read().split()
                        # Field 22 is starttime in ticks since boot
                        starttime_ticks = int(stat_data[21])
                        
                        # Get system boot time
                        with open('/proc/stat', 'r') as stat_f:
                            for line in stat_f:
                                if line.startswith('btime'):
                                    boot_time = int(line.split()[1])
                                    break
                        
                        # Get ticks per second
                        try:
                            ticks_per_sec = os.sysconf(os.sysconf_names['SC_CLK_TCK'])
                        except (KeyError, AttributeError):
                            ticks_per_sec = 100  # Default fallback
                        
                        # Calculate start time
                        start_seconds = boot_time + (starttime_ticks / ticks_per_sec)
                        current_time = time.time()
                        docker_info['uptime'] = current_time - start_seconds
                        
                        # Format created_at timestamp
                        docker_info['created_at'] = datetime.fromtimestamp(start_seconds).isoformat()
                        
                except (FileNotFoundError, PermissionError, ValueError, IndexError) as e:
                    logger.debug(f"Error calculating container uptime: {e}")
                
                # Method 4: Try docker command if available (less likely to work inside container)
                try:
                    result = subprocess.run(
                        ['docker', 'inspect', '--format', 
                         '{{.Config.Image}}|{{.Name}}|{{.Created}}|{{.State.StartedAt}}',
                         socket.gethostname()], 
                        capture_output=True, text=True, timeout=3
                    )
                    
                    if result.returncode == 0:
                        parts = result.stdout.strip().split('|')
                        if len(parts) >= 4:
                            docker_info['image_name'] = parts[0]
                            docker_info['container_name'] = parts[1].lstrip('/')
                            docker_info['created_at'] = parts[2]
                            
                except subprocess.TimeoutExpired:
                    logger.debug("Docker command timed out")
                except FileNotFoundError:
                    logger.debug("Docker command not found in container")
                except Exception as e:
                    logger.debug(f"Docker command failed: {e}")
                
                # Set container name from hostname if not found
                if not docker_info['container_name']:
                    docker_info['container_name'] = socket.gethostname()
                
                # Try to get container stats
                try:
                    result = subprocess.run(
                        ['docker', 'stats', '--no-stream', '--format', 
                         'table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}'],
                        capture_output=True, text=True, timeout=5
                    )
                    if result.returncode == 0:
                        lines = result.stdout.strip().split('\n')
                        if len(lines) > 1:  # Skip header
                            stats_line = lines[1]
                            docker_info['container_stats'] = stats_line
                except Exception:
                    pass
                    
        except Exception as e:
            logger.debug(f"Error checking Docker environment: {e}")
        
        return docker_info
    
    def _get_latest_camera_snapshot(self):
        """Get information about the latest periodic camera snapshot"""
        try:
            # Check multiple possible locations for snapshots
            possible_paths = [
                "/mnt/storage/periodic_snapshots",  # Primary SSD location
                "/tmp/periodic_snapshots",          # Fallback temp location
                "/app/periodic_snapshots",          # Docker app directory
                os.path.join(os.getcwd(), "periodic_snapshots")  # Current working directory
            ]
            
            snapshot_path = None
            for path in possible_paths:
                if os.path.exists(path) and os.path.isdir(path):
                    snapshot_path = path
                    break
            
            if not snapshot_path:
                return {
                    'available': False,
                    'message': 'No snapshots directory found in any location'
                }
            
            # Find the latest snapshot
            try:
                snapshot_files = [f for f in os.listdir(snapshot_path) 
                                if (f.startswith('periodic_snapshot_') or f.startswith('traffic_')) and f.endswith('.jpg')]
            except OSError as e:
                return {
                    'available': False,
                    'message': f'Error accessing snapshot directory: {str(e)}'
                }
            
            if not snapshot_files:
                return {
                    'available': False,
                    'message': f'No snapshots found in {snapshot_path}'
                }
            
            # Get the most recent snapshot
            try:
                latest_snapshot = max(snapshot_files, 
                                    key=lambda x: os.path.getmtime(os.path.join(snapshot_path, x)))
                
                snapshot_full_path = os.path.join(snapshot_path, latest_snapshot)
                mod_time = os.path.getmtime(snapshot_full_path)
                file_size = os.path.getsize(snapshot_full_path)
                
                # Create URL based on the actual path
                url_path = f'/api/camera/snapshot/{latest_snapshot}'
                
                return {
                    'available': True,
                    'filename': latest_snapshot,
                    'timestamp': datetime.fromtimestamp(mod_time).isoformat(),
                    'file_size_bytes': file_size,
                    'path': snapshot_path,
                    'url': url_path
                }
            except (OSError, ValueError) as e:
                return {
                    'available': False,
                    'message': f'Error accessing snapshot file: {str(e)}'
                }
            
        except Exception as e:
            logger.error(f"Error getting latest camera snapshot: {e}")
            return {
                'available': False,
                'message': f'Error: {str(e)}'
            }


if __name__ == "__main__":
    # Test the API gateway
    api_gateway = EdgeAPIGateway()
    
    try:
        api_gateway.start_server()
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
        api_gateway.stop_server()
    except Exception as e:
        logger.error(f"Server startup failed: {e}")
        api_gateway.stop_server()